import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.longpoll import VkLongPoll, VkEventType
import time
from vk_api.keyboard import *
from Vk import VK_funcs
from VK_funcs import calc_age, searching_portrait, MyVkClass
from pprint import pprint

bot_token = '3ed6d7a1af9a6f6789559a925b14b30963b1514d943c41926cb88b28ea1091dd321d9ddc494cfa694ba54'
group_id = 209978754


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


def main():
    vk_session = vk_api.VkApi(token=bot_token)
    bot_longpool = VkBotLongPoll(vk_session, group_id=group_id)
    long_pool = VkLongPoll(vk_session, group_id=group_id)
    vk = vk_session.get_api()
    vk_user = vk_api.VkApi(token=MyVkClass.my_token)
    vk_user = vk_user.get_api()
    profile_info = vk_user.account.getProfileInfo()
    user_portrait = searching_portrait(profile_info)

    for event in bot_longpool.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            text = event.message.get('text').lower()
            user_id = event.message.get('from_id')
            if text == 'id':
                vk.messages.send(**typical_message_params(event),
                                 message=f"ID страницы: {user_id}")
            elif text == 'f':
                users_get = vk.users.get(user_ids=user_id, fields=['bdate', 'sex', 'relation', 'city'])
                print(users_get)
                searching_person = searching_portrait(users_get[0])
                print(searching_person)
                users_search = vk_user.users.search(sort=0, count=10, fields=['photo_max_orig', 'relation'],
                                                    **searching_person)
                pprint(users_search)

                vk.messages.send(**typical_message_params(event),
                                      message='Сервис на стадии разработки')
            elif text == 'пока':
                vk.messages.send(**typical_message_params(event), message='Пока =)')
            elif text == 'h':
                vk.messages.send(**typical_message_params(event), message=show_help())
            else:
                vk.messages.send(**typical_message_params(event), message=f"Команда неизвестна")
                time.sleep(0.5)
                vk.messages.send(**typical_message_params(event), message=show_help())

    # for event in bot_longpool.listen():
    #     # while convers:
    #         if event.type == VkBotEventType.MESSAGE_NEW:
    #             if event.message['text'].lower() == 'id':
    #                 vk.messages.send(**typical_message_params(event), message=event.message['from_id'])
    #             elif event.message['text'].lower() == 'найти':
    #                 vk.messages.send(**typical_message_params(event), message='Ля мы какие, сразу пару, а вот не готово, подожди чуток')
    #             elif event.message['text'].lower() == 'пока':
    #                 vk.messages.send(**typical_message_params(event), message='До новых встреч =)')
    #                 break
    #             else:
    #                 vk.messages.send(**typical_message_params(event), message='Ой, такую команду мы не знаем')





if __name__ == '__main__':
    main()




















    # for event in bot_longpool.listen():
    #     if event.type == VkBotEventType.MESSAGE_NEW:
    #         print('new m')
    #         vk.messages.send(user_id=event.message['from_id'], random_id=get_message_id(), peer_id='-209978754',
    #                          message='https://oauth.vk.com/authorize?client_id=8044074&redirect_uri=https://oauth.vk.com/blank.html&scope=65538&display=mobile&response_type=token')






# if __name__ == '__main__':
#     main()
