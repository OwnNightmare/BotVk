import datetime
import sqlalchemy.engine.row
import json

my_token = 'c3a240cff79d2ddac8a4e884df9b599090c3d54f166d62f5c2c3768d86a215fe590b7d62bc8a26a13ec15'  # offline level


# class MyVkClass:
#
#     app_id = '8044074'
#     my_token = 'c3a240cff79d2ddac8a4e884df9b599090c3d54f166d62f5c2c3768d86a215fe590b7d62bc8a26a13ec15'  # offline level
#     query_pattern = 'https://api.vk.com/method/METHOD?PARAMS&access_token=TOKEN&v=V'
#     url_methods = 'https://api.vk.com/method/'
#     bot_token = '3ed6d7a1af9a6f6789559a925b14b30963b1514d943c41926cb88b28ea1091dd321d9ddc494cfa694ba54'
#
#     def __init__(self, vk_token):
#         self.vk_token = vk_token
#         self.usual_params = {
#             'access_token': self.vk_token,
#             'v': '5.131'
#         }
#         self.photo_params = {'owner_id': '000000001',
#                              'album_id': 'profile',
#                              'extended': 1,
#                             'access_token': self.vk_token,
#                              'v': '5.131'}
#         self.portrait = {}


def flat_nested(array):
    for item in array:
        if isinstance(item, (sqlalchemy.engine.row.LegacyRow, list, tuple)):
            for sub_item in flat_nested(item):
                yield sub_item
        else:
            yield item


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


