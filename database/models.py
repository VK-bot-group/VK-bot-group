from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    vk_id = Column(Integer, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    sex = Column(Integer)  # 1 — мужской, 2 — женский
    city = Column(String)
    profile_url = Column(String)
    age = Column(Integer)

    # Связь с избранными
    favorites = relationship("FavoriteUser", back_populates="user", foreign_keys="[FavoriteUser.user_id]")

class FavoriteUser(Base):
    __tablename__ = "favorite_users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    favorite_user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", foreign_keys=[user_id], back_populates="favorites")
    favorite_user = relationship("User", foreign_keys=[favorite_user_id])

class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    liked_user_id = Column(Integer, ForeignKey("users.id"))

class BlackList(Base):
    __tablename__ = "blacklist"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    blocked_user_id = Column(Integer, ForeignKey("users.id"))