import webbrowser
import requests
import datetime
from typing import Any
import Vk

vk_url= 'https://vk.com/'

def calc_age(acc_info: dict):
    """acc_info - значение ключа 'response' json ответа Vk API метода account.getProfileInfo"""
    birth_info = acc_info['bdate']
    birth_info = birth_info.split('.')
    birth_info = [int(i) for i in birth_info[::-1]]
    birthday = datetime.date(birth_info[0], birth_info[1], birth_info[2])
    curr_date = datetime.date.today()
    age = curr_date - birthday
    age = age.days // 364
    return age


def searching_portrait(acc_info: dict):
    """ Возвращает "портрет" искомого человека, составленный на основании acc_info.
    acc_info - значение ключа 'response'  успешного json ответа Vk API метода account.getProfileInfo"""
    searching_portrait = {}
    response = acc_info
    searching_portrait['city'] = response.get('city').get('id')
    searching_portrait['status'] = response.get('relation')
    own_age = calc_age(response)
    sex = response.get('sex')
    if sex == 2:
        searching_portrait['sex'] = 1
        searching_portrait['age_from'] = own_age - 2
        searching_portrait['age_to'] = own_age
    elif sex == 1:
        searching_portrait['sex'] = 2
        searching_portrait['age_from'] = own_age - 1
        searching_portrait['age_to'] = own_age + 2
    else:
        searching_portrait['sex'] = ''
        searching_portrait['age_from'] = own_age - 1
        searching_portrait['age_to'] = own_age + 1
    return searching_portrait


def get_ids(found_users: dict):
    """ found_users -  успешный результат выполнения метода users.search,
    список пользователей доступен по ключу 'items' """
    users_list = found_users['items']
    ids = [user['id'] for user in users_list]
    # prepared_list = []
    # for user in users_list:
    #     temp_dict = {'name': f"{user.get('first_name')} {user.get('last_name')}", 'user_url': f"{vk_url}id{user['id']}"}
    #     prepared_list.append(temp_dict)
    return ids


def prepare_attachment(users):
    """ Формирует параметр 'attachments' для метода messages.send
    аргумент users - результат выполнения функции prepare_found_users
    Типы вложений type=link, type=photo
    """
    attach = {}
    for user in users:
        attach = {'attachment': {'type': 'link', 'url': user['user_url'], 'title': user['name']}}
    return attach


class MyVkClass:

    app_id = '8044074'
    my_token = 'c3a240cff79d2ddac8a4e884df9b599090c3d54f166d62f5c2c3768d86a215fe590b7d62bc8a26a13ec15'  # offline level
    query_pattern = 'https://api.vk.com/method/METHOD?PARAMS&access_token=TOKEN&v=V'
    url_methods = 'https://api.vk.com/method/'
    bot_token = '3ed6d7a1af9a6f6789559a925b14b30963b1514d943c41926cb88b28ea1091dd321d9ddc494cfa694ba54'

    @classmethod
    def open_page(cls):
        oauth_url = 'https://oauth.vk.com/authorize'
        params_open = "client_id=8044074&redirect_uri=https://oauth.vk.com/blank.html&scope=65538&display=page&response_type=token"
        webbrowser.open_new(f"{oauth_url}?{params_open}")

    def __init__(self, vk_token):
        self.vk_token = vk_token
        self.usual_params = {
            'access_token': self.vk_token,
            'v': '5.131'
        }
        self.photo_params = {'owner_id': '000000001',
                             'album_id': 'profile',
                             'extended': 1,
                            'access_token': self.vk_token,
                             'v': '5.131'}
        self.portrait = {}

    def make_ids_list(self, method_name, **kwargs):
        """Шаблон вызова Vk API метода
         method_name - имя метода"""
        if method_name == 'getProfileInfo':
            response = requests.get(self.url_methods + method_name, params=self.usual_params)
            return response
        elif method_name == 'photos.get':
            photos = []
            for user_id in kwargs['ids']:
                self.photo_params['owner_id'] = user_id
                photos.append(requests.get(self.url_methods + method_name, params=self.photo_params).json())
            return photos



    def search(self):
        method_name = 'users.search'


if __name__ == '__main__':
    # VkClient.open_page()
    # user_token = input('Ваш Vk токен: ')
    me = MyVkClass(MyVkClass.my_token)


