import sqlalchemy
from sqlalchemy import MetaData, Table, Integer, String, ForeignKey,\
    delete, Column, insert, PrimaryKeyConstraint
from cities import get_countries

db = 'postgresql://postgres:1710@localhost:5432/vkdb'
engine = sqlalchemy.create_engine(db)
connection = engine.connect()
metadata_obj = MetaData()



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


def fill_countries(countries: dict) -> None:
    for country in countries['items']:
        connection.execute(f"""INSERT INTO countries(id, name)
                            VALUES({country['id']}, {country['title']})
                            ON CONFLICT DO NOTHING""")


def clear_tables():
    connection.execute(f"""DELETE FROM people;
                        DELETE FROM users;""")


if __name__ == '__main__':
    create_tables()
    fill_countries(get_countries())







