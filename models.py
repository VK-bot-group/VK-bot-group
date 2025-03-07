import sqlite3
class User:

    def __init__(self, user_id, first_name, last_name, city=None, age=None):
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.city = city
        self.age = age

        # Подключение к базе данных (или создание, если её нет)
        self.conn = sqlite3.connect('vk_bot.db')
        self.cursor = self.conn.cursor()

        # Создание таблицы для хранения пользователей
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            city TEXT,
            age INTEGER
        )
        ''')
        self.conn.commit()

    def save_to_db(self):
        """Сохраняет пользователя в базу данных."""
        try:
            self.cursor.execute('''
            INSERT INTO users (user_id, first_name, last_name, city, age)
            VALUES (?, ?, ?, ?, ?)
            ''', (self.user_id, self.first_name, self.last_name, self.city, self.age))
            self.conn.commit()
            
        except sqlite3.IntegrityError:
            print(f"Пользователь с ID {self.user_id} уже существует в базе данных.")

    
    def is_user_in_db(self,user_id):
        """Проверяет, есть ли пользователь в базе данных."""
        self.cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        return self.cursor.fetchone() is not None

    def __str__(self):
        return f"{self.first_name} {self.last_name} (ID: {self.user_id}, Город: {self.city}, Возраст: {self.age})"