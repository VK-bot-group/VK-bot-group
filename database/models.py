from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database.database import Base

class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    vk_id = Column(Integer, unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    city = Column(String, nullable=True)
    sex = Column(Integer, nullable=True)
    photo_url = Column(String, nullable=True)

    likes = relationship("Like", back_populates="user")
    blacklisted = relationship("BlackList", back_populates="user")

class Like(Base):
    """Модель лайков"""
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    liked_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    mutual = Column(Boolean, default=False)

    user = relationship("User", Foreign_keys=[user_id])
    liked_user = relationship("User", Foreign_keys=[liked_user_id])

class BlackList(Base):
    """Модель чёрного списка"""
    __tablename__ = "blacklist"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    blocked_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", Foreign_keys=[user_id])
    blocked_user = relationship("User", Foreign_keys=[blocked_user_id])
