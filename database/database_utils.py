from sqlalchemy.orm import Session
from database.database import SessionLocal, init_db
from database.models import User, FavoriteUser, Like, BlackList


class DatabaseUtils:
    def __init__(self):
        self.session: Session = SessionLocal()

    def create_user(self, user_id: int, first_name: str, last_name: str,
                    sex: int, city: str, profile_url: str, age: int):
        """
        Создает нового пользователя в базе данных, если его еще нет.
        """
        user = self.session.query(User).filter(User.user_id == user_id).first()
        if not user:
            user = User(
                user_id=user_id,  # Используем ID пользователя ВКонтакте
                first_name=first_name,
                last_name=last_name,
                sex=sex,
                city=city,
                profile_url=profile_url,
                age=age
            )
            self.session.add(user)
            self.session.commit()
            self.session.refresh(user)
        return user

    def get_user(self, user_id: int):
        """
        Получает пользователя по его ID ВКонтакте.
        """
        return self.session.query(User).filter(User.id == user_id).first()

    def add_to_favorites(self, user_id: int, favorite_user_id: int):
        """
        Добавляет пользователя в избранное.
        """
        favorite = FavoriteUser(user_id=user_id, favorite_user_id=favorite_user_id)
        self.session.add(favorite)
        self.session.commit()
        return favorite

    def get_favorites(self, user_id: int):
        """
        Получает список избранных пользователей.
        """
        return self.session.query(FavoriteUser).filter(FavoriteUser.user_id == user_id).all()

    def remove_from_favorites(self, favorite_id: int):
        """
        Удаляет пользователя из избранного.
        """
        favorite = self.session.query(FavoriteUser).filter(FavoriteUser.id == favorite_id).first()
        if favorite:
            self.session.delete(favorite)
            self.session.commit()
            return True
        return False

    def add_like(self, user_id: int, liked_user_id: int):
        """
        Добавляет лайк пользователю.
        """
        like = Like(user_id=user_id, liked_user_id=liked_user_id)
        self.session.add(like)
        self.session.commit()
        return like

    def get_likes(self, user_id: int):
        """
        Получает список лайков пользователя.
        """
        return self.session.query(Like).filter(Like.user_id == user_id).all()

    def remove_like(self, like_id: int):
        """
        Удаляет лайк.
        """
        like = self.session.query(Like).filter(Like.id == like_id).first()
        if like:
            self.session.delete(like)
            self.session.commit()
            return True
        return False

    def add_to_blacklist(self, user_id: int, blocked_user_id: int):
        """
        Добавляет пользователя в черный список.
        """
        blacklist_entry = BlackList(user_id=user_id, blocked_user_id=blocked_user_id)
        self.session.add(blacklist_entry)
        self.session.commit()
        return blacklist_entry

    def get_blacklist(self, user_id: int):
        """
        Получает список пользователей в черном списке.
        """
        return self.session.query(BlackList).filter(BlackList.user_id == user_id).all()

    def remove_from_blacklist(self, blacklist_id: int):
        """
        Удаляет пользователя из черного списка.
        """
        blacklist_entry = self.session.query(BlackList).filter(BlackList.id == blacklist_id).first()
        if blacklist_entry:
            self.session.delete(blacklist_entry)
            self.session.commit()
            return True
        return False

    def close(self):
        """
        Закрывает сессию.
        """
        self.session.close()

init_db()

# Создание экземпляра DatabaseUtils
db = DatabaseUtils()

# Закрытие сессии
db.close()