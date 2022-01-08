import pytest
import unittest
from Vk.VK_funcs import MyVkClass



class TestVkApi:
    """При инициализации класса создается объект класса VkClient - тестовый юзер с моим VK-токеном пользователя"""
    test_user = MyVkClass(MyVkClass.my_token)

    def test_get_acc_info(self):
        """Тест получения информации о самом пользователе"""
        assert TestVkApi.test_user.make_ids_list().status_code == 200
        assert TestVkApi.test_user.make_ids_list().json().get('response') is not None

    def test_calc_age(self):
        """Тест функции вычисления возраста"""

