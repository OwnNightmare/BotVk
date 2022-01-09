import datetime


class MyVkClass:

    app_id = '8044074'
    my_token = 'c3a240cff79d2ddac8a4e884df9b599090c3d54f166d62f5c2c3768d86a215fe590b7d62bc8a26a13ec15'  # offline level
    query_pattern = 'https://api.vk.com/method/METHOD?PARAMS&access_token=TOKEN&v=V'
    url_methods = 'https://api.vk.com/method/'
    bot_token = '3ed6d7a1af9a6f6789559a925b14b30963b1514d943c41926cb88b28ea1091dd321d9ddc494cfa694ba54'

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
    _portrait = {}
    response = acc_info
    _portrait['city'] = response.get('city').get('id')
    _portrait['status'] = response.get('relation')
    own_age = calc_age(response)
    sex = response.get('sex')
    if sex == 2:
        _portrait['sex'] = 1
        _portrait['age_from'] = own_age - 2
        _portrait['age_to'] = own_age
    elif sex == 1:
        _portrait['sex'] = 2
        _portrait['age_from'] = own_age - 1
        _portrait['age_to'] = own_age + 2
    else:
        _portrait['sex'] = ''
        _portrait['age_from'] = own_age - 1
        _portrait['age_to'] = own_age + 1
    return _portrait


def get_ids(users_list: list):
    """ users_list - список словарей, где каждый - данные о найденном пользователе
    список пользователей доступен по ключу 'items' """
    ids = [user['id'] for user in users_list]
    return ids


if __name__ == '__main__':
    # VkClient.open_page()
    # user_token = input('Ваш Vk токен: ')
    me = MyVkClass(MyVkClass.my_token)

    # @classmethod
    # def open_page(cls):
    #     oauth_url = 'https://oauth.vk.com/authorize'
    #     params_open = "client_id=8044074&redirect_uri=https://oauth.vk.com/blank.html&scope=65538&display=page&response_type=token"
    #     webbrowser.open_new(f"{oauth_url}?{params_open}")


