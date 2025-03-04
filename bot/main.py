import vk_api
import os
from vk_api.longpoll import VkLongPoll, VkEventType
from dotenv import load_dotenv


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


if __name__ == "__main__":
    bot = VKBot()
    bot.run()
