import random

import vk_api
import os
from vk_api.longpoll import VkLongPoll, VkEventType
from dotenv import load_dotenv
from vk_api import ApiError
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from database.database import SessionLocal, init_db
from bot.utils import search_users, get_top_photos, create_keyboard, send_user_info, send_favorites


class VKBot:
    def __init__(self):
        load_dotenv()
        token = os.getenv("TOKEN")
        if not token:
            raise ValueError("Токен не найден в переменных окружения!")

        self.vk_session = vk_api.VkApi(token)
        self.vk = self.vk_session.get_api()
        self.vk_poll = VkLongPoll(self.vk_session)
        self.handlers = {}

    def register_handler(self, command):
        """Декоратор для регистрации обработчиков."""
        def wrapper(func):
            self.handlers[command] = func
            return func
        return wrapper


    def handle_message(self, event):
        text = event.text.lower()
        if text in self.handlers:
            self.handlers[text](self, event)
        else:
            print(f"Неизвестная команда: {text}")

    def run(self):
        try:
            for event in self.vk_poll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    self.handle_message(event)
        except Exception as e:
            print(f"Произошла ошибка: {e}")


        # Регистрация команд
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

        # Текущий кандидат
        self.current_candidate = None

        # Смещение для поиска
        self.search_offset = 0

    def start_handler(self, event):
        """
        Обработчик команды "начать".
        Отправляет приветственное сообщение и клавиатуру.
        """
        user_id = event.object.message["from_id"]
        random_id = random.randint(1, 2 ** 31)
        self.vk.messages.send(
            user_id=user_id,
            message="Привет! Я бот для знакомств в VK!",
            random_id=random_id,
            keyboard=self.get_keyboard()
        )

    def get_keyboard(self):
        """
        Создает клавиатуру для бота.
        """
        from vk_api.keyboard import VkKeyboard, VkKeyboardColor
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button("Найти пару", VkKeyboardColor.POSITIVE)
        keyboard.add_button("Помощь", VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button("Избранные", VkKeyboardColor.PRIMARY)
        return keyboard.get_keyboard()

    def help_handler(self, event):
        """
        Обработчик команды "помощь".
        Отправляет список доступных команд.
        """
        random_id = random.randint(1, 2 ** 31)
        command_str = ", ".join(self.handlers.keys())
        self.vk.messages.send(
            user_id=event.object.message["from_id"],
            message=f"Список команд:\n{command_str}",
            random_id=random_id,
            keyboard=self.get_keyboard()
        )

    def favorites_handler(self, event):
        """
        Обработчик команды "избранные".
        Отправляет список избранных пользователей.
        """
        user_id = event.object.message["from_id"]
        session = SessionLocal()

        try:
            # Получаем список избранных из базы данных
            favorites = session.query(Favorite).filter(Favorite.user_id == user_id).all()
            if favorites:
                message = "Ваши избранные:\n"
                for favorite in favorites:
                    partner_info = self.vk_u.users.get(user_ids=favorite.partner_id,
                                                       fields="first_name,last_name,domain")
                    message += f"{partner_info[0]['first_name']} {partner_info[0]['last_name']} (https://vk.com/{partner_info[0]['domain']})\n"
            else:
                message = "Ваш список избранных пуст."

            # Отправляем сообщение
            self.vk.messages.send(
                user_id=user_id,
                message=message,
                random_id=random.randint(1, 2 ** 31),
                keyboard=self.get_keyboard()
            )
        except Exception as e:
            print(f"Ошибка при получении избранных: {e}")
            self.vk.messages.send(
                user_id=user_id,
                message="Ошибка при получении списка избранных.",
                random_id=random.randint(1, 2 ** 31)
            )
        finally:
            session.close()

    def user_info_handler(self, event):
        """
        Обработчик команды "me".
        Отправляет информацию о текущем пользователе.
        """
        user_id = event.object.message["from_id"]
        try:
            # Получаем информацию о пользователе
            user_info = self.vk_u.users.get(user_ids=user_id, fields="first_name, last_name, sex")
            sex = user_info[0]["sex"]
            message = f"Имя: {user_info[0]['first_name']} {user_info[0]['last_name']}\n"
            message += f"Пол: {'Мужской' if sex == 2 else 'Женский'}"
        except vk_api.exceptions.ApiError as e:
            message = f"Ошибка при получении данных: {e}"

        # Отправляем сообщение
        random_id = random.randint(1, 2 ** 31)
        self.vk.messages.send(
            user_id=user_id,
            message=message,
            random_id=random_id,
            keyboard=self.get_keyboard()
        )

    # Остальные методы класса VKBot...

    def next_handler(self, event):
        """
        Обработчик кнопки "Следующая".
        Увеличивает смещение и выполняет новый поиск.
        """
        user_id = event.object.message["from_id"]
        self.search_offset += 1  # Увеличиваем смещение
        self.find_partner_handler(event)

    def add_to_favorites_handler(self, event):
        """Обработчик кнопки 'В избранное'"""
        user_id = event.object.message["from_id"]
        if self.current_candidate:
            # Добавляем пользователя в избранное (заглушка)
            print(f"Пользователь {self.current_candidate['id']} добавлен в избранное.")
            self.vk.messages.send(
                user_id=user_id,
                message="Пользователь добавлен в избранное!",
                random_id=random.randint(1, 2 ** 31)
            )
        else:
            self.vk.messages.send(
                user_id=user_id,
                message="Ошибка: кандидат не найден.",
                random_id=random.randint(1, 2 ** 31)
            )

    def add_to_blacklist_handler(self, event):
        """Обработчик кнопки 'В черный список'"""
        user_id = event.object.message["from_id"]
        if self.current_candidate:
            # Добавляем пользователя в черный список (заглушка)
            print(f"Пользователь {self.current_candidate['id']} добавлен в черный список.")
            self.vk.messages.send(
                user_id=user_id,
                message="Пользователь добавлен в черный список!",
                random_id=random.randint(1, 2 ** 31)
            )
        else:
            self.vk.messages.send(
                user_id=user_id,
                message="Ошибка: кандидат не найден.",
                random_id=random.randint(1, 2 ** 31)
            )

    def find_partner_handler(self, event):
        user_id = event.object.message["from_id"]
        session = SessionLocal()

        try:
            # Получаем информацию о текущем пользователе
            user_info = self.vk_u.users.get(user_ids=user_id, fields="first_name, last_name, sex")
            sex = user_info[0]["sex"]

            # Определяем противоположный пол
            opposite_sex = 1 if sex == 2 else 2

            # Поиск кандидатов с использованием смещения
            candidates = search_users(self.vk_u, age=25, gender=opposite_sex, city_name="Москва",
                                      offset=self.search_offset)

            if candidates:
                self.current_candidate = candidates[0]  # Сохраняем текущего кандидата
                top_photos = get_top_photos(self.vk_u, self.current_candidate["id"])
                send_user_info(self.vk_session, user_id, self.current_candidate, top_photos)
            else:
                self.vk.messages.send(
                    user_id=user_id,
                    message="Извините, подходящих кандидатов не найдено.",
                    random_id=random.randint(1, 2 ** 31)
                )
        except ApiError as e:
            self.vk.messages.send(
                user_id=user_id,
                message=f"Ошибка при поиске пары: {e}",
                random_id=random.randint(1, 2 ** 31)
            )

        session.close()

    def run(self):
        print("Bot is Running")
        for event in self.vk_poll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                text = event.object.message["text"].lower()
                if text in self.handlers:
                    self.handlers[text](event)


if __name__ == "__main__":
    bot = VKBot()
    bot.run()
