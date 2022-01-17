import vk_api
import time
import datetime
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from random import shuffle
from typing import Callable, Iterable
import sqlalchemy.engine.row
import json
from typing import Any
from DB.Create_DB import check_country, check_city, make_and_fill_db,\
    clear_user_tables, ins_into_people, ins_into_users, connection
from tokens import user_access_token, group_access_token, group_id  # Импорт токенов и ID сообщества


def usual_msg_prms(user_id: int) -> dict:
    """Возвращает обязательные параметры для сообщения в виде словаря:\n
       @user_id - id текущего пользователя ВК"""

    params = {'user_id': user_id,
              'random_id': int(time.time() * 1000),
              'peer_id': group_id}
    return params


def sender(api, user_id: int, text: str = None, attachment: Any = None, keyboard=None) -> None:
    """ Отправляет сообщение пользователю в группу, ничего не возвращает\n
    @api - объект класса  VkApiMethod, обязательный параметр\n
    @user_id -  ВК ID  текущего пользователя, обязательный параметр\n
    @text - текст сообщения, обязательный если attachments=None\n
    @attachments - вложения, обязательный если text=None\n
    @keyboard - отправляемая клавиатура, необязательный"""

    params = {'user_id': user_id,
              'random_id': int(time.time() * 1000),
              'peer_id': group_id * -1}

    api.messages.send(**params, message=text, attachment=attachment, keyboard=keyboard)


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
                   'city_choice': """{"one_time": false, "buttons":[
                                [{"action": {"type": "text", "label": "Начать"}, "color": "positive"}, 
                                {"action": {"type": "text", "label": "Другой"}, "color": "primary"}]]}""",
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


def check_location(user_get: list) -> str:
    """Если не получена страна пользователя возвращает: country!
    Если не получен город возвращает: city!
    Если полученные все данные возвращает: ok! """
    for user in user_get:
        if not user.get('country'):
            return 'country!'
        if not user.get('city'):
            return 'city!'
    return 'ok!'


def make_features(user_get_response: list, age: int = None, city_id: int = None, relation: int = None) -> dict:
    """ Возвращает критерии поиска людей для текущего пользователя\n
    @user_get_response - успешный ответ метода users.get\n
    @age - возраст пользователя\n
    @city_id - ID города
    @relation - статус пользователя от (0 до 8)"""

    acc_info = user_get_response[0]
    features = {}
    if not city_id:
        features['city'] = acc_info.get('city').get('id')
    else:
        features['city'] = city_id
    if not relation:
        features['status'] = acc_info.get('relation')
    else:
        features['status'] = relation
    if not age:
        if acc_info.get('bdate'):
            age = calc_age(acc_info.get('bdate'))
    if isinstance(age, int) and age in range(12, 120):
        sex = acc_info.get('sex')
        if int(sex) == 2:
            features['sex'] = 1
            features['age_from'] = age - 2
            features['age_to'] = age
        elif sex == 1:
            features['sex'] = 2
            features['age_from'] = age - 1
            features['age_to'] = age + 2
        else:
            features['sex'] = 0
            features['age_from'] = age - 1
            features['age_to'] = age + 1
        return features


def filter_people(users_search_resp: dict, user_id: int) -> dict or None:
    """Возвращает список id страниц, которых еще не видел пользователь\n
    Делает запрос к БД, получая уже записанные id для, \n
    исключает их из принятых в аргументе response_obj \n
    @user_search_resp - успешный ответ метода users.search
    @user_id - ID текущего пользователя"""

    filtered_users = []
    if len(users_search_resp) > 0:
        for user in users_search_resp['items']:
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


def wrap_photos(api, array: Iterable, user_id: int) -> None:
    """ Отправляет фото, заносит отправленные id в БД\n
    @api: - объект класса  VkApiMethod\n
    @array: список формата [[owner_id, [photo_id1, photo_id2..], ...]]\n
    @user_id: ID текущего пользователя\n"""

    for user_collage in array:
        sender(api, user_id, text=f"https://vk.com/id{user_collage[0]}", attachment=[i for i in user_collage[1]])
        ins_into_people(user_id=user_id, candidate_id=user_collage[0])
    sender(api, user_id, 'Поиск окончен', keyboard=keyboarding()['search'])


