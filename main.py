import vk_api
import os
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

from dotenv import load_dotenv
from handlers import help_handler, unknown_handler
from models import Person

class VKBot:
        
    def __init__(self):
        load_dotenv()
        token = os.getenv("TOKEN")
        group_id = os.getenv("GROUP_ID")
        if not token:
            raise ValueError("Токен не найден в переменных окружения!")

        self.vk_session = vk_api.VkApi(token=token)
        self.vk = self.vk_session.get_api()
        self.vk_poll = VkBotLongPoll(self.vk_session, group_id)
        self.handlers = {
                        'help':help_handler
                        }
        
   
    def handle_message(self, event):

        self.current_person = Person()
        self.current_person.get_info(self.vk_poll,event.message['from_id'])
        print(Person)
        text = event.object.message['text']
        if text in self.handlers:
            self.handlers[text]( event)
        else:
            unknown_handler(event)
            

    def run(self):
        try:
            for event in self.vk_poll.listen():
                if event.type == VkBotEventType.MESSAGE_NEW:
                    self.handle_message(event)
        except Exception as e:
            print(f"Произошла ошибка: {e}")


if __name__ == "__main__":
    bot = VKBot()
    bot.run()
