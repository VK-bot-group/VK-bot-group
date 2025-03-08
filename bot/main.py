import os
import random
import logging
from dotenv import load_dotenv
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from database.database import SessionLocal
from database.models import FavoriteUser

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()
token_bot = os.getenv("TOKEN_BOT")
token_user = os.getenv("TOKEN_USER")
group_id = os.getenv("GROUP_ID")

if not token_bot or not token_user or not group_id:
    raise ValueError("Один из токенов или Group ID не найден в переменных окружения!")

class VKApiService:
    def __init__(self, token_bot, token_user, group_id):
        self.vk_session = vk_api.VkApi(token=token_bot)
        self.vk = self.vk_session.get_api()
        self.vk_poll = VkBotLongPoll(self.vk_session, group_id)
        self.vk_user = vk_api.VkApi(token=token_user)
        self.vk_u = self.vk_user.get_api()

    def send_message(self, user_id, message, keyboard=None):
        try:
            self.vk.messages.send(
                user_id=user_id,
                message=message,
                random_id=random.randint(1, 2 ** 31),
                keyboard=keyboard
            )
        except vk_api.exceptions.ApiError as e:
            logger.error(f"Ошибка при отправке сообщения: {e}")
            self.send_message(user_id, "Произошла ошибка при отправке сообщения. Попробуйте позже.")

    def get_user_info(self, user_id):
        try:
            return self.vk_u.users.get(user_ids=user_id, fields="first_name,last_name,sex,city")[0]
        except vk_api.exceptions.ApiError as e:
            logger.error(f"Ошибка при получении данных: {e}")
            return None

    def get_city_id(self, city_name):
        try:
            response = self.vk_u.database.getCities(q=city_name)
            if response["count"] > 0:
                return response["items"][0]["id"]
            else:
                return None
        except vk_api.exceptions.ApiError as e:
            logger.error(f"Ошибка при получении ID города: {e}")
            return None

    def search_users(self, age, gender, city_name):
        city_id = self.get_city_id(city_name)
        if not city_id:
            logger.error(f"Город '{city_name}' не найден.")
            return []

        try:
            response = self.vk_u.users.search(
                sex=gender,
                age_from=age,
                age_to=age,
                city=city_id,
                fields="photo_max,first_name,last_name,city",
                count=5
            )
            return response["items"]
        except vk_api.exceptions.ApiError as e:
            logger.error(f"Ошибка при поиске пользователей: {e}")
            return []

    def get_top_photos(self, user_id):
        try:
            photos = self.vk_u.photos.get(owner_id=user_id, album_id='profile', count=10)
            sorted_photos = sorted(photos.get('items', []), key=lambda x: x.get('likes', {}).get('count', 0),
                                   reverse=True)
            return sorted_photos[:3]
        except Exception as e:
            logger.error(f"Ошибка при получении фотографий: {e}")
            return []


