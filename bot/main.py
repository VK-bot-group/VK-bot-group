import os
import random
from dotenv import load_dotenv
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
#from database.database import SessionLocal, init_db
#from utils import search_users, get_top_photos, create_keyboard, send_user_info, send_favorites


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
            "me": self.user_info_handler
    
        }

    @staticmethod
    def get_keyboard():
        from vk_api.keyboard import VkKeyboard, VkKeyboardColor
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button("Найти пару", VkKeyboardColor.POSITIVE)
        keyboard.add_button("   ", VkKeyboardColor.PRIMARY)
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
        try:
            user_info = self.vk_u.users.get(user_ids=user_id, fields="first_name, last_name, sex")
            sex = user_info[0]["sex"]
            message = f"Имя: {user_info[0]['first_name']} {user_info[0]['last_name']}\n"
            message += f"Пол: {'Мужской' if sex == 2 else 'Женский'}"
        except vk_api.exceptions.ApiError as e:
            message = f"Ошибка при получении данных: {e}"

        random_id = random.randint(1, 2 ** 31)
        self.vk.messages.send(
            user_id=user_id,
            message=message,
            random_id=random_id,
            keyboard=self.get_keyboard()
        )
    
    def unknown_handler(self, event):
        """Обработчик для неизвестных слов"""
        
        random_id = random.randint(1, 2 ** 31)
        text = event.object.message['text']
        self.vk.messages.send(
            user_id=event.object.message['from_id'],
            message=f"Вы набрали {text}, но я не знаю эту команду",
            random_id=random_id
        )

    def run(self):
        print("Bot is Running")
        for event in self.vk_poll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                if event.object.message["text"].lower() in self.handlers:
                    self.handlers[event.object.message["text"].lower()](event)
                else:
                    self.unknown_handler(event)

if __name__ == "__main__":
#    init_db()
    bot = VKBot()
    bot.run()