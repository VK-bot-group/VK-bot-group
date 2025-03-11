"""
Основной модуль включающий класс VKBot,
запускает работу чат-бота
"""
import os
import random
from datetime import datetime
from typing import List, Dict, Optional
import vk_api
from dotenv import load_dotenv
from vk_api import ApiError
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from database.database import User, BlackList, SessionLocal
from database.database_utils import DatabaseUtils


class VKBot:
    """Класс для взаимодействия
    с пользователем чат-бота вконтакте и локальной базой данных.
    """
    def __init__(self):
        load_dotenv()
        self.vk_session = vk_api.VkApi(token=os.getenv("TOKEN_BOT"))
        self.vk_poll = VkBotLongPoll(self.vk_session, os.getenv("GROUP_ID"))
        self.vk_user = vk_api.VkApi(token=os.getenv("TOKEN_USER"))
        self.vk_u = self.vk_user.get_api()
        self.vk = self.vk_session.get_api()
        self.db = DatabaseUtils()
        self.handlers = {
            "начать": self.start_handler,
            "помощь": self.help_handler,
            "я": self.user_info_handler,
            "найти пару": self.find_partner_handler,
            "избранные": self.favorites_handler,
            "следующая": self.next_handler,
            "в избранное": self.add_to_favorites_handler,
            "в черный список": self.add_to_blacklist_handler,
        }
        self.current_candidate = None
        self.search_offset = 0

    @staticmethod
    def get_keyboard():
        """ Создает клавиатуру для бота. """
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button("Найти пару", VkKeyboardColor.POSITIVE)
        keyboard.add_button("Помощь", VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button("Избранные", VkKeyboardColor.PRIMARY)
        return keyboard.get_keyboard()

    @staticmethod
    def _calculate_age(bdate: str) -> int:
        """ Рассчитывает возраст по дате рождения. """
        if bdate and len(bdate.split(".")) == 3:
            birth_year = int(bdate.split(".")[2])
            current_year = datetime.now().year
            return current_year - birth_year
        return 25  # Значение по умолчанию, если дата рождения недоступна

    def send_message(self, user_id: int, message: str, keyboard=None, attachments=None):
        """Метод для отправки сообщений пользователю"""
        try:
            self.vk.messages.send(
                user_id=user_id,
                message=message,
                random_id=random.randint(1, 2 ** 31),
                keyboard=keyboard,
                attachment=attachments
            )
        except ApiError as e:
            print(f"Ошибка при отправке сообщения: {e}")

    def register_handler(self, command):
        """Декоратор для регистрации обработчиков."""
        def wrapper(func):
            self.handlers[command] = func
            return func
        return wrapper

    def handle_message(self, event):
        """ Обработчик сообщений пользователя. Запускает доступные команды. """
        text = event.object.message["text"].lower()
        if text in self.handlers:
            self.handlers[text](self, event)
        else:
            print(f"Неизвестная команда: {text}")

    def start_handler(self, event):
        """
        Обработчик команды "начать".
        Сохраняет пользователя в базу данных и отправляет приветственное сообщение.
        """
        user_id = event.object.message["from_id"]
        random_id = random.randint(1, 2 ** 31)
        try:
            user_info = self.vk_u.users.get(user_ids=user_id,
                                            fields="first_name, last_name, sex, city, bdate")[0]
            # Сохраняем пользователя в базу данных
            self.db.create_user(
                user_id=user_id,  # Используем ID пользователя ВКонтакте
                first_name=user_info["first_name"],
                last_name=user_info["last_name"],
                sex=user_info.get("sex", 0),
                city=user_info.get("city", {}).get("title", "Неизвестно"),
                age=self._calculate_age(user_info.get("bdate", ""))
            )
            self.send_message(user_id,
                              "Привет! Я бот для знакомств в VK!", keyboard=self.get_keyboard())
        except ApiError as e:
            print(f"Ошибка при получении данных пользователя: {e}")
            self.vk.messages.send(
                user_id=user_id,
                message="Не удалось получить ваши данные. Проверьте настройки приватности.",
                random_id=random_id)

    def help_handler(self, event):
        """ Обработчик команды "помощь". Отправляет список доступных команд. """
        random_id = random.randint(1, 2 ** 31)
        command_str = ", ".join(self.handlers.keys())
        self.vk.messages.send(
            user_id=event.object.message["from_id"],
            message=f"Список команд:\n{command_str}",
            random_id=random_id,
            keyboard=self.get_keyboard())

    def user_info_handler(self, event):
        """ Обработчик команды "я". Отправляет информацию о пользователе. """
        user_id = event.object.message["from_id"]
        user = self.db.get_user(user_id)
        if user:
            message = (
                f"Имя: {user.first_name} {user.last_name}\n"
                f"Пол: {'Мужской' if user.sex == 2 else 'Женский'}\n"
                f"Город: {user.city}\n"
                f"Возраст: {user.age}"
            )
        else:
            message = "Ваши данные не найдены в базе данных."
        self.send_message(user_id, message, keyboard=self.get_keyboard())

    def next_handler(self, event):
        """
        Обработчик кнопки "Следующая".
        Увеличивает смещение и выполняет новый поиск.
        """
        self.search_offset += 3
        self.find_partner_handler(event)

    def add_to_favorites_handler(self, event):
        """Обработчик кнопки 'В избранное', Добавляем кандидата в избранное"""
        user_id = event.object.message["from_id"]
        if self.current_candidate:
            self.db.add_to_favorites(user_id=user_id, favorite_user_id=self.current_candidate["id"])
            self.vk.messages.send(
                user_id=user_id,
                message="Пользователь добавлен в избранное!",
                random_id=random.randint(1, 2 ** 31))
        else:
            self.vk.messages.send(
                user_id=user_id,
                message="Ошибка: кандидат не найден.",
                random_id=random.randint(1, 2 ** 31))

    def add_to_blacklist_handler(self, event):
        """Обработчик кнопки 'В черный список'"""
        user_id = event.object.message["from_id"]
        if self.current_candidate:
            self.db.add_to_blacklist(user_id=user_id, blocked_user_id=self.current_candidate["id"])
            self.vk.messages.send(
                user_id=user_id,
                message="Пользователь добавлен в черный список!",
                random_id=random.randint(1, 2 ** 31))
        else:
            self.vk.messages.send(
                user_id=user_id,
                message="Ошибка: кандидат не найден.",
                random_id=random.randint(1, 2 ** 31))

    def favorites_handler(self, event):
        """Обработчик команды 'избранные' Отправляет пользователю список избранных"""
        user_id = event.object.message["from_id"]
        favorites = self.db.get_favorites(user_id)
        if favorites:
            message = "Ваши избранные:\n"
            for favorite in favorites:
                partner_info = self.vk_u.users.get(user_ids=favorite.favorite_user_id,
                                                   fields="first_name,last_name,domain")
                message += (f"{partner_info[0]['first_name']} {partner_info[0]['last_name']} "
                            f"(https://vk.com/{partner_info[0]['domain']})\n")
        else:
            message = "Ваш список избранных пуст."
        self.vk.messages.send(
            user_id=user_id,
            message=message,
            random_id=random.randint(1, 2 ** 31),
            keyboard=self.get_keyboard())

    def find_partner_handler(self, event):
        """Метод для поиска пары по критериям пользователя"""
        user_id = event.object.message["from_id"]
        session = SessionLocal()
        try:
            # Получаем информацию о пользователе из базы данных
            user = session.query(User).filter_by(user_id=user_id).first()
            if not user:
                self.send_message(user_id,
                    "Не удалось получить ваши данные. Добавьте информацию о себе.")
                return
            # Получаем ID города по его названию
            city_id = self.get_city_id(user.city)
            if not city_id:
                self.send_message(user_id, f"Город '{user.city}' не найден.")
                return
            # Поиск пользователей
            users = self.vk_u.users.search(
                age_from=user.age - 4,
                age_to=user.age + 4,
                sex=1 if user.sex == 2 else 2,  # Ищем противоположный пол
                city=city_id,  # Используем ID города
                has_photo=1,  # Только пользователи с фотографиями
                count=100,
                offset=self.search_offset,  # Смещение по списку
                fields="photo_max_orig,domain,sex,is_closed"  # Добавляем поле is_closed
            )
            # Фильтруем только открытые профили
            open_users = [u for u in users["items"] if not u.get("is_closed", True)]
            # Ищем первого подходящего кандидата
            for candidate in open_users:
                in_blacklist = session.query(BlackList).filter_by(
                    user_id=user_id,
                    blocked_user_id=candidate["id"]
                ).first()
                if not in_blacklist:
                    self.current_candidate = candidate  # Сохраняем текущего кандидата
                    top_photos = self.get_top_photos(self.current_candidate["id"])
                    if top_photos:  # Если фотографии доступны
                        self.send_user_info(user_id, self.current_candidate, top_photos)
                        return
            # Если подходящие кандидаты не найдены
            self.send_message(user_id, "Извините, подходящих кандидатов не найдено.")
        except ApiError as e:
            self.send_message(user_id, f"Ошибка при поиске пары: {e}")
        finally:
            session.close()

    def get_top_photos(self, user_id: int, count: int = 3) -> List[str]:
        """Находим самые популярные фото кандидата"""
        try:
            photos = self.vk_u.photos.get(
                owner_id=user_id,
                album_id="profile",
                extended=1,
                count=100
            )["items"]
            photos.sort(key=lambda x: x["likes"]["count"], reverse=True)
            return [f"photo{photo['owner_id']}_{photo['id']}" for photo in photos[:count]]
        except ApiError as e:
            print(f"Ошибка при получении фотографий: {e}")
            return []

    def send_user_info(self, user_id: int, partner: Dict, photos: List[str]) -> None:
        """Отправляем инфо о кандидате + фото, и выводим кнопки для продолжения"""
        message = (
            f"Имя: {partner['first_name']} {partner['last_name']}\n"
            f"Ссылка: https://vk.com/{partner['domain']}\n"
        )
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button("Следующая", VkKeyboardColor.PRIMARY)
        keyboard.add_button("В избранное", VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button("В черный список", VkKeyboardColor.NEGATIVE)
        self.send_message(user_id, message,
                          keyboard=keyboard.get_keyboard(),
                          attachments=",".join(photos))

    def get_city_id(self, city_name: str) -> Optional[int]:
        """ Получает ID города по его названию с помощью API VK. """
        try:
            city_data = self.vk_u.database.getCities(
                q=city_name,  # Название города
                count=1  # Ограничиваем результат одним городом
            )
            if city_data["items"]:
                return city_data["items"][0]["id"]  # Возвращаем ID города
            return None  # Если город не найден
        except ApiError as e:
            print(f"Ошибка при получении ID города: {e}")
            return None

    def run(self):
        """ Запуск бота"""
        print("Bot is Running")
        try:
            for event in self.vk_poll.listen():
                if event.type == VkBotEventType.MESSAGE_NEW:
                    text = event.object.message["text"].lower()
                    if text in self.handlers:
                        self.handlers[text](event)
        finally:
            self.db.close()  # Закрываем сессию при завершении работы бота


if __name__ == "__main__":
    bot = VKBot()
    bot.run()
