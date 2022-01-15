import vk_api
import time
import datetime
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from random import shuffle
from typing import Callable, Iterable
from datetime import datetime as dt
import sqlalchemy.engine.row
import json
from typing import Any
from DB.Create_DB import check_country, check_city, \
    create_tables, clear_users_db, ins_into_people, ins_into_users, connection


status = """
1 — не женат (не замужем),
2 — встречается,
3 — помолвлен(-а),
4 — женат (замужем),
5 — всё сложно,
6 — в активном поиске,
7 — влюблен(-а),
8 — в гражданском браке."""




my_token = 'c3a240cff79d2ddac8a4e884df9b599090c3d54f166d62f5c2c3768d86a215fe590b7d62bc8a26a13ec15'  # offline level
bot_token = '3ed6d7a1af9a6f6789559a925b14b30963b1514d943c41926cb88b28ea1091dd321d9ddc494cfa694ba54'  # ключ доступа бота
group_id = 209978754  # ID вашего сообщества
main_user = vk_api.VkApi(token=my_token)
main_bot = vk_api.VkApi(token=bot_token)


def usual_msg_prms(user_id: int) -> dict:
    """Возвращает обязательные параметры для сообщения в виде словаря:\n
       @user_id - id текущего пользователя ВК.
        """

    params = {'user_id': user_id,
              'random_id': int(time.time() * 1000),
              'peer_id': group_id * -1}
    return params


def sender(api, user_id: int, text: str = None, attachments: Any = None, keyboard=None) -> None:
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


def welcome() -> str:
    """Возвращает текст приветственного сообщения"""

    hello = """ Добро пожаловать в бота VKindere!\n
Я могу найти вам пару:
выберу 3-х человек, основываясь на ваших данных, 
и пришлю фото каждого кандидата, с ссылкой на профиль\n
Чтобы начать поиск, напишите: 
поиск
"""
    return hello


def keyboarding() -> dict:
    """ Возвращает словарь со значениями в виде строкового json объекта\n
    Обязательно указывать ключ словаря"""

    my_keyboard = {'search':
                   """ {"one_time": false, "buttons":
                    [[{"action": {"type": "text", "label": "Поиск"}, "color": "positive"}]]} """,
                   'cancel':
                       """ {"one_time": false, "buttons":
                           [[{"action": {"type": "text", "label": "Отмена"}, "color": "negative"}]]} """,
                   'empty': """ {"one_time": true, "buttons": []} """
                   }
    return my_keyboard


