from typing import Callable

import sqlalchemy.engine.row
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import time
from datetime import datetime
from VK_funcs import make_searching_portrait, my_token, flat_nested, key
import json
from random import shuffle
# from vk_api.longpoll import VkLongPoll, VkEventType
from DB import DataBase

bot_token = '3ed6d7a1af9a6f6789559a925b14b30963b1514d943c41926cb88b28ea1091dd321d9ddc494cfa694ba54'
group_id = 209978754


def usual_msg_prms(user_id):
    params = {'user_id': user_id,
              'random_id': int(time.time() * 1000),
              'peer_id': group_id * -1}
    return params


def sender(api, user_id, text=None, attachments=None, keyboard=None):
    params = {'user_id': user_id,
              'random_id': int(time.time() * 1000),
              'peer_id': group_id * -1}

    api.messages.send(**params, message=text, attachments=attachments, keyboard=keyboard)


def say_welcome():
    hello = """ Добро пожаловать в бота VKindere!\n
Я могу найти вам пару:
выберу 4-х человек, основываясь на ваших данных, 
и пришлю фото каждого кандидата, с ссылкой на профиль\n
Чтобы начать поиск, напишите: 
поиск
"""
    return hello


def main_keyboard():

    keyboard = """
                 {"one_time": false, "buttons":
                 [[{"action": {"type": "text", "label": "Поиск"}, "color": "positive"}]]}
               """
    return keyboard


def empty_keyboard():
    keyboard = """
                     {"one_time": true, "buttons": []}
                   """
    return keyboard


def cancel_keyboard():
    cancel_but = """
                   {"one_time": false, "buttons":
                   [[{"action": {"type": "text", "label": "Отмена"}, "color": "negative"}]]}
                 """
    return cancel_but


def show_help():
    with open('help.txt') as f:
        text = f.read()
    return text


def filter_closed(response_obj):
    """response_obj - успешный ответ users.search метода"""
    filtered_users = []
    for user in response_obj['items']:
        if user['can_access_closed']:
            filtered_users.append(user)
    return filtered_users


def get_ids(pairs_list: list):
    """@users_list (закрытые аккаунты отфильтрованы) - список словарей, где каждый - данные о найденном пользователе.
    Возвращает список id-страниц, которых нет в базе """

    records = DataBase.connection.execute(f"""SELECT candidate_id 
                                FROM people p
                                JOIN users u
                                ON p.user_id = u.id
                                """).fetchall()
    found_ids = [u['id'] for u in pairs_list]
    if len(records) > 0:
        seen_ids = [i for i in flat_nested(records)]
        new_ids = list(set(found_ids).difference(seen_ids))
        return new_ids
    return found_ids


def choose_photos(query_maker: vk_api.VkApi.method, ids):
    """
    query_maker - bound method VkApi.method, должен иметь ключ пользователя
    ids - список ID страниц, у которых нужно запросить фото через photos.get
    """
    resp_obj_store = []  # Список для объектов успешного ответа photos.get, все фото 1 пользователя и метаданные к ним
    sorted_photos = []
    owner_and_photos = []
    shuffle(ids)
    for user_id in ids:
        resp_obj_store.append(query_maker('photos.get', values={'owner_id': user_id, 'album_id': 'profile',
                                                        'extended': 1, 'photo_sizes': 0}))
    for user in resp_obj_store:
        user_photo_list = user['items']
        user_photo_list: list
        user_photo_list.sort(key=lambda d: d['likes']['count'] + d['comments']['count'], reverse=True)
        sorted_photos.append(user_photo_list)

        with open('all_photos_sorted.json', mode='w') as f:
            json.dump(sorted_photos, f, indent=2)
    photo = {}
    user_count = 0
    for user in sorted_photos:
        users_photos = []
        foto_count = 0
        if user_count > 2:
            break
        for photo in user:
            if foto_count > 2:
                break
            users_photos.append(f"photo{photo['owner_id']}_{photo['id']}")
            foto_count += 1
            if len(users_photos) >= 3:
                owner_and_photos.append((photo['owner_id'], users_photos))
                user_count += 1
                with open('ids array.json', mode='w') as f:
                    json.dump(owner_and_photos, f, indent=2)
    return owner_and_photos


