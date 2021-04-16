from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()


class DbConnector(object):
    engine = None
    session = None

    def __init__(self):
        self.engine = create_engine('sqlite:///bot.db', echo=True)
        session = sessionmaker(bind=self.engine)
        self.session = session()
        User.categories = relationship('Category', order_by=Category.id, back_populates='user')
        User.keywords = relationship('Keyword', order_by=Keyword.id, back_populates='user')
        Base.metadata.create_all(self.engine)

    def __del__(self):
        self.session.close()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer)
    name = Column(String)

    def __init__(self, tg_id, name):
        self.name = name
        self.telegram_id = tg_id


class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    news_api_id = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', back_populates='categories')

    def __init__(self, name: str, news_api_id, user: User):
        self.name = name
        self.news_api_id = news_api_id
        self.user = user


class Keyword(Base):
    __tablename__ = 'keywords'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', back_populates='keywords')

    def __init__(self, name: str, user: User):
        self.name = name
        self.user = user
