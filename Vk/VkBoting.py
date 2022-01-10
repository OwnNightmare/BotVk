import sqlalchemy.engine.row
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import time
from datetime import datetime
from VK_funcs import make_searching_portrait, my_token, flat_sql_row
import json
from random import shuffle
# from vk_api.longpoll import VkLongPoll, VkEventType
from DB import DataBase
bot_token = '3ed6d7a1af9a6f6789559a925b14b30963b1514d943c41926cb88b28ea1091dd321d9ddc494cfa694ba54'
group_id = 209978754


def get_message_id():
    microseconds = int(time.time() * 1000)
    return microseconds


def show_help():
    with open('help.txt') as f:
        text = f.read()
    return text


def typical_message_params(event):
    params = {'user_id': event.message['from_id'],
              'random_id': get_message_id(),
              'peer_id': group_id * -1}
    return params


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
                                FROM people
                                """).fetchall()
    found_ids = [u['id'] for u in pairs_list]
    if len(records) > 0:
        seen_ids = [i for i in flat_sql_row(records)]
        new_ids = list(set(found_ids).difference(seen_ids))
        return new_ids
    else:
        return found_ids


def choose_photos(query_maker: vk_api.VkApi.method, ids):
    """
    query_maker - bound method VkApi.method, должен иметь ключ пользователя
    ids - список ID страниц, у которых нужно запросить фото через photos.get"""
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
        if user_count > 3:
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


def send_and_insert_db(query_maker, event, array, user_id):
    """query_maker: объект класса VkApiMethod,  для обращения к API методам, как к обычным,
    event: событие VkBotLongPoll.listen(),
    array: список формата [[owner_id, [photo_id1, photo_id2..], ...]] """
    for user_collage in array:
        query_maker.messages.send(**typical_message_params(event),
                                  attachment=[i for i in user_collage[1]],
                                  message=f"https://vk.com/id{user_collage[0]}")
        DataBase.ins_into_people(user_id=user_id, candidate_id=user_collage[0])


def main():
    DataBase.clear_db()
    main_user = vk_api.VkApi(token=my_token)
    main_bot = vk_api.VkApi(token=bot_token)
    bot_long_pool = VkBotLongPoll(main_bot, group_id=group_id)
    group_api = main_bot.get_api()
    user_api = main_user.get_api()
    DataBase.create_tables()

    for event in bot_long_pool.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            text = event.message.get('text').lower()
            user_id = event.message.get('from_id')
            print(f"user {user_id} taken")
            DataBase.ins_into_users(id=user_id, name='Юрий Борисов')
            if text == 'id':
                group_api.messages.send(**typical_message_params(event),
                                        message=f"ID страницы: {user_id}")
            elif text == 'f':
                count = 72
                group_api.messages.send(**typical_message_params(event),
                    message=f'Идет поиск...\nСреднее время поиска {int(count * 0.5)} секунд\n'
                            f'Пожалуйста, подождите =)')
                users_get = group_api.users.get(user_ids=user_id, fields=['bdate', 'sex', 'relation', 'city'])
                with open('vk_self_info.json', 'w') as f:
                    json.dump(users_get, f, indent=2, ensure_ascii=False)
                features = make_searching_portrait(users_get[0])
                if features:
                    beginning = datetime.now()
                    found_users = user_api.users.search(sort=0, count=count, **features,
                                                        fields='photo_id')
                    filtered_users = filter_closed(found_users)
                    ids = get_ids(filtered_users)
                    photo_array = choose_photos(main_user.method, ids)
                    group_api.messages.send(**typical_message_params(event), message='Поиск окончен, высылаем фото')
                    time.sleep(0.7)
                    send_and_insert_db(group_api, event, photo_array, user_id)
                    finish = datetime.now()
                    with open('search_time.txt', 'a') as f:
                        exec_time = finish - beginning
                        f.write(f"Execution time: {exec_time}, people: {count}\n")
            elif text == 'пока':
                group_api.messages.send(**typical_message_params(event), message='Пока =)')
            elif text == 'h':
                group_api.messages.send(**typical_message_params(event), message=show_help())
            else:
                group_api.messages.send(**typical_message_params(event), message=f"Команда неизвестна")
                time.sleep(0.5)
                group_api.messages.send(**typical_message_params(event), message=show_help())


if __name__ == '__main__':
    main()
    DataBase.clear_db()


