import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.longpoll import VkLongPoll, VkEventType
import time
from datetime import datetime
from VK_funcs import make_searching_portrait, get_ids, my_token
import json
from random import shuffle

bot_token = '3ed6d7a1af9a6f6789559a925b14b30963b1514d943c41926cb88b28ea1091dd321d9ddc494cfa694ba54'
group_id = 209978754


def get_message_id():
    mcrs = int(time.time() * 1000)
    return mcrs


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


def choose_photos(query_maker: 'VkApi.method', ids):
    """
    query_maker - bound method VkApi.method, должен иметь ключ пользователя
    ids - список ID страниц, у которых нужно запросить фото через photos.get"""
    resp_obj_store = []  # Список для объектов успешного ответа photos.get, все фото 1 пользователя и метаданные к ним
    sorted_photos = []
    users_photos = []
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
            return owner_and_photos
        for photo in user:
            if foto_count > 2:
                break
            users_photos.append(f"photo{photo['owner_id']}_{photo['id']}")
            foto_count += 1
        if photo.get('owner_id') is not None and len(str(photo['owner_id'])) > 0:
            if len(users_photos) >= 3:
                owner_and_photos.append((photo['owner_id'], users_photos))
                user_count += 1
                with open('ids array.json', mode='w') as f:
                    json.dump(owner_and_photos, f, indent=2)


def send_photos(query_maker, event, array):
    """query_maker: объект класса VkApiMethod,  для обращения к API методам, как к обычным,
    event: событие VkBotLongPoll.listen(),
    array: список формата [[owner_id, [photo_id1, photo_id2..], ...]] """
    for user_collage in array:
        query_maker.messages.send(**typical_message_params(event),
                                  attachment=[i for i in user_collage[1]],
                                  message=f"https://vk.com/id{user_collage[0]}")


def main():
    main_user = vk_api.VkApi(token=my_token)
    main_bot = vk_api.VkApi(token=bot_token)
    bot_longpool = VkBotLongPoll(main_bot, group_id=group_id)
    group_api = main_bot.get_api()
    user_api = main_user.get_api()

    for event in bot_longpool.listen():
        # try:
            if event.type == VkBotEventType.MESSAGE_NEW:
                text = event.message.get('text').lower()
                user_id = event.message.get('from_id')
                if text == 'id':
                    group_api.messages.send(**typical_message_params(event),
                                            message=f"ID страницы: {user_id}")
                elif text == 'f':
                    group_api.messages.send(**typical_message_params(event), message='Ищем пару...')
                    users_get = group_api.users.get(user_ids=user_id, fields=['bdate', 'sex', 'relation', 'city'])
                    with open('vk_self_info.json', 'w') as f:
                        json.dump(users_get, f, indent=2, ensure_ascii=False)
                    features = make_searching_portrait(users_get[0])
                    if features:
                        beginning = datetime.now()
                        count = 22
                        found_users = user_api.users.search(sort=0, count=count, **features,
                                                            fields='photo_id')
                        filtered_users = filter_closed(found_users)
                        ids = get_ids(filtered_users)
                        photo_array = choose_photos(main_user.method, ids)
                        send_photos(group_api, event, photo_array)
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
        # except BaseException as er:
        #     with open('errors_log.txt', 'a') as f:
        #         now = datetime.now()
        #         f.writelines([str(er), str(now), '\n'])
        #         print(er.with_traceback(None))
        #         return


if __name__ == '__main__':
    main()

