import pytest
import unittest
from Vk.Bot import usual_msg_prms, make_searching_portrait, filter_people
from DB.Create_DB import db, engine, connection, clear_user_tables, create_tables


portrait = {
    "city": 72,
    "status": 1,
    "sex": 1,
    "age_from": 27,
    "age_to": 29
}

user_with_bad_bdate = [{'id': 222968943, 'first_name': 'Юрий', 'last_name': 'Борисов',
             'can_access_closed': True, 'is_closed': False, 'sex': 2,
             'bdate': '16.10', 'city': {'id': 72, 'title': 'Краснодар'},
             'relation': 1
                       }]
user_with_ok_bdate = [{
                'id': 222968943, 'first_name': 'Юрий', 'last_name': 'Борисов',
                'can_access_closed': True, 'is_closed': False, 'sex': 2,
                'bdate': '16.10.1995', 'city': {'id': 72, 'title': 'Краснодар'},
                'relation': 1
                }]

search_response = {'items': [
                    {'id': 789456456, 'first_name': 'Анастасия',
                        'last_name': 'Иванова', 'can_access_closed': False,
                        'is_closed': True,
                        'track_code': 'dc355b...'},
                   {'id': 654321, 'first_name': 'Елизавета', 'last_name': 'Банная',
                        'can_access_closed': True, 'is_closed': False,
                        'photo_id': '292_7243202', 'track_code': '0a168ba...'},
                   {'id': 5555555, 'first_name': 'Антонина', 'last_name': 'Антонова',
                       'can_access_closed': True, 'is_closed': False,
                        'photo_id': '555555_111111', 'track_code': '0a168ba...'}]}


class TestVkApi(unittest.TestCase):
    def setUp(self) -> None:
        connection.execute("""INSERT INTO users
                            (id, name)
                            VALUES(123, 'test_user')""")
        connection.execute("""INSERT INTO people
                            (user_id, candidate_id)
                            VALUES(123, 654321)""")

    def test_usual_msg_prms(self):
        """Тест получения информации о самом пользователе"""
        assert isinstance(usual_msg_prms(15315151), dict)

    def test_make_searching_portrait_and_calc_age(self):
        """Тест функции вычисления возраста"""
        assert make_searching_portrait(user_with_bad_bdate) is None
        assert isinstance(make_searching_portrait(user_with_ok_bdate), dict)
        assert len(make_searching_portrait(user_with_ok_bdate)) == 5

    def test_filter_ids(self):
        assert len(filter_people(search_response, 123)) == 1

    def tearDown(self) -> None:
        clear_user_tables()








