from main import bot
from keyboards import KeyboardBuilder
import random


@bot.register_handler("привет")
def hello_handler(bot, event, keyboard: KeyboardBuilder):
    """Обработчик для команды 'привет'"""
    keyboard.add_button("Начать")
    keyboard_markup = keyboard.get_keyboard()

    random_id = random.randint(1, 2 ** 31)

    bot.vk.messages.send(
        user_id=event.user_id,
        message="Привет! Как могу помочь?",
        random_id=random_id,
        keyboard=keyboard_markup
    )


@bot.register_handler("помощь")
def help_handler(bot, event, keyboard: KeyboardBuilder):
    """Обработчик для команды 'помощь'"""
    keyboard.add_button("Помощь")
    keyboard_markup = keyboard.get_keyboard()

    random_id = random.randint(1, 2 ** 31)

    bot.vk.messages.send(
        user_id=event.user_id,
        message="Вот список команд!",
        random_id=random_id,
        keyboard=keyboard_markup
    )