def ask_for_country(api, user_id, bot_pool):
    """
    :param api: объект класса  VkApiMethod
    :param user_id: ID пользователя ВК
    :param bot_pool: объект класса VkBotLongPoll
    :return: country_id
    """
    sender(api, user_id, 'Страна поиска', keyboard=keyboarding()['cancel'])
    for event in bot_pool.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            req_country = event.message.get('text')
            if req_country.casefold() == 'отмена':
                sender(api, user_id, 'Поиск отменен', keyboard=keyboarding()['search'])
                return
            country_id = check_country(req_country)
            if country_id:
                return country_id
            sender(api, user_id, 'Извините, не могу произвести поиск в этой стране')


def ask_for_city(api, user_id: int, bot_pool, country_id: int):
    """
    :param api: объект класса  VkApiMethod
    :param user_id: ID пользователя ВК
    :param bot_pool: объект класса VkBotLongPoll
    :param country_id: ID страны
    :return: city_id
    """
    sender(api, user_id, 'Город', keyboard=keyboarding()['cancel'])
    for event in bot_pool.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            req_city = event.message['text']
            if req_city.casefold() == 'назад':
                # sender(api, user_id, 'Страна поиска', keyboard=keyboarding()['cancel'])
                country = ask_for_country(api, user_id, bot_pool)
            elif req_city.casefold() == 'отмена':
                sender(api, user_id, 'Поиск отменен', keyboard=keyboarding()['search'])
                return
            city_id = check_city(country_id, req_city)
            if city_id:
                return city_id
            else:
                sender(api, user_id, 'Не могу найти город, попробуйте '
                                         'указать близлежащий крупный', keyboard=keyboarding()['cancel'])


def ask_for_age(api, bot_pool, features: dict, user_get_response: list, user_id, city_id: int = None):
    """
    :param api: объект класса  VkApiMethod
    :param bot_pool: объект класса VkBotLongPoll
    :param features: словарь с критериями поиска
    :param user_get_response: успешный ответ API метода users.get
    :param user_id: ID пользователя ВК
    :param city_id: ID города
    :return: features
    """
    if features is None:
        sender(api, user_id, 'Возраст', keyboard=keyboarding()['cancel'])
        for thing in bot_pool.listen():
            if thing.type == VkBotEventType.MESSAGE_NEW:
                answer = thing.message.get('text').casefold().strip()
                if answer != 'отмена':
                    if answer.isdigit() and int(answer) in range(14, 116):
                        answer = int(answer)
                        features = make_features(user_get_response, age=answer, city_id=city_id)
                        return features
                    else:
                        sender(api, user_id, 'Вводите цифры от 14 до 115', keyboard=keyboarding()['cancel'])
                else:
                    sender(api, user_id, 'Поиск отменен', keyboard=keyboarding()['search'])
                    return
    else:
        return features


def search_and_send(api_bot, user_main, features: dict, user_id: int):
    """
    :param api_bot: объект класса  VkApiMethod
    :param user_main: объект класса VkApi, с токеном доступа пользователя
    :param features: словарь с критериями поиска
    :param user_id: ID пользователя ВК
    :return: None
    """
    api_user = user_main.get_api()
    count = 75  # Количество людей получаемых в ответе users.search
    if isinstance(features, dict) and len(features) == 5:
        sender(api_bot, user_id, 'Идет поиск...', keyboard=keyboarding()['empty'])
        found_people = api_user.users.search(sort=0, **features, count=count,
                                             fields='photo_id')
        unique_ids = filter_people(found_people, user_id)
        if unique_ids:
            photos_to_attach = choose_photos(user_main.method, unique_ids)
            wrap_photos(api_bot, photos_to_attach, user_id)
        else:
            sender(api_bot, user_id, 'Извините, никого не найдено', keyboard=keyboarding()['search'])
            return False


