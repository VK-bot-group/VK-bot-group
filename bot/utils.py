import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.exceptions import ApiError
from database.database import SessionLocal
from typing import List, Dict, Optional
import random

def search_users(vk_api_user, age: int, gender: int, city_name: str, count: int = 10, offset: int = 0) -> List[Dict]:
    """
    Поиск пользователей по заданным параметрам.
    Возвращает только открытые профили.
    :param vk_api_user: API для выполнения запросов от имени пользователя.
    :param age: Возраст для поиска.
    :param gender: Пол (1 — женский, 2 — мужской).
    :param city_name: Название города для поиска.
    :param count: Количество пользователей для поиска.
    :param offset: Смещение по списку пользователей.
    :return: Список найденных пользователей.
    """
    try:
        # Получаем ID города по его названию
        city_data = vk_api_user.database.getCities(
            q=city_name,  # Название города
            count=1  # Ограничиваем результат одним городом
        )
        if not city_data["items"]:
            print(f"Город '{city_name}' не найден.")
            return []

        city_id = city_data["items"][0]["id"]  # ID города

        # Поиск пользователей
        users = vk_api_user.users.search(
            age_from=age - 4,
            age_to=age + 4,
            sex=gender,
            city=city_id,  # Используем ID города
            has_photo=1,  # Только пользователи с фотографиями
            count=count,
            offset=offset,  # Смещение по списку
            fields="photo_max_orig,domain,sex,is_closed"  # Добавляем поле is_closed
        )

        # Фильтруем только открытые профили
        open_users = [user for user in users["items"] if not user.get("is_closed", True)]
        return open_users
    except ApiError as e:
        print(f"Ошибка при поиске пользователей: {e}")
        return []

def get_top_photos(vk_api_user, user_id: int, count: int = 3) -> List[str]:
    """
    Получает топовые фотографии пользователя.
    :param vk_api_user: API для выполнения запросов от имени пользователя.
    :param user_id: ID пользователя.
    :param count: Количество фотографий.
    :return: Список строк в формате "photo<owner_id>_<photo_id>".
    """
    try:
        # Получаем фотографии пользователя
        photos = vk_api_user.photos.get(
            owner_id=user_id,
            album_id="profile",  # Фотографии из профиля
            extended=1,          # Дополнительные данные (лайки)
            count=100            # Максимальное количество фотографий
        )["items"]

        # Сортируем фотографии по количеству лайков
        photos.sort(key=lambda x: x["likes"]["count"], reverse=True)

        # Формируем список вложений
        attachments = []
        for photo in photos[:count]:
            photo_id = photo["id"]
            owner_id = photo["owner_id"]
            attachments.append(f"photo{owner_id}_{photo_id}")

        return attachments
    except ApiError as e:
        print(f"Ошибка при получении фотографий: {e}")
        return []

def create_keyboard() -> dict:
    """
    Создает клавиатуру для бота.
    :return: Словарь с клавиатурой.
    """
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("Найти пару", VkKeyboardColor.POSITIVE)
    keyboard.add_button("Помощь", VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("Избранные", VkKeyboardColor.PRIMARY)
    return keyboard.get_keyboard()

def send_user_info(vk_session, user_id: int, partner: Dict, photos: List[str]) -> None:
    """
    Отправляет информацию о найденном пользователе с фотографией и кнопками.
    :param vk_session: Сессия VK API для отправки сообщений.
    :param user_id: ID пользователя, которому отправляется информация.
    :param partner: Информация о найденном пользователе.
    :param photos: Список вложений в формате "photo<owner_id>_<photo_id>".
    """
    vk = vk_session.get_api()

    # Формируем сообщение
    message = (
        f"Имя: {partner['first_name']} {partner['last_name']}\n"
        f"Ссылка: https://vk.com/{partner['domain']}\n"
    )

    # Создаем клавиатуру с кнопками
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("Следующая", VkKeyboardColor.PRIMARY)
    keyboard.add_button("В избранное", VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button("В черный список", VkKeyboardColor.NEGATIVE)

    # Отправляем сообщение
    try:
        vk.messages.send(
            user_id=user_id,
            message=message,
            attachment=",".join(photos),  # Прикрепляем фотографии
            keyboard=keyboard.get_keyboard(),
            random_id=random.randint(1, 2 ** 31)
        )
    except ApiError as e:
        print(f"Ошибка при отправке сообщения: {e}")

def send_favorites(vk_session, user_id: int, session) -> None:
    """
    Отправляет список избранных пользователей.
    :param vk_session: Сессия VK API для отправки сообщений.
    :param user_id: ID пользователя, которому отправляется информация.
    :param session: Сессия базы данных.
    """
    vk = vk_session.get_api()

    # Здесь должен быть код для получения избранных из базы данных
    # Например:
    # favorites = session.query(Favorite).filter(Favorite.user_id == user_id).all()
    # for favorite in favorites:
    #     partner_info = vk.users.get(user_ids=favorite.partner_id, fields="first_name,last_name,domain")
    #     message = f"Избранный: {partner_info[0]['first_name']} {partner_info[0]['last_name']}\nСсылка: https://vk.com/{partner_info[0]['domain']}"
    #     vk.messages.send(user_id=user_id, message=message, random_id=random.randint(1, 2 ** 31))

    # Заглушка для примера
    message = "Список избранных пуст."
    try:
        vk.messages.send(
            user_id=user_id,
            message=message,
            random_id=random.randint(1, 2 ** 31))
    except ApiError as e:
        print(f"Ошибка при отправке сообщения: {e}")
