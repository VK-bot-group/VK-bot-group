from main import bot
from keyboards import KeyboardBuilder
import random


@bot.register_handler("Начать")
def hello_handler(bot, event):
    """Обработчик для команды 'привет'"""
    keyboard = KeyboardBuilder()
    keyboard.add_button("Начать")
    keyboard_markup = keyboard.get_keyboard()

    random_id = random.randint(1, 2 ** 31)

    bot.vk.messages.send(
        user_id=event.user_id,
        message="Привет! Как могу помочь?",
        random_id=random_id,
        keyboard=keyboard_markup
    )


@bot.register_handler("Помощь")
def help_handler(bot, event):
    """Обработчик для команды 'помощь'"""
    keyboard = KeyboardBuilder()
    keyboard.add_button("Помощь")
    keyboard_markup = keyboard.get_keyboard()

    random_id = random.randint(1, 2 ** 31)

    bot.vk.messages.send(
        user_id=event.user_id,
        message="Вот список команд!",
        random_id=random_id,
        keyboard=keyboard_markup
    )