class VKBot:
    def __init__(self, vk_api_service, session):
        self.vk_api_service = vk_api_service
        self.session = session
        self.handlers = {
            "начать": self.start_handler,
            "помощь": self.help_handler,
            "me": self.user_info_handler,
            "найти пару": self.find_partner_handler,
            "избранные": self.favorites_handler,
        }

    @staticmethod
    def get_keyboard():
        from vk_api.keyboard import VkKeyboard, VkKeyboardColor
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button("Найти пару", VkKeyboardColor.POSITIVE)
        keyboard.add_button("Помощь", VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button("Избранные", VkKeyboardColor.PRIMARY)
        return keyboard.get_keyboard()

    @staticmethod
    def get_inline_keyboard():
        from vk_api.keyboard import VkKeyboard, VkKeyboardColor
        keyboard = VkKeyboard(inline=True)
        keyboard.add_button("Лайк", color=VkKeyboardColor.POSITIVE, payload={"action": "like"})
        keyboard.add_button("Дизлайк", color=VkKeyboardColor.NEGATIVE, payload={"action": "dislike"})
        return keyboard.get_keyboard()

    def start_handler(self, event):
        user_id = event.object.message["from_id"]
        self.vk_api_service.send_message(user_id, "Привет! Я бот для знакомств в VK!")

    def help_handler(self, event):
        user_id = event.object.message["from_id"]
        command_str = "\n".join(self.handlers.keys())
        self.vk_api_service.send_message(user_id, f"Список команд:\n{command_str}")

    def user_info_handler(self, event):
        user_id = event.object.message["from_id"]
        user_info = self.vk_api_service.get_user_info(user_id)
        if user_info:
            sex = "Мужской" if user_info["sex"] == 2 else "Женский"
            message = f"Имя: {user_info['first_name']} {user_info['last_name']}\nПол: {sex}"
        else:
            message = "Не удалось получить информацию о пользователе."
        self.vk_api_service.send_message(user_id, message)

    def find_partner_handler(self, event):
        user_id = event.object.message["from_id"]
        user_info = self.vk_api_service.get_user_info(user_id)
        if user_info:
            opposite_sex = 1 if user_info["sex"] == 2 else 2
            city = user_info.get("city", {}).get("title", "Москва")

            candidates = self.vk_api_service.search_users(age=25, gender=opposite_sex, city_name=city)

            if candidates:
                partner = candidates[0]
                message = (f"Имя: {partner['first_name']} "
                           f"{partner['last_name']}\n"
                           f"Возраст: {partner.get('bdate', 'Не указан')} \n"
                           f"Город: {partner.get('city', {}).get('title', 'Не указан')}")

                photos = self.vk_api_service.get_top_photos(partner['id'])
                self.vk_api_service.send_message(user_id, message, self.get_inline_keyboard())
                self.send_user_info(user_id, partner, photos)
            else:
                self.vk_api_service.send_message(user_id, "Извините, подходящих кандидатов не найдено.")
        else:
            self.vk_api_service.send_message(user_id, "Ошибка при поиске пары.")

    def favorites_handler(self, event):
        user_id = event.object.message["from_id"]
        self.send_favorites(user_id)

    def send_user_info(self, user_id, user_info, photos):
        attachment = ','.join([f"photo{photo['owner_id']}_{photo['id']}" for photo in photos]) if photos else ''
        message = f"Имя: {user_info['first_name']} {user_info['last_name']}\nСсылка: https://vk.com/id{user_info['id']}"
        if not photos:
            message += "\nУ этого пользователя нет фотографий."

        # Отправляем данные, включая ссылку и фотографии, только после того, как лайкнули
        try:
            self.vk_api_service.vk.messages.send(
                user_id=user_id, message=message, attachment=attachment,
                random_id=random.randint(1, 1_000_000)
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке информации: {e}")

    def send_favorites(self, user_id):
        favorites = self.session.query(FavoriteUser).filter(FavoriteUser.user_id == user_id).all()
        message = "Избранные:\n" + '\n'.join([f"{f.favorite_user.first_name} {f.favorite_user.last_name}: "
                                              f"https://vk.com/id{f.favorite_user.id}" for f in favorites])
        self.vk_api_service.send_message(user_id, message or "У вас нет избранных.")


    def handle_inline_buttons(self, event):
        action = event.object.payload["action"]
        user_id = event.object.message["from_id"]

        if action == "like":
            self.vk_api_service.send_message(user_id, "Вы поставили лайк! Сейчас покажем фотографии.")
            # После лайка, показываем фотографии
            partner_info = self.get_partner_info(user_id)  # Нужно добавить логику получения информации о партнере
            photos = self.vk_api_service.get_top_photos(partner_info['id'])
            self.send_user_info(user_id, partner_info, photos)
        elif action == "dislike":
            self.vk_api_service.send_message(user_id, "Вы поставили дизлайк. Ищем нового кандидата.")
            self.find_partner_handler(event)  # Пытаемся найти нового кандидата

    def run(self):
        print("Bot is Running")
        for event in self.vk_api_service.vk_poll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                command = event.object.message["text"].lower()
                if command in self.handlers:
                    self.handlers[command](event)
            elif event.type == VkBotEventType.MESSAGE_EVENT:
                self.handle_inline_buttons(event)


if __name__ == "__main__":
    vk_api_service = VKApiService(token_bot, token_user, group_id)
    session = SessionLocal()
    bot = VKBot(vk_api_service, session)
    bot.run()