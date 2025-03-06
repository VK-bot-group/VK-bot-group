import vk_api
import os
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

from dotenv import load_dotenv
import random


class VKBot:
    def __init__(self):
        load_dotenv()
        # Токен бота.
        token_bot = os.getenv("TOKEN_BOT")
        group_id = os.getenv("GROUP_ID")
        # Персональный токен ВК.
        token_user = os.getenv("TOKEN_USER")
        if not token_bot or not token_user:
            raise ValueError("Токен не найден в переменных окружения!")

        # Авторизация через токен бота.
        self.vk_session = vk_api.VkApi(token=token_bot)
        self.vk = self.vk_session.get_api()
        self.vk_poll = VkBotLongPoll(self.vk_session, group_id)
        self.handlers = {
            'help': self.help_handler,
            'me': self.user_info_handler
        }

        # Авторизация через персональный токен.
        self.vk_user = vk_api.VkApi(token=token_user)
        self.vk_u = self.vk_user.get_api()

    def help_handler(self, event):
        """Обработчик для команды 'помощь'"""

        random_id = random.randint(1, 2 ** 31)

        command_str = ", ".join([key for key, val in self.handlers.items()])

        self.vk.messages.send(
            user_id=event.object.message['from_id'],
            message=f"Cписок команд:\n{command_str}",
            random_id=random_id
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

    def get_photos(self, event):
        """Получение трех фото с наибольшими лайками. Список из 3 url."""
        user_id = event.object.message['from_id']
        photos = self.vk.photos.get(owner_id=user_id, album_id="profile", extended=1)['items']
        if not photos:
            return "Фото в профиле отсутствуют"

        top_photos = sorted(photos, key=lambda x: x['likes']['count'], reverse=True)[:3]
        top_photo_urls = [max(photo['sizes'], key=lambda s: s['height'] * s['width'])['url'] for photo in top_photos]

        return top_photo_urls

    def user_info_handler(self, event):
        user_id = event.object.message['from_id']
        user_info = self.vk_u.users.get(user_ids=user_id, fields="first_name, last_name, photo_100, bdate")

        random_id = random.randint(1, 2 ** 31)

        first_name = user_info[0]['first_name']
        last_name = user_info[0]['last_name']
        photo_url = user_info[0]['photo_100']
        bdate = user_info[0].get('bdate', 'Не указана')

        top_photos = self.get_photos(event)

        photos_message = "\n".join(top_photos) if isinstance(top_photos, list) else top_photos

        self.vk.messages.send(
            user_id=user_id,
            message=f"Информация о вас: {first_name} {last_name}\n"
                    f"Ссылка на фото: {photos_message}\n"
                    f"Дата рождения: {bdate}",
            random_id=random_id
        )

    def start_handler(self, event):
        user_id = event.object.message['from_id']
        user_info = self.vk_u.users.get(user_ids=user_id)
        random_id = random.randint(1, 2 ** 31)

        self.vk.message.send(
            user_id=user_id,
            message=f"Привет! Я бот для знакомств в VK!",
            random_id=random_id
        )

    def next_handler(self):
        pass

    def save(self):
        pass

    def handle_message(self, event):
        text = event.object.message['text']
        print(text)
        if text in self.handlers:
            self.handlers[text](event)
        else:
            self.unknown_handler(event)
            print(f"Неизвестная команда: {text}")

    def run(self):
        print("Bot is Running")
        try:
            for event in self.vk_poll.listen():
                if event.type == VkBotEventType.MESSAGE_NEW:
                    self.handle_message(event)
        except Exception as e:
            print(f"Произошла ошибка: {e}")


if __name__ == "__main__":
    bot = VKBot()
    bot.run()
