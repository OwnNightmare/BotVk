import webbrowser
import requests


class VkClient:

    app_id = '8044074'
    my_token_offline = 'c3a240cff79d2ddac8a4e884df9b599090c3d54f166d62f5c2c3768d86a215fe590b7d62bc8a26a13ec15'

    @staticmethod
    def _open_page():
        oauth_url = 'https://oauth.vk.com/authorize'
        params_open = "client_id=8044074&redirect_uri=https://oauth.vk.com/blank.html&scope=65538&display=page&response_type=token"
        webbrowser.open_new(f"{oauth_url}?{params_open}")

    def __init__(self, vk_token):
        self.vk_token = vk_token


if __name__ == '__main__':
    VkClient._open_page()
    user_token = input('Ваш Vk токен: ')
    me = VkClient(VkClient.my_token_offline)
