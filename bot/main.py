import vk_api
import os
from vk_api.longpoll import VkLongPoll, VkEventType
from dotenv import load_dotenv


class VKBot:
    def __init__(self):
        load_dotenv()
        token = os.getenv("TOKEN")
        self.vk_session = vk_api.VkApi(token)
        self.vk = self.vk_session.get_api()
        self.vk_poll = VkLongPoll(self.vk_session)
        #self.handler = "Взять из файла handlers"

    def run(self):
        for event in self.vk_poll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                user_id = event.user_id
                message = event.text
                #self.handler.handle_message(user_id, message, self.vk)


if __name__ == "__main__":
    bot = VKBot()
    bot.run()
