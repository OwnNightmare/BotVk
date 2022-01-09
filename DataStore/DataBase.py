import sqlalchemy
from sqlalchemy import MetaData, Table, Integer, String, ForeignKey, PrimaryKeyConstraint, Column

db = 'postgresql://postgres:1710@localhost:5432/vkdb'
engine = sqlalchemy.create_engine(db)
connect = engine.connect()
engine = sqlalchemy.create_engine(db)
metadata_obj = MetaData()

Users = Table('users', metadata_obj,
              Column('id', Integer, primary_key=True),
              Column('name', String))


People = Table('people', metadata_obj,
               Column('vk_id'), Integer, primary_key=True)
