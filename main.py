import random
from datetime import datetime
import vk_api
import os
from vk_api.longpoll import VkLongPoll, VkEventType
from dotenv import load_dotenv
from vk_api import ApiError
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from database.database import SessionLocal, init_db
from bot.utils import search_users, get_top_photos, create_keyboard, send_user_info, send_favorites
from database.models import FavoriteUser, User, BlackList
from database.database_utils import DatabaseUtils


class VKBot:
    def __init__(self):
        load_dotenv()
        token_bot = os.getenv("TOKEN_BOT")
        group_id = os.getenv("GROUP_ID")
        token_user = os.getenv("TOKEN_USER")
        if not token_bot or not token_user:
            raise ValueError("Токен не найден в переменных окружения!")

        self.vk_session = vk_api.VkApi(token=token_bot)
        self.vk = self.vk_session.get_api()
        self.vk_poll = VkBotLongPoll(self.vk_session, group_id)

        self.vk_user = vk_api.VkApi(token=token_user)
        self.vk_u = self.vk_user.get_api()

        # Инициализация DatabaseUtils
        self.db = DatabaseUtils()

        # Регистрация команд
        self.handlers = {
            "начать": self.start_handler,
            "помощь": self.help_handler,
            "я": self.user_info_handler,  # Отправляет сообщение
            "найти пару": self.find_partner_handler,
            "избранные": self.favorites_handler,
            "следующая": self.next_handler,
            "в избранное": self.add_to_favorites_handler,
            "в черный список": self.add_to_blacklist_handler,
        }

        # Текущий кандидат
        self.current_candidate = None

        # Смещение для поиска чтобы не попадались одинаковые часто
        self.search_offset = 50

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

    def start_handler(self, event):
        """
        Обработчик команды "начать".
        Сохраняет пользователя в базу данных и отправляет приветственное сообщение.
        """
        user_id = event.object.message["from_id"]
        random_id = random.randint(1, 2 ** 31)

        try:
            # Получаем информацию о пользователе
            user_info = self.vk_u.users.get(user_ids=user_id, fields="first_name, last_name, sex, city, bdate")[0]

            # Сохраняем пользователя в базу данных
            self.db.create_user(
                user_id=user_id,  # Используем ID пользователя ВКонтакте
                first_name=user_info["first_name"],
                last_name=user_info["last_name"],
                sex=user_info.get("sex", 0),
                city=user_info.get("city", {}).get("title", "Неизвестно"),
                profile_url=f"https://vk.com/id{user_id}",
                age=self._calculate_age(user_info.get("bdate", ""))
            )

            # Отправляем приветственное сообщение
            self.vk.messages.send(
                user_id=user_id,
                message="Привет! Я бот для знакомств в VK!",
                random_id=random_id,
                keyboard=self.get_keyboard()
            )
        except ApiError as e:
            print(f"Ошибка при получении данных пользователя: {e}")
            self.vk.messages.send(
                user_id=user_id,
                message="Не удалось получить ваши данные. Проверьте настройки приватности.",
                random_id=random_id
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

    def user_info_handler(self, event):
        """
        Обработчик команды "я".
        Отправляет информацию о текущем пользователе из базы данных.
        """
        user_id = event.object.message["from_id"]
        session = SessionLocal()

        try:
            # Получаем информацию о пользователе из базы данных
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                # Формируем сообщение
                message = (
                    f"Имя: {user.first_name} {user.last_name}\n"
                    f"Пол: {'Мужской' if user.sex == 2 else 'Женский'}\n"
                    f"Город: {user.city}\n"
                    f"Возраст: {user.age}"
                )
            else:
                message = "Ваши данные не найдены в базе данных."

            # Отправляем сообщение
            self.vk.messages.send(
                user_id=user_id,
                message=message,
                random_id=random.randint(1, 2 ** 31),
                keyboard=self.get_keyboard()
            )
        except Exception as e:
            print(f"Ошибка при получении данных пользователя: {e}")
            self.vk.messages.send(
                user_id=user_id,
                message="Ошибка при получении ваших данных.",
                random_id=random.randint(1, 2 ** 31)
            )
        finally:
            session.close()

    def _get_user_info(self, event):
        """
        Внутренний метод для получения информации о пользователе.
        """
        user_id = event.object.message["from_id"]
        try:
            # Получаем информацию о пользователе
            user_info = self.vk_u.users.get(user_ids=user_id, fields="first_name, last_name, sex, bdate, city")
            return user_info[0]  # Возвращаем данные пользователя
        except vk_api.exceptions.ApiError as e:
            print(f"Ошибка при получении данных пользователя: {e}")
            return None

    def next_handler(self, event):
        """
        Обработчик кнопки "Следующая".
        Увеличивает смещение и выполняет новый поиск.
        """
        user_id = event.object.message["from_id"]
        self.search_offset += 50  # Увеличиваем смещение
        self.find_partner_handler(event)

    def add_to_favorites_handler(self, event):
        """Обработчик кнопки 'В избранное'"""
        user_id = event.object.message["from_id"]
        if self.current_candidate:
            # Добавляем кандидата в избранное
            self.db.add_to_favorites(user_id=user_id, favorite_user_id=self.current_candidate["id"])
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
            # Добавляем кандидата в черный список
            self.db.add_to_blacklist(user_id=user_id, blocked_user_id=self.current_candidate["id"])
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

    def favorites_handler(self, event):
        """Обработчик команды 'избранные'"""
        user_id = event.object.message["from_id"]
        try:
            # Получаем список избранных из базы данных
            favorites = self.db.get_favorites(user_id)
            if favorites:
                message = "Ваши избранные:\n"
                for favorite in favorites:
                    partner_info = self.vk_u.users.get(user_ids=favorite.favorite_user_id,
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

    def find_partner_handler(self, event):
        user_id = event.object.message["from_id"]
        session = SessionLocal()
        try:
            # Получаем информацию о пользователе из базы данных
            user = session.query(User).filter_by(user_id=user_id).first()
            if not user:
                self.vk.messages.send(
                    user_id=user_id,
                    message="Не удалось получить ваши данные. Добавьте информацию о себе.",
                    random_id=random.randint(1, 2 ** 31)
                )
                return

            age = user.age
            sex = user.sex
            opposite_sex = 1 if sex == 2 else 2  # Ищем противоположный пол
            city = user.city

            # Поиск кандидатов с использованием данных пользователя
            candidates = search_users(self.vk_u, age=age, gender=opposite_sex, city_name=city,
                                      offset=self.search_offset)

            if candidates:
                # Ищем первого открытого кандидата, проверяя черный список
                for candidate in candidates:
                    if not candidate.get("is_closed", True):
                        # Проверяем, нет ли кандидата в черном списке
                        in_blacklist = session.query(BlackList).filter_by(
                            user_id=user_id,
                            blocked_user_id=candidate["id"]
                        ).first()

                        if not in_blacklist:
                            self.current_candidate = candidate  # Сохраняем текущего кандидата
                            top_photos = get_top_photos(self.vk_u, self.current_candidate["id"])
                            if top_photos:  # Если фотографии доступны
                                send_user_info(self.vk_session, user_id, self.current_candidate, top_photos)
                                break  # Прерываем цикл после первого подходящего кандидата
                else:
                    # Если все кандидаты закрыты или в черном списке
                    self.vk.messages.send(
                        user_id=user_id,
                        message="Извините, подходящих кандидатов не найдено.",
                        random_id=random.randint(1, 2 ** 31)
                    )
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
        finally:
            session.close()

    def run(self):
        print("Bot is Running")
        try:
            for event in self.vk_poll.listen():
                if event.type == VkBotEventType.MESSAGE_NEW:
                    text = event.object.message["text"].lower()
                    if text in self.handlers:
                        self.handlers[text](event)
        finally:
            self.db.close()  # Закрываем сессию при завершении работы бота

    def _calculate_age(self, bdate: str) -> int:
        """
        Рассчитывает возраст по дате рождения.
        """
        if bdate and len(bdate.split(".")) == 3:
            birth_year = int(bdate.split(".")[2])
            current_year = datetime.now().year
            return current_year - birth_year
        return 25  # Значение по умолчанию, если дата рождения недоступна

if __name__ == "__main__":
    bot = VKBot()
    bot.run()
