import vk_api
import os
from vk_api.longpoll import VkLongPoll, VkEventType
from dotenv import load_dotenv


class VKBot:
    def __init__(self):
        load_dotenv()
        TOKEN = os.getenv("TOKEN")
        if not TOKEN:
            raise ValueError("Токен не найден в переменных окружения!")

        self.vk_session = vk_api.VkApi(token=TOKEN)
        self.vk = self.vk_session.get_api()
        self.vk_poll = VkLongPoll(self.vk_session)
        self.handlers = {}

    def register_handler(self, command):
        """Декоратор для регистрации обработчиков."""
        def wrapper(func):
            self.handlers[command] = func
            return func
        return wrapper

    def user_search(self, query="Имя", city=1, sex=1, age_from=18, age_to=60, count=20):
        """Поиск пользователей по фильтру."""
        try:
            response = self.vk.users.search(
                q=query,
                count=count,
                city=city,
                sex=sex,
                age_from=age_from,
                age_to=age_to,
                has_photo=1,
                fields="first_name,last_name,city,sex"
            )
            return response.get("items", [])
        except vk_api.exceptions.ApiError as e:
            print(f"Ошибка API: {e}")
            return []

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


if __name__ == "__main__":
    bot = VKBot()
    bot.run()
