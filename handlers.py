class Handlers:
    @staticmethod
    def handle_start(bot, user_id, message):
        bot.send_message(user_id, "Привет! Я бот. Введите /help для списка команд.")

    @staticmethod
    def handle_search(bot, user_id, message):
        bot.send_message(user_id, "Введите город и возраст для поиска (например, Москва 25).")

    @staticmethod
    def handle_help(bot, user_id, message):
        help_text = """
        Доступные команды:
        start - Начать работу с ботом
        search - Поиск пользователей
        help - Список команд
        """
        bot.send_message(user_id, help_text)