import pytest
import unittest
from Vk.VkBoting import usual_msg_prms, calc_age, make_searching_portrait

portrait = {
    "city": 72,
    "status": 1,
    "sex": 1,
    "age_from": 27,
    "age_to": 29
}

user_with_bad_bdate = {'id': 222968943, 'first_name': 'Юрий', 'last_name': 'Борисов',
             'can_access_closed': True, 'is_closed': False, 'sex': 2,
             'bdate': '16.10', 'city': {'id': 72, 'title': 'Краснодар'},
             'relation': 1
                       }
user_with_ok_bdate = {
                'id': 222968943, 'first_name': 'Юрий', 'last_name': 'Борисов',
                'can_access_closed': True, 'is_closed': False, 'sex': 2,
                'bdate': '16.10.1995', 'city': {'id': 72, 'title': 'Краснодар'},
                'relation': 1
                }


class TestVkApi:
    """При инициализации класса создается объект класса VkClient - тестовый юзер с моим VK-токеном пользователя"""


    def test_usual_msg_prms(self):
        """Тест получения информации о самом пользователе"""
        assert isinstance(usual_msg_prms(15315151), dict)

    def test_make_searching_portrait_and_calc_age(self):
        """Тест функции вычисления возраста"""
        assert make_searching_portrait(user_with_bad_bdate) is None
        assert isinstance(make_searching_portrait(user_with_ok_bdate), dict)
        assert len(make_searching_portrait(user_with_ok_bdate)) == 5








