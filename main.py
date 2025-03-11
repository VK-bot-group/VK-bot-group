import random
from datetime import datetime
import vk_api
import os
from dotenv import load_dotenv
from vk_api import ApiError
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from database.database import User, BlackList, SessionLocal
from database.database_utils import DatabaseUtils
from typing import List, Dict
from vk_api.keyboard import VkKeyboard, VkKeyboardColor


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
        self.search_offset = 0

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

    def next_handler(self, event):
        """
        Обработчик кнопки "Следующая".
        Увеличивает смещение и выполняет новый поиск.
        """
        user_id = event.object.message["from_id"]
        self.search_offset += 3  # Увеличиваем смещение
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

            # Получаем ID города по его названию
            try:
                city_data = self.vk_u.database.getCities(
                    q=user.city,  # Название города
                    count=1  # Ограничиваем результат одним городом
                )
                if not city_data["items"]:
                    self.vk.messages.send(
                        user_id=user_id,
                        message=f"Город '{user.city}' не найден.",
                        random_id=random.randint(1, 2 ** 31)
                    )
                    return

                city_id = city_data["items"][0]["id"]  # ID города

                # Поиск пользователей
                users = self.vk_u.users.search(
                    age_from=user.age - 4,
                    age_to=user.age + 4,
                    sex=1 if user.sex == 2 else 2,  # Ищем противоположный пол
                    city=city_id,  # Используем ID города
                    has_photo=1,  # Только пользователи с фотографиями
                    count=10,
                    offset=self.search_offset,  # Смещение по списку
                    fields="photo_max_orig,domain,sex,is_closed"  # Добавляем поле is_closed
                )

                # Фильтруем только открытые профили
                open_users = [u for u in users["items"] if not u.get("is_closed", True)]

                # Ищем первого подходящего кандидата
                for candidate in open_users:
                    # Проверяем, нет ли кандидата в черном списке
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

        except Exception as e:
            self.vk.messages.send(
                user_id=user_id,
                message=f"Произошла ошибка: {str(e)}",
                random_id=random.randint(1, 2 ** 31)
            )

        finally:
            session.close()

    def get_top_photos(self, user_id: int, count: int = 3) -> List[str]:
        """
        Получает топовые фотографии пользователя.
        :param user_id: ID пользователя.
        :param count: Количество фотографий.
        :return: Список строк в формате "photo<owner_id>_<photo_id>".
        """
        try:
            # Получаем фотографии пользователя
            photos = self.vk_u.photos.get(
                owner_id=user_id,
                album_id="profile",  # Фотографии из профиля
                extended=1,  # Дополнительные данные (лайки)
                count=100  # Максимальное количество фотографий
            )["items"]

            # Сортируем фотографии по количеству лайков
            photos.sort(key=lambda x: x["likes"]["count"], reverse=True)

            # Формируем список вложений
            attachments = []
            for photo in photos[:count]:
                photo_id = photo["id"]
                owner_id = photo["owner_id"]
                attachments.append(f"photo{owner_id}_{photo_id}")

            return attachments
        except ApiError as e:
            print(f"Ошибка при получении фотографий: {e}")
            return []

    def send_user_info(self, user_id: int, partner: Dict, photos: List[str]) -> None:
        """
        Отправляет информацию о найденном пользователе с фотографией и кнопками.
        :param user_id: ID пользователя, которому отправляется информация.
        :param partner: Информация о найденном пользователе.
        :param photos: Список вложений в формате "photo<owner_id>_<photo_id>".
        """
        # Формируем сообщение
        message = (
            f"Имя: {partner['first_name']} {partner['last_name']}\n"
            f"Ссылка: https://vk.com/{partner['domain']}\n"
        )

        # Создаем клавиатуру с кнопками
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button("Следующая", VkKeyboardColor.PRIMARY)
        keyboard.add_button("В избранное", VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button("В черный список", VkKeyboardColor.NEGATIVE)

        # Отправляем сообщение
        try:
            self.vk.messages.send(
                user_id=user_id,
                message=message,
                attachment=",".join(photos),  # Прикрепляем фотографии
                keyboard=keyboard.get_keyboard(),
                random_id=random.randint(1, 2 ** 31)
            )
        except ApiError as e:
            print(f"Ошибка при отправке сообщения: {e}")

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
