from sqlalchemy.orm import Session
from database.database import SessionLocal, init_db
from database.database import User, FavoriteUser, BlackList


class DatabaseUtils:
    def __init__(self):
        self.session: Session = SessionLocal()

    def create_user(self, user_id: int, first_name: str, last_name: str,
                    sex: int, city: str, profile_url: str, age: int):
        """
        Создает нового пользователя в базе данных, если его еще нет.
        """
        user = self.session.query(User).filter(user_id == User.user_id).first()
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
        Получает пользователя по его ID ВКонтакте из базы данных.
        """
        return self.session.query(User).filter(user_id == User.id).first()

    def add_to_favorites(self, user_id: int, favorite_user_id: int):
        """
        Добавляет пользователя в избранное, если такой пары еще нет в базе данных.
        """
        # Проверяем, существует ли уже такая пара в базе данных
        existing_favorite = self.session.query(FavoriteUser).filter_by(
            user_id=user_id,
            favorite_user_id=favorite_user_id
        ).first()

        if not existing_favorite:
            # Если пары нет, создаем новый объект
            favorite = FavoriteUser(user_id=user_id, favorite_user_id=favorite_user_id)
            self.session.add(favorite)
            self.session.commit()

    def get_favorites(self, user_id: int):
        """
        Получает список избранных пользователей.
        """
        return self.session.query(FavoriteUser).filter(user_id == FavoriteUser.user_id).all()

    def add_to_blacklist(self, user_id: int, blocked_user_id: int):
        """
        Добавляет пользователя в черный список.
        """
        blacklist_entry = BlackList(user_id=user_id, blocked_user_id=blocked_user_id)
        self.session.add(blacklist_entry)
        self.session.commit()
        return blacklist_entry

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