import webbrowser
import requests
import datetime


class VkClient:

    app_id = '8044074'
    my_token = 'c3a240cff79d2ddac8a4e884df9b599090c3d54f166d62f5c2c3768d86a215fe590b7d62bc8a26a13ec15'  # offline level
    query_pattern = 'https://api.vk.com/method/METHOD?PARAMS&access_token=TOKEN&v=V'
    url_methods = 'https://api.vk.com/method/'

    @classmethod
    def open_page(cls):
        oauth_url = 'https://oauth.vk.com/authorize'
        params_open = "client_id=8044074&redirect_uri=https://oauth.vk.com/blank.html&scope=65538&display=page&response_type=token"
        webbrowser.open_new(f"{oauth_url}?{params_open}")

    def __init__(self, vk_token):
        self.vk_token = vk_token
        self.needed_params = {
            'access_token': self.vk_token,
            'v': '5.131'
        }
        self.portrait = {}

    def get_acc_info(self):
        """Получает информацию о профиле вк текущего пользователя"""
        method_name = 'account.getProfileInfo'
        response = requests.get(self.url_methods + method_name, params=self.needed_params)
        return response.json()

    def calc_age(self, acc_info):
        birth_info = acc_info['response']['bdate']
        birth_info = birth_info.split('.')
        birth_info = [int(i) for i in birth_info[::-1]]
        birthday = datetime.date(birth_info[0], birth_info[1], birth_info[2])
        curr_date = datetime.date.today()
        age = curr_date - birthday
        age = age.days // 364
        return age

    def form_portrait(self):
        data = self.get_acc_info()
        response = data['response']
        self.portrait['town'] = response.get('home_town')
        self.portrait['sex'] = response.get('sex')
        self.portrait['relation'] = response.get('relation')
        self.portrait['age'] = self.calc_age(data)
        return self.portrait

    def search(self):
        method_name = 'users.search'


if __name__ == '__main__':
    # VkClient.open_page()
    # user_token = input('Ваш Vk токен: ')
    me = VkClient(VkClient.my_token)
