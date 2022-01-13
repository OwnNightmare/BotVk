from typing import Callable
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import time
import datetime
import sqlalchemy.engine.row
from datetime import datetime
import json
from random import shuffle
from DB import DataBase

my_token = 'c3a240cff79d2ddac8a4e884df9b599090c3d54f166d62f5c2c3768d86a215fe590b7d62bc8a26a13ec15'  # offline level
bot_token = '3ed6d7a1af9a6f6789559a925b14b30963b1514d943c41926cb88b28ea1091dd321d9ddc494cfa694ba54'  # ключ доступа бота
group_id = 209978754  # ID вашего сообщества


def usual_msg_prms(user_id):
    """Возвращает обязательные параметры для сообщения в виде словаря:\n
       @user_id - id текущего пользователя ВК.
        """

    params = {'user_id': user_id,
              'random_id': int(time.time() * 1000),
              'peer_id': group_id * -1}
    return params


def sender(api, user_id, text=None, attachments=None, keyboard=None):
    """ Отправляет сообщение пользователю в группу, ничего не возвращает\n
    @api - объект класса  VkApiMethod, обязательный параметр\n
    @user_id -  ВК ID  текущего пользователя, обязательный параметр\n
    @text - текст сообщения, обязательный если attachments=None\n
    @attachments - вложения, обязательный если text=None\n
    @keyboard - отправляемая клавиатура, необязательный"""

    params = {'user_id': user_id,
              'random_id': int(time.time() * 1000),
              'peer_id': group_id * -1}

    api.messages.send(**params, message=text, attachments=attachments, keyboard=keyboard)


def say_welcome():
    """Возвращает текст приветственного сообщения"""

    hello = """ Добро пожаловать в бота VKindere!\n
Я могу найти вам пару:
выберу 3-х человек, основываясь на ваших данных, 
и пришлю фото каждого кандидата, с ссылкой на профиль\n
Чтобы начать поиск, напишите: 
поиск
"""
    return hello


def bot_buttons():
    """ Обязательно указывать ключ словаря!
    Возвращает словарь со значениями в виде строкового json объекта"""

    my_keyboard = {'search':
                   """ {"one_time": false, "buttons":
                    [[{"action": {"type": "text", "label": "Поиск"}, "color": "positive"}]]} """,
                   'cancel':
                       """ {"one_time": false, "buttons":
                           [[{"action": {"type": "text", "label": "Отмена"}, "color": "negative"}]]} """,
                   'empty': """ {"one_time": true, "buttons": []} """
                   }
    return my_keyboard


def show_help():
    with open('help.txt') as f:
        text = f.read()
    return text


def calc_age(acc_info: dict):
    """acc_info - значение ключа 'response' json ответа Vk API метода account.getProfileInfo"""
    birth_info = acc_info.get('bdate')
    if not birth_info:
        return
    birth_info = birth_info.split('.')
    birth_info = [int(i) for i in birth_info[::-1] if i.isdigit()]
    if len(birth_info) == 3:
        birthday = datetime.date(birth_info[0], birth_info[1], birth_info[2])
        curr_date = datetime.date.today()
        age = curr_date - birthday
        age = age.days // 364
        return age
    return


def make_searching_portrait(acc_info: dict, age=None):
    """ Возвращает "портрет" искомого человека, составленный на основании acc_info.
    acc_info - значение ключа 'response'  успешного json ответа Vk API метода account.getProfileInfo"""
    _portrait = {'city': acc_info.get('city').get('id'), 'status': acc_info.get('relation')}
    if not age:
        age = calc_age(acc_info)
    if isinstance(age, int) and age in range(12, 120):
        sex = acc_info.get('sex')
        if int(sex) == 2:
            _portrait['sex'] = 1
            _portrait['age_from'] = age - 2
            _portrait['age_to'] = age
        elif sex == 1:
            _portrait['sex'] = 2
            _portrait['age_from'] = age - 1
            _portrait['age_to'] = age + 2
        else:
            _portrait['sex'] = 0
            _portrait['age_from'] = age - 1
            _portrait['age_to'] = age + 1
        with open('portrait.json', 'a') as f:
            json.dump(_portrait, f, indent=2, ensure_ascii=False)
        return _portrait


def filter_closed(response_obj):
    """ Возвращает список данных об аккаунтах, к которым есть доступ
    @response_obj - успешный ответ users.search метода"""

    filtered_users = []
    for user in response_obj['items']:
        if user['can_access_closed']:
            filtered_users.append(user)
    return filtered_users