def main():
    """Очищаем таблицы, созданные make_and_fill_db, получаем экземпляры класса VkApi, для работы с API VK,
начинаем прослушку сервера методом listen(), если событие, случившееся на сервере - новое сообщение
 (VkBotEventType.MESSAGE_NEW), то получаем id пользователя(далее П) и проверяем текст запроса.\n
 Если запрос не равен 'поиск' - отправляем приветственное сообщение с инструкцией к боту и клавиатуру с кнопкой
 'search'\n Если запрос == 'поиск': исполняем API метод 'users.get', для получения инфы о П.\n
 В БД записываем ID и Имя П функцией ins_into_users, проверяем указаны ли Страна и Город:
- если не указана страна(и как следствие город) - запрашиваем ввод страны
- если нет только города: проверяется есть ли указанная в профиле страна в нашей локальной БД, которая сод-ит только 18
  стран, если есть - запрос и проверка города, если страны нет - в поиске отказывается
- если город и страна указаны изначально - спрашиваем начать ли поиск или указать город вручную
    """
    clear_user_tables()
    user_main = vk_api.VkApi(token=user_access_token)
    bot_main = vk_api.VkApi(token=group_access_token)
    bot_long_pool = VkBotLongPoll(bot_main, group_id=group_id)
    api_bot = bot_main.get_api()

    for event in bot_long_pool.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            request = event.message.get('text').casefold().strip()
            user_id = event.message.get('from_id')
            if request != 'поиск':
                sender(api_bot, user_id, text=welcome(),
                       keyboard=keyboarding()['search'])
            elif request == "поиск":
                user_get = api_bot.users.get(user_ids=user_id, fields=['bdate', 'sex', 'relation', 'country', 'city'])
                ins_into_users(id=user_id, name=get_name(user_get))
                location = check_location(user_get)
                if location == 'country!':
                    country_id = ask_for_country(api_bot, user_id, bot_long_pool)
                    if country_id:
                        city_id = ask_for_city(api_bot, user_id, bot_long_pool, country_id)
                        if city_id:
                            features = make_features(user_get, city_id=city_id)
                            features = ask_for_age(api_bot, bot_long_pool, features, user_get, user_id, city_id)
                            if features:
                                result = search_and_send(api_bot, user_main, features, user_id)
                elif location == 'city!':
                    country_name = user_get[0]['country']['title']
                    country_id = check_country(country_name)
                    if country_id:
                        city_id = ask_for_city(api_bot, user_id, bot_long_pool, country_id)
                        if city_id:
                            features = make_features(user_get, city_id=city_id)
                            features = ask_for_age(api_bot, bot_long_pool, features, user_get, user_id, city_id)
                            if features:
                                search_and_send(api_bot, user_main, features, user_id)
                elif location == 'ok!':
                    sender(api_bot, user_id, 'Выполнить поиск в вашем городе:\nначать, \n'
                                             'Выбрать другой город:\nдругой', keyboard=keyboarding()['city_choice'])
                    for ev in bot_long_pool.listen():
                        if ev.t == VkBotEventType.MESSAGE_NEW:
                            if ev.message['text'].casefold() == 'начать':
                                features = make_features(user_get)
                                features = ask_for_age(api_bot, bot_long_pool, features, user_get, user_id)
                                if features:
                                    search_and_send(api_bot, user_main, features, user_id)
                                    break
                            elif ev.message['text'].casefold() == 'другой':
                                city_id = ask_for_city(api_bot, user_id, bot_long_pool, user_get[0]['country']['id'])
                                if city_id:
                                    features = make_features(user_get, city_id=city_id)
                                    features = ask_for_age(api_bot, bot_long_pool, features, user_get, user_id)
                                    if features:
                                        search_and_send(api_bot, user_main, features, user_id)
                                else:
                                    break


if __name__ == '__main__':
    if make_and_fill_db(): print('Bot is ready')  # Можно закомментировать при повторном запуске
    main()
