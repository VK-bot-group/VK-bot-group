import random

def help_handler(event,vk_object):
        """Обработчик для команды 'помощь'"""
        
        random_id = random.randint(1, 2 ** 31)

        command_str = ", ".join([key for key,val in self.handlers.items()])


        vk_object.messages.send(
            user_id=event.object.message['from_id'],
            message=f"Cписок команд:\n{command_str}",
            random_id=random_id
        )

def unknown_handler(event, vk_object, vk_session):
    """Обработчик для неизвестных слов"""
    
    random_id = random.randint(1, 2 ** 31)
    text = event.object.message['text']
    vk_object.messages.send(
        user_id=event.object.message['from_id'],
        message=f"Вы набрали {text}, но я не знаю эту команду",
        random_id=random_id
    )

def user_info_handler(event):
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

