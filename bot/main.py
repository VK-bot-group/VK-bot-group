import os
import random
from dotenv import load_dotenv
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from database.database import SessionLocal
from utils import search_users, get_top_photos, create_keyboard, send_user_info, send_favorites


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

        # Регистрация команд
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

    def start_handler(self, event):
        user_id = event.object.message["from_id"]
        random_id = random.randint(1, 2 ** 31)
        self.vk.messages.send(
            user_id=user_id,
            message="Привет! Я бот для знакомств в VK!",
            random_id=random_id,
            keyboard=self.get_keyboard()
        )

    def help_handler(self, event):
        random_id = random.randint(1, 2 ** 31)
        command_str = ", ".join(self.handlers.keys())
        self.vk.messages.send(
            user_id=event.object.message["from_id"],
            message=f"Список команд:\n{command_str}",
            random_id=random_id,
            keyboard=self.get_keyboard()
        )

    def user_info_handler(self, event):
        """Обработчик команды 'me' - информация о пользователе"""
        user_id = event.object.message["from_id"]
        user_info = self.vk_u.users.get(user_ids=user_id, fields="first_name, last_name, sex")
        sex = user_info[0]["sex"]
        message = f"Имя: {user_info[0]['first_name']} {user_info[0]['last_name']}\n"
        message += f"Пол: {'Мужской' if sex == 2 else 'Женский'}"

        random_id = random.randint(1, 2 ** 31)
        self.vk.messages.send(
            user_id=user_id,
            message=message,
            random_id=random_id,
            keyboard=self.get_keyboard()
        )

    def find_partner_handler(self, event):
        user_id = event.object.message["from_id"]
        session = SessionLocal()

        # Получаем информацию о текущем пользователе
        user_info = self.vk_u.users.get(user_ids=user_id, fields="first_name, last_name, sex")
        sex = user_info[0]["sex"]

        # Определяем противоположный пол
        opposite_sex = 1 if sex == 2 else 2

        # Поиск кандидатов
        candidates = search_users(self.vk_session, age=25, gender=opposite_sex, city="Москва")

        if candidates:
            partner = candidates[0]
            top_photos = get_top_photos(self.vk_session, partner["id"])
            send_user_info(self.vk_session, user_id, partner, top_photos)
            self.vk.messages.send(
                user_id=user_id,
                message="Потенциальный партнёр найден!",
                random_id=random.randint(1, 2 ** 31),
                keyboard=create_keyboard()
            )

        session.close()

    def favorites_handler(self, event):
        """Обработчик команды 'Избранные'"""
        user_id = event.object.message["from_id"]
        session = SessionLocal()
        send_favorites(self.vk_session, user_id, session)
        session.close()

    def run(self):
        print("Bot is Running")
        for event in self.vk_poll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                if event.object.message["text"].lower() in self.handlers:
                    self.handlers[event.object.message["text"].lower()](event)


if __name__ == "__main__":
    bot = VKBot()
    bot.run()