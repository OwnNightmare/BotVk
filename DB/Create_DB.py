from sqlalchemy import MetaData, Table, Integer, String, ForeignKey,\
    delete, Column, insert, PrimaryKeyConstraint
import sqlalchemy
import vk_api
from pprint import pprint


db = 'postgresql://postgres:1710@localhost:5432/vkdb'
engine = sqlalchemy.create_engine(db)
connection = engine.connect()
metadata_obj = MetaData()

my_token = 'c3a240cff79d2ddac8a4e884df9b599090c3d54f166d62f5c2c3768d86a215fe590b7d62bc8a26a13ec15'  # offline level
api = vk_api.VkApi(token=my_token)
api = api.get_api()


def create_tables():
    Users = Table('users', metadata_obj,
                  Column('id', Integer, primary_key=True),
                  Column('name', String, nullable=True))

    People = Table('people', metadata_obj,
                   Column('user_id', Integer, ForeignKey('users.id'), nullable=False),
                   Column('candidate_id', Integer),
                   PrimaryKeyConstraint('candidate_id', 'user_id', name='pk_pair'))

    Countries = Table('countries', metadata_obj,
                      Column('id', Integer, primary_key=True),
                      Column('name', String, nullable=False)
                      )

    Cities = Table('cities', metadata_obj,
                   Column('id', Integer, primary_key=True),
                   Column('name', String, nullable=False)
                   )

    Country_citi = Table('country_city', metadata_obj,
                         Column('country_id', Integer, ForeignKey('countries.id')),
                         Column('city_id', Integer, ForeignKey('cities.id')),
                         PrimaryKeyConstraint('country_id', 'city_id', name='pk_co_ci')
                         )

    metadata_obj.create_all(engine)


def ins_into_users(**kwargs):
    """@kwargs -  id, name"""
    connection.execute(f"""INSERT INTO users
                        ({list(kwargs.keys())[0]}, {list(kwargs.keys())[1]})
                        VALUES({list(kwargs.values())[0]}, '{list(kwargs.values())[1]}')
                         ON CONFLICT DO NOTHING""")


def ins_into_people(**kwargs):
    """@kwargs -  user_id, candidate_id"""
    connection.execute(f"""INSERT INTO people
                        ({list(kwargs.keys())[0]}, {list(kwargs.keys())[1]})
                        VALUES({list(kwargs.values())[0]}, '{list(kwargs.values())[1]}')
                        ON CONFLICT DO NOTHING""")


def get_countries() -> dict:

    """Возвращает массив данных успешного ответа метода database.getCountries\n
    Доступ к списку стран по ключу 'items' возвращаемого словаря """

    countries_ = api.database.getCountries(need_all=0)
    return countries_


def get_cities_for_country(countries_: dict) -> list:
    """Возвращает список tuple-ов, где 0 элемент - ID страны, 1 элемент - словарь с ключами 'count' и 'items',
    где значение ключа 'items' - список городов страны, а 'count' - число городов; """
    data = []
    for country in countries_['items']:
        cities = api.database.getCities(country_id=country['id'])
        data.append((country['id'], cities))
    return data


def fill_countries(countries_: dict) -> None:
    for country in countries_['items']:
        connection.execute(f"""INSERT INTO countries(id, name)
                            VALUES({country['id']}, '{country['title']}')
                            ON CONFLICT DO NOTHING""")


def fill_cities(data: list) -> None:
    for tup in data:
        for city in tup[1]['items']:
            connection.execute(f"""INSERT INTO cities(id, name)
                                   VALUES({city['id']}, '{city['title']}')
                                    ON CONFLICT DO NOTHING""")


def bound_country_cities(data: list):
    for tup in data:
        for city in tup[1]['items']:
            connection.execute(f"""INSERT INTO country_city
                                   (country_id, city_id)
                                   VALUES({tup[0]}, {city['id']})
                                    ON CONFLICT DO NOTHING""")


def clear_users_db():
    connection.execute(f"""DELETE FROM people;
                        DELETE FROM users;""")


def check_country(country_name: str) -> int or None:

    country_name = country_name.capitalize()
    country_id_array = connection.execute(f"""SELECT id FROM countries
                                                 WHERE name = '{country_name}' """).fetchone()

    if country_id_array:
        return country_id_array[0]


def check_city(country_id: int, city_name: str) -> int or None:
    city = city_name.capitalize()
    city_id_array = connection.execute(f"""SELECT id FROM cities c
                                    JOIN country_city cc 
                                    ON c.id = cc.city_id
                                    WHERE cc.country_id = {country_id} and c.name = '{city}' """).fetchone()

    if city_id_array:
        return city_id_array[0]


if __name__ == '__main__':
    # create_tables()
    # countries = get_countries()
    # co_ci_array = get_cities_for_country(countries)
    # fill_countries(countries)
    # fill_cities(co_ci_array)
    # bound_country_cities(co_ci_array)

    ...