def flat_nested(array):
    """ Выпрямляет переданный аргумент, в том числе массив данных из БД,
    полученный через sqlalchemy\n
     Возвращает объект итератора"""
    for item in array:
        if isinstance(item, (sqlalchemy.engine.row.LegacyRow, list, tuple)):
            for sub_item in flat_nested(item):
                yield sub_item
        else:
            yield item


def get_ids(pairs_list: list):
    """
    Делает запрос в БД, получая id "кандидатов" для пользователя\n
    исключает их из принятых в аргументе данных\n
    Возвращает список id, которых еще не видел пользователь\n
    @pairs_list (закрытые аккаунты отфильтрованы) - список словарей, где каждый - данные о найденном пользователе.
     """

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
    """ Выполняет запрос photos.get, для каждого пользователя сортирует фото по популярности,\n
    формирует tuple('id владельца', [photo<id_владельца>_<id_фото>, ...]),\n
    где список фото - строки в нужном для параметра attachments метода messages.send формате,\n
    возвращает список tuple-ов\n
    @query_maker - bound method VkApi.method, должен иметь ключ пользователя
    @ids - список ID страниц, у которых нужно получить фото
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
    """ Отправляет фото, заносит отправленные id в БД\n
    @query_maker: объект класса VkApiMethod,  для обращения к API методам, как к обычным\n
    @event: событие VkBotLongPoll.listen(),\n
    @array: список формата [[owner_id, [photo_id1, photo_id2..], ...]] """

    for user_collage in array:
        api.messages.send(**usual_msg_prms(user_id),
                          attachment=[i for i in user_collage[1]],
                          message=f"https://vk.com/id{user_collage[0]}",
                          keyboard=keyboard()['search'])
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
        try:
            if event.type == VkBotEventType.MESSAGE_NEW:
                request = event.message.get('text').casefold().strip()
                user_id = event.message.get('from_id')
                print(f"user {user_id} taken")
                DataBase.ins_into_users(id=user_id, name='')
                if request != 'поиск':
                    sender(group_api, user_id, text=say_welcome(),
                           keyboard=bot_buttons()['search'])
                elif request == "поиск":
                    count = 70
                    users_get = group_api.users.get(user_ids=user_id, fields=['bdate', 'sex', 'relation', 'city'])
                    with open('vk_self_info.json', 'a') as f:
                        json.dump(users_get, f, indent=2, ensure_ascii=False)
                    features = make_searching_portrait(users_get[0])
                    if features is None:
                        wrong_input = 0
                        while not features:
                            if wrong_input == 0:
                                sender(group_api, user_id, 'Уточните ваш возраст', keyboard=bot_buttons()['cancel'])
                            elif wrong_input == 1:
                                sender(group_api, user_id, 'Кажется, возраст введен неверное, используйте только цифры'
                                                           ' в диапазоне от 14 до 115')
                            elif wrong_input == 2:
                                sender(group_api, user_id, 'Не могу выполнить поиск, попробуйте начать новый',
                                       keyboard=bot_buttons()['search'])
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
                                        sender(group_api, user_id, 'Поиск отменен', keyboard=bot_buttons()['search'])
                                        features = 'break while loop'
                                        break
                    if isinstance(features, dict) and len(features) == 5:
                        sender(group_api, user_id, 'Идет поиск...', keyboard=bot_buttons()['empty'])
                        beginning = datetime.now()
                        found_users = user_api.users.search(sort=0, count=count, **features,
                                                            fields='photo_id')
                        filtered_users = filter_closed(found_users)
                        ids = get_ids(filtered_users)
                        photo_array = choose_photos(main_user.method, ids)
                        send_photos(group_api, photo_array, user_id, bot_buttons)
                        finish = datetime.now()
                        with open('search_time.txt', 'a') as f:
                            exec_time = finish - beginning
                            f.write(f"Execution time: {exec_time}, people: {count}\n")
        except:
            pass
        finally:
            sender(group_api, user_id, 'Извините, что-то пошло не так')


            # else:
            #     sender(group_api, user_id, 'Увы, пока что  я в этом не разбираюсь')
            #     time.sleep(0.9)
            #     sender(group_api, user_id, 'Для справки отправьте "h"')


if __name__ == '__main__':
    main()


