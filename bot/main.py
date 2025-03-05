import vk_api
import os
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

from dotenv import load_dotenv
import random

class VKBot:
    
    def help_handler(self, event):
        """Обработчик для команды 'помощь'"""
        
        random_id = random.randint(1, 2 ** 31)

        command_str = ", ".join([key for key,val in self.handlers.items()])


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
    
    def user_info_handler(self,event):
        user_id=event.object.message['from_id']
        user_info = self.vk.users.get(user_ids=user_id, fields='first_name,last_name,photo_100,bdate')
        
        random_id = random.randint(1, 2 ** 31)
        
        first_name = user_info[0]['first_name']
        last_name = user_info[0]['last_name']
        photo_url = user_info[0]['photo_100']
        bdate = user_info[0]['bdate']

        self.vk.messages.send(
            user_id=event.object.message['from_id'],
            message=f"Информация о вас: {first_name} {last_name}\nСсылка на фото: {photo_url}\nДата рождения:{bdate}",
            random_id=random_id
        )



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
                        'help':self.help_handler,
                        'me':self.user_info_handler

                        }
        
   
    def handle_message(self, event):
        text = event.object.message['text']
        print(text)
        if text in self.handlers:
            self.handlers[text]( event)
        else:
            self.unknown_handler(event)
            print(f"Неизвестная команда: {text}")

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
