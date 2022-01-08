import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.longpoll import VkLongPoll, VkEventType
import time
from datetime import datetime
from vk_api.keyboard import *
from Vk import VK_funcs
from VK_funcs import calc_age, searching_portrait, MyVkClass, get_ids, prepare_attachment
from pprint import pprint
import json

me = MyVkClass(MyVkClass.my_token)
bot_token = '3ed6d7a1af9a6f6789559a925b14b30963b1514d943c41926cb88b28ea1091dd321d9ddc494cfa694ba54'
group_id = 209978754
att = [{'type': 'link', 'url': 'https://vk.com/'}]


def get_message_id():
    ms = int(time.time())
    return ms


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
    photos_response = []
    sorted_photos = []
    popular_photos = []
    for user_id in ids:
        photos_response.append(query_maker('photos.get', values={'owner_id': user_id, 'album_id': 'profile',
                                                        'extended': 1, 'photo_sizes': 0}))

    for user in photos_response:
        user_photo_list = user['items']
        user_photo_list: list
        user_photo_list.sort(key=lambda d: d['likes']['count'] + d['comments']['count'], reverse=True)
        sorted_photos.append(user_photo_list)

        with open('all_photos_sorted.json', mode='w') as f:
            json.dump(sorted_photos, f, indent=2)

    user_count = 0
    for user in sorted_photos[::-1]:
        foto_count = 0
        if user_count == 3:
            break
        for photo in user:
            popular_photos.append({'owner_id': photo['owner_id'], 'photo_id': photo['id']})
            foto_count += 1
            if foto_count == 3:
                break
        user_count += 1

    with open('chosen_photos_data.json', mode='w') as f:
        json.dump(popular_photos, f, indent=2)

    return popular_photos




def main():
    vk_session = vk_api.VkApi(token=bot_token)
    bot_meth = vk_session.method
    bot_longpool = VkBotLongPoll(vk_session, group_id=group_id)
    long_pool = VkLongPoll(vk_session, group_id=group_id)
    api = vk_session.get_api()
    vk_user = vk_api.VkApi(token=MyVkClass.my_token)
    user_meth = vk_user.method
    vk_user = vk_user.get_api()
    profile_info = vk_user.account.getProfileInfo()
    user_portrait = searching_portrait(profile_info)

    for event in bot_longpool.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            text = event.message.get('text').lower()
            user_id = event.message.get('from_id')
            if text == 'id':
                api.messages.send(**typical_message_params(event),
                                 message=f"ID страницы: {user_id}")
            elif text == 'f':
                api.messages.send(**typical_message_params(event),
                                  message=f"ID страницы: {user_id}",
                                  attachment=['photo1_456264771', 'photo1_456264771', 'photo1_456264771'])
                users_get = api.users.get(user_ids=user_id, fields=['bdate', 'sex', 'relation', 'city'])
                searching_person = searching_portrait(users_get[0])
                found_users = vk_user.users.search(sort=0, count=20, is_closed=False, **searching_person,
                                                   fields='photo_id')
                filtered_users = filter_closed(found_users)
                pprint(filtered_users)
                ids = get_ids(filtered_users)
                owner_and_photo = choose_photos(user_meth, ids)
                pprint(owner_and_photo)

                # api.messages.send(**typical_message_params(event),
                #                  attachment=[f'photo1_456264771'],
                #                  message='Це Дуров, https://vk.com/id000000001''))')
            elif text == 'пока':
                api.messages.send(**typical_message_params(event), message='Пока =)')
            elif text == 'h':
                api.messages.send(**typical_message_params(event), message=show_help())
            else:
                api.messages.send(**typical_message_params(event), message=f"Команда неизвестна")
                time.sleep(0.5)
                api.messages.send(**typical_message_params(event), message=show_help())
        # except BaseException as er:
        #     with open('errors_log.txt', 'a') as f:
        #         now = datetime.now()
        #         f.writelines([str(er), str(now), '\n'])


if __name__ == '__main__':
    main()




















    # for event in bot_longpool.listen():
    #     if event.type == VkBotEventType.MESSAGE_NEW:
    #         print('new m')
    #         vk.messages.send(user_id=event.message['from_id'], random_id=get_message_id(), peer_id='-209978754',
    #                          message='https://oauth.vk.com/authorize?client_id=8044074&redirect_uri=https://oauth.vk.com/blank.html&scope=65538&display=mobile&response_type=token')






# if __name__ == '__main__':
#     main()
