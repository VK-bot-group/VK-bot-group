import vk_api

# 🔑 Твой персональный токен
TOKEN_USER = "vk1.a.UoZGyHeRP6IjITBiQXO32cqmxiwLkDFYT3Ux5d6v4GBGlL5qNLm1BO0RjHjDd14UWuCyLv2713kET_Q2DDm-jZg_B5CfB4Hpv_xMl8jpzOj0lLjoSLs0-0B5r7suuNsgK-GzltvIGafY_heuO9gJfZ0Zu_K34KUPbNfZk3gipg5EDD2xi81_ejmEnCipZa0q"

# Авторизация через VK API
vk_session = vk_api.VkApi(token=TOKEN_USER)
vk = vk_session.get_api()

def get_top_3_photos(user_id):
    """Получает 3 фото пользователя с наибольшим числом лайков."""
    try:
        # Запрос всех фото из профиля
        photos = vk.photos.get(owner_id=user_id, album_id="profile", extended=1)['items']

        if not photos:
            return "У пользователя нет фото в профиле."

        # Сортируем фото по количеству лайков (по убыванию)
        top_photos = sorted(photos, key=lambda x: x['likes']['count'], reverse=True)[:3]

        # Получаем ссылки на наибольший размер фото
        top_photo_urls = [max(photo['sizes'], key=lambda s: s['height'] * s['width'])['url'] for photo in top_photos]

        return top_photo_urls

    except Exception as e:
        return f"Ошибка: {e}"

# Тестируем
user_id = 1  # ID пользователя, у которого берем фото
top_photos = get_top_3_photos(user_id)

print("Топ-3 фото пользователя:", top_photos)