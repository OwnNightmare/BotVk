import vk_api
from pprint import pprint
from Vk.VkBoting import my_token

api = vk_api.VkApi(token=my_token)
api = api.get_api()


def get_countries():
    countries = api.database.getCountries(need_all=0)
    return countries


def get_cities(countries: dict):
    data = []
    for country in countries['items']:
        cities = api.database.getCities(country_id=country['id'])
        data.append((country['id'], cities))
    return data


pprint(get_cities(get_countries()))