def send_photos(api, array, user_id, keyboard: Callable = None):
    """query_maker: объект класса VkApiMethod,  для обращения к API методам, как к обычным,
    event: событие VkBotLongPoll.listen(),
    array: список формата [[owner_id, [photo_id1, photo_id2..], ...]] """
    for user_collage in array:
        api.messages.send(**usual_msg_prms(user_id),
                          attachment=[i for i in user_collage[1]],
                          message=f"https://vk.com/id{user_collage[0]}",
                          keyboard=keyboard())
        DataBase.ins_into_people(user_id=user_id, candidate_id=user_collage[0])


def main():
    DataBase.clear_tables()
    main_user = vk_api.VkApi(token=my_token)
    main_bot = vk_api.VkApi(token=bot_token)
    bot_long_pool = VkBotLongPoll(main_bot, group_id=group_id)
    group_api = main_bot.get_api()
    user_api = main_user.get_api()
    # DataBase.create_tables()

    for event in bot_long_pool.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            request = event.message.get('text').casefold().strip()
            user_id = event.message.get('from_id')
            print(f"user {user_id} taken")
            DataBase.ins_into_users(id=user_id, name='')
            if request != 'поиск':
                sender(group_api, user_id, text=say_welcome(),
                       keyboard=main_keyboard())
            elif request == "поиск":
                count = 70
                users_get = group_api.users.get(user_ids=user_id, fields=['bdate', 'sex', 'relation', 'city'])
                with open('vk_self_info.json', 'a') as f:
                    json.dump(users_get, f, indent=2, ensure_ascii=False)
                features = make_searching_portrait(users_get[0])
                if features is None:
                    wrong_input = 0
                    while features is None:
                        if wrong_input == 0:
                            sender(group_api, user_id, 'Уточните ваш возраст', keyboard=cancel_keyboard())
                        elif wrong_input == 1:
                            sender(group_api, user_id, 'Кажется, возраст введен неверное, используйте только цифры'
                                                       ' в диапазоне от 14 до 115')
                        elif wrong_input == 2:
                            sender(group_api, user_id, 'Не могу выполнить поиск, попробуйте начать новый',
                                   keyboard=main_keyboard())
                            break
                        for thing in bot_long_pool.listen():
                            if thing.type == VkBotEventType.MESSAGE_NEW:
                                answer = thing.message.get('text').casefold().strip()
                                if answer != 'отмена':
                                    if answer.isdigit() and int(answer) in range(14, 116):
                                        # if int(answer) in range(14, 116):
                                        answer = int(answer)
                                        features = make_searching_portrait(users_get[0], age=answer)
                                    wrong_input += 1
                                    break
                                else:
                                    sender(group_api, user_id, 'Поиск отменен', keyboard=main_keyboard())
                                    features = 'break while loop'
                                    break
                if isinstance(features, dict) and len(features) == 5:
                    sender(group_api, user_id, 'Идет поиск...', keyboard=empty_keyboard())
                    beginning = datetime.now()
                    found_users = user_api.users.search(sort=0, count=count, **features,
                                                        fields='photo_id')
                    filtered_users = filter_closed(found_users)
                    ids = get_ids(filtered_users)
                    photo_array = choose_photos(main_user.method, ids)
                    send_photos(group_api, photo_array, user_id, main_keyboard)
                    finish = datetime.now()
                    with open('search_time.txt', 'a') as f:
                        exec_time = finish - beginning
                        f.write(f"Execution time: {exec_time}, people: {count}\n")


            # else:
            #     sender(group_api, user_id, 'Увы, пока что  я в этом не разбираюсь')
            #     time.sleep(0.9)
            #     sender(group_api, user_id, 'Для справки отправьте "h"')


if __name__ == '__main__':
    main()


