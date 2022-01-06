import vk_api

bot_token = '3ed6d7a1af9a6f6789559a925b14b30963b1514d943c41926cb88b28ea1091dd321d9ddc494cfa694ba54'


vk_session = vk_api.VkApi(token=bot_token, client_secret='7bef404e7bef404e7bef404e347b95fe6477bef7bef404e1a39ff1888d02c7dc0189687')
vk_session.server_auth()
