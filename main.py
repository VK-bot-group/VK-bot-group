import vk_api
import os
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

from dotenv import load_dotenv
from handlers import Handlers
import random
from models import Person


class VkSearch:
#Класс логики поиска
    def __init__(self, vk_user_api):
        self.vk_user_api = vk_user_api

    def search_users(self, city_id, age_from, age_to, count=10):
        """Поиск пользователей по городу и возрасту."""
        response = self.vk_user_api.users.search(
            city=city_id,
            age_from=age_from,
            age_to=age_to,
            count=count,
            fields='city,photo_200'
        )
        return response['items']

class VKBot:
#Класс логики бота

    def __init__(self):
        load_dotenv()
        group_token = os.getenv("TOKEN_GROUP")
        group_id = os.getenv("GROUP_ID")
        user_token = os.getenv("TOKEN_USER")

        if not group_token or not user_token:
            raise ValueError("Токен не найден в переменных окружения!")

        # Сессия и API для работы от имени группы
        self.vk_group_session = vk_api.VkApi(token=group_token)
        self.vk_group_api = self.vk_group_session.get_api()

        # LongPoll для получения событий от группы
        self.vk_group_longpoll = VkBotLongPoll(self.vk_group_session, group_id)

        # Сессия и API для работы от имени пользователя
        self.vk_user_session = vk_api.VkApi(token=user_token)
        self.vk_user_api = self.vk_user_session.get_api()

        self.handlers = {
            "start": Handlers.handle_start,
            "search": Handlers.handle_search,
            "help": Handlers.handle_help,
        }
        
    def find_users(self, city_id, age_from, age_to):
        """Поиск пользователей и отправка результатов."""
        users = VkSearch.search_users(city_id, age_from, age_to)
        for user in users:
            print(f"Найден пользователь: {user['first_name']} {user['last_name']}")

    def handle_message(self, event):
        message_text = event.message['text'].lower()
        user_id = event.message['from_id']

        for command, handler in self.handlers.items():
            if message_text.startswith(command):
                handler(self, user_id, message_text)  # Передаем self (бот) в обработчик
                return
    
        self.send_message(user_id, 'Неизвестная команда. Наберите help для вывода всех команд')

    def send_message(self, user_id, message):
        
        random_id = random.randint(1, 2 ** 31)
        self.vk_group_api.messages.send(
            user_id=user_id,
            message=message,
            random_id=random_id
        )

    def run(self):

        for event in self.vk_group_longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                self.handle_message(event)


if __name__ == "__main__":
    bot = VKBot()
    bot.run()