def calc_age(b_date: str) -> int or None:
    """Если день рождения указан полностью:возвращает возраст пользователя\n
    Если нет: возвращает None\n
    @b_date - день рождения пользователя в формате str(ДД.ММ.ГГГГ)"""

    b_date = b_date.split('.')
    b_date = [int(i) for i in b_date[::-1] if i.isdigit()]
    if len(b_date) == 3:
        birthday = datetime.date(b_date[0], b_date[1], b_date[2])
        curr_date = datetime.date.today()
        age = curr_date - birthday
        age = int(age.days // 364)
        return age
    return


def get_name(user_get_response: list) -> str:
    """Возвращает Имя и Фамилию пользователя\n
    @user_get_response - объект успешного ответа от метода users.get"""

    user = user_get_response[0]
    name = f"{user.get('first_name')} {user.get('last_name')}"
    return name


def check(user_get: list) -> str:
    for user in user_get:
        if not user.get('country'):
            return 'country!'
        if not user.get('city'):
            return 'city!'
        if not user.get('relation') or len(str(user.get('relation'))) == 0:
            return 'relation!'
    return 'ok!'


def make_searching_portrait(user_get_response: list, age: int = None, city_id: int = None, relation:int = None) -> dict or None:
    """ Возвращает критерии поиска людей для текущего польз-ля\n
    Если возраст None - вычисляет его из полученных данных\n
    @acc_info - словарь с данными о текущем пользователе
    @age - возраст пользователя"""

    acc_info = user_get_response[0]
    portrait = {}
    if not city_id:
        portrait['city_id'] = acc_info.get('city').get('id')
    else:
        portrait['city_id'] = city_id
    if not relation:
        portrait['relation'] = acc_info.get('relation')
    else:
        portrait['relation'] = relation
    if not age:
        if acc_info.get('bdate'):
            age = calc_age(acc_info.get('bdate'))
    if isinstance(age, int) and age in range(12, 120):
        sex = acc_info.get('sex')
        if int(sex) == 2:
            portrait['sex'] = 1
            portrait['age_from'] = age - 2
            portrait['age_to'] = age
        elif sex == 1:
            portrait['sex'] = 2
            portrait['age_from'] = age - 1
            portrait['age_to'] = age + 2
        else:
            portrait['sex'] = 0
            portrait['age_from'] = age - 1
            portrait['age_to'] = age + 1
        return portrait


def filter_people(response_obj: dict, user_id: int) -> dict or None:
    """Возвращает список id страниц, которых еще не видел пользователь\n
    Делает запрос к БД, получая уже записанные id для, \n
    исключает их из принятых в аргументе response_obj \n
    @response_obj - успешный ответ users.search метода, dict
    @user_id - ID текущего пользователя"""

    filtered_users = []
    if len(response_obj) > 0:
        for user in response_obj['items']:
            if user['can_access_closed']:
                filtered_users.append(user)
        if len(filtered_users) > 0:

            records = connection.execute(f"""SELECT candidate_id FROM people p
                                                    JOIN users u ON p.user_id = u.id 
                                                    WHERE u.id = {user_id}""").fetchall()

            all_ids = [u['id'] for u in filtered_users]
            if len(records) > 0:
                seen_ids = [i for i in flat_nested(records)]
                new_ids = list(set(all_ids).difference(seen_ids))
                if len(new_ids) > 0:
                    return new_ids
                return
            return all_ids


def flat_nested(array: Iterable):
    """Возвращает объект итератора\n
    Выпрямляет вложенные структуры, в том числе массив данных из БД,
    полученный через sqlalchemy\n"""
    for item in array:
        if isinstance(item, (sqlalchemy.engine.row.LegacyRow, list, tuple)):
            for sub_item in flat_nested(item):
                yield sub_item
        else:
            yield item


def choose_photos(query_maker, ids: list) -> list:
    """ Возвращает список tuple-ов\n
    Выполняет запрос photos.get, для каждого пользователя сортирует фото по популярности,\n
    формирует tuple('id владельца', [photo<id_владельца>_<id_фото>, ...]),\n
    где список фото - строки в нужном для параметра attachments метода messages.send формате,\n
    @query_maker - bound method VkApi.method, должен иметь ключ пользователя\n
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


def send_photos(api: vk_api.vk_api.VkApiMethod, array: Iterable, user_id: int, keyboard: Callable = None) -> None:
    """ Отправляет фото, заносит отправленные id в БД\n
    @api: api - объект класса  VkApiMethod\n
    @array: список формата [[owner_id, [photo_id1, photo_id2..], ...]]\n
    @user_id: ID текущего пользователя\n
    @keyboard - ожидается функция keyboarding"""

    for user_collage in array:
        api.messages.send(**usual_msg_prms(user_id),
                          attachment=[i for i in user_collage[1]],
                          message=f"https://vk.com/id{user_collage[0]}",
                          keyboard=keyboard()['search'])
        ins_into_people(user_id=user_id, candidate_id=user_collage[0])


def do_main_logic(bot_pool, features: dict, user_get_response, user_id: int, city_id: int = None):
    api_user = main_user.get_api()
    api_bot = main_bot.get_api()
    count = 85
    if features is None:
        sender(api_bot, user_id, 'Возраст', keyboard=keyboarding()['cancel'])
        for thing in bot_pool.listen():
            if thing.type == VkBotEventType.MESSAGE_NEW:
                answer = thing.message.get('text').casefold().strip()
                if answer != 'отмена':
                    if answer.isdigit() and int(answer) in range(14, 116):
                        answer = int(answer)
                        features = make_searching_portrait(user_get_response, age=answer, city_id=city_id)
                        print(features)
                        break
                    else:
                        sender(api_bot, user_id, 'Вводите цифры от 14 до 115', keyboard=keyboarding()['cancel'])
                else:
                    sender(api_bot, user_id, 'Поиск отменен', keyboard=keyboarding()['search'])
                    break
    if isinstance(features, dict) and len(features) == 5:
        sender(api_bot, user_id, 'Идет поиск...', keyboard=keyboarding()['empty'])
        found_people = api_user.users.search(sort=0, count=count, **features,
                                             fields='photo_id')
        unique_ids = filter_people(found_people, user_id)
        if unique_ids:
            photos_to_attach = choose_photos(main_user.method, unique_ids)
            send_photos(api_bot, photos_to_attach, user_id, keyboarding)
        else:
            sender(api_bot, user_id, 'Извините, никого не найдено', keyboard=keyboarding()['search'])


def main():
    create_tables()
    clear_users_db()
    bot_long_pool = VkBotLongPoll(main_bot, group_id=group_id)
    group_api = main_bot.get_api()
    user_api = main_user.get_api()

    for event in bot_long_pool.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            request = event.message.get('text').casefold().strip()
            user_id = event.message.get('from_id')
            if request != 'поиск':
                sender(group_api, user_id, text=welcome(),
                       keyboard=keyboarding()['search'])
            elif request == "поиск":
                user_get = group_api.users.get(user_ids=user_id, fields=['bdate', 'sex', 'relation', 'country', 'city'])
                ins_into_users(id=user_id, name=get_name(user_get))
                completeness = check(user_get)
                if completeness == 'country!':
                    sender(group_api, user_id, 'Страна поиска')
                    for co_event in bot_long_pool.listen():
                        break_outer = False
                        if co_event.type == VkBotEventType.MESSAGE_NEW:
                            country_name = co_event.message.get('text').capitalize()
                            country_id = check_country(country_name)
                            if country_id:
                                sender(group_api, user_id, 'Город')
                                for city_event in bot_long_pool.listen():
                                    if city_event.type == VkBotEventType.MESSAGE_NEW:
                                        city_name = city_event.message['text']
                                        city_id = check_city(country_id, city_name)
                                        if city_id:
                                            features = make_searching_portrait(user_get, city_id=city_id)
                                            do_main_logic(bot_long_pool, features, user_get, user_id, city_id)
                                            break_outer = True
                                            break
                                if break_outer:
                                    break
                elif completeness == 'city!':
                    country_name = user_get[0]['country']['title']
                    country_id = check_country(country_name)
                    if country_id:
                        sender(group_api, user_id, 'Уточните город')
                        for msg in bot_long_pool.listen():
                            if msg.type == VkBotEventType.MESSAGE_NEW:
                                city_name = msg.message.get('text')
                                city_id = check_city(country_id, city_name)
                                if city_id:
                                    features = make_searching_portrait(user_get, city_id=city_id)
                                    do_main_logic(bot_long_pool, features, user_get, user_id, city_id)
                                    break
                elif completeness == 'relation!':
                    sender(group_api, user_id, f'Выберите статус\n{status}')
                    for ev in bot_long_pool.listen():
                        if ev.type == VkBotEventType.MESSAGE_NEW:
                            relation = ev.message['text']
                            if relation.isdigit() and int(relation) in range(1, 9):
                                features = make_searching_portrait(user_get, relation=relation)
                                do_main_logic(bot_long_pool, features, user_get, user_id)
                                break

                elif completeness == 'ok!':
                    features = make_searching_portrait(user_get)
                    do_main_logic(bot_long_pool, features, user_get, user_id)


if __name__ == '__main__':
    main()
