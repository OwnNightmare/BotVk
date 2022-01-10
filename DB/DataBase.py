import sqlalchemy
from sqlalchemy import MetaData, Table, Integer, String, ForeignKey,\
    delete, Column, insert, PrimaryKeyConstraint, select
from sqlalchemy.dialects.postgresql import insert as insert_psql


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

    metadata_obj.create_all(engine)


    # inst_stmt = insert_psql(Users).values(id=1232412, name='Борисов Юра')
    # do_nothing_on = inst_stmt.on_conflict_do_nothing(
    #     index_elements=['id']
    # )
    #
    # print(inst_stmt.compile)
    # with engine.connect() as conn:
    #     result = conn.execute(do_nothing_on)


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
                       """)


def clear_db():
    connection.execute(f"""DELETE FROM people;
                        DELETE FROM users;""")










