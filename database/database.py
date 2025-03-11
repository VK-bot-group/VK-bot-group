from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv
from sqlalchemy import Column, Integer, String, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import relationship

load_dotenv()

DATABASE_URL = os.getenv("DATABASE")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    Base.metadata.create_all(bind=engine)

class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True)  # ID пользователя ВКонтакте
    first_name = Column(String)
    last_name = Column(String)
    sex = Column(Integer)  # 1 — женский, 2 — мужской
    city = Column(String)
    profile_url = Column(String)
    age = Column(Integer)
    # Связь с избранными
    favorites = relationship("FavoriteUser", back_populates="user")


class FavoriteUser(Base):
    __tablename__ = "favorite_users"
    # Составной первичный ключ
    __table_args__ = (PrimaryKeyConstraint('user_id', 'favorite_user_id'),)
    user_id = Column(Integer, ForeignKey("users.user_id"))  # ID пользователя, который добавил в избранное
    favorite_user_id = Column(Integer)  # ID пользователя, добавленного в избранное
    user = relationship("User", foreign_keys=user_id, back_populates="favorites")


class BlackList(Base):
    __tablename__ = "blacklist"
    # Составной первичный ключ
    __table_args__ = (PrimaryKeyConstraint('user_id', 'blocked_user_id'),)
    user_id = Column(Integer, ForeignKey("users.user_id"))  # ID пользователя, который добавил в черный список
    blocked_user_id = Column(Integer)  # ID пользователя, добавленного в черный список