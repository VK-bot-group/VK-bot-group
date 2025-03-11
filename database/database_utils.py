"""
Модуль для выполнения операций с базами данных через класс DatabaseUtils
"""
from sqlalchemy.orm import Session
from database.database import SessionLocal
from database.database import User, FavoriteUser, BlackList


class DatabaseUtils:
    """ Класс для выполнения операций с таблицами базы данных """
    def __init__(self):
        self.session: Session = SessionLocal()

    def create_user(self, user_id: int, first_name: str, last_name: str,
                    sex: int, city: str,age: int):
        """ Создает нового пользователя в базе данных, если его еще нет. """
        user = self.session.query(User).filter(user_id == User.user_id).first()
        if not user:
            user = User(
                user_id=user_id,
                first_name=first_name,
                last_name=last_name,
                sex=sex,
                city=city,
                age=age
            )
            self.session.add(user)
            self.session.commit()
        return user

    def get_user(self, user_id: int):
        """ Получает пользователя по его ID ВКонтакте из базы данных. """
        return self.session.query(User).filter(user_id == User.user_id).first()

    def add_to_favorites(self, user_id: int, favorite_user_id: int):
        """
        Добавляет пользователя в избранное, если такой пары еще нет в базе данных.
        """
        if not self.session.query(FavoriteUser).filter_by(
            user_id=user_id,
            favorite_user_id=favorite_user_id
        ).first():
            favorite = FavoriteUser(user_id=user_id, favorite_user_id=favorite_user_id)
            self.session.add(favorite)
            self.session.commit()

    def get_favorites(self, user_id: int):
        """ Получает список избранных пользователей. """
        return self.session.query(FavoriteUser).filter(user_id == FavoriteUser.user_id).all()

    def add_to_blacklist(self, user_id: int, blocked_user_id: int):
        """ Добавляет пользователя в черный список. """
        blacklist_entry = BlackList(user_id=user_id, blocked_user_id=blocked_user_id)
        self.session.add(blacklist_entry)
        self.session.commit()
        return blacklist_entry

    def close(self):
        """ Закрывает сессию. """
        self.session.close()
