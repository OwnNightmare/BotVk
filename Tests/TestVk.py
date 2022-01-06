import pytest
import unittest
from Vk.Vk_module import VkClient


class TestVkApi:
    test_user = VkClient(VkClient.my_token)

    def test_get_acc_info(self):
        assert  TestVkApi.test_user.get_acc_info().status_code == 200
        assert TestVkApi.test_user.get_acc_info().json().get('response') is not None


    def test_calc_age(self):
        assert type(TestVkApi.test_user.calc_age(TestVkApi.test_user.get_acc_info().json())) is int


    def test_format_portrait(self):
        assert TestVkApi.test_user.form_portrait()['age'] > -1
        assert len(TestVkApi.test_user.form_portrait()['town']) > 0
        assert TestVkApi.test_user.form_portrait()['sex'] > 0
        assert TestVkApi.test_user.form_portrait()['relation'] > -1
