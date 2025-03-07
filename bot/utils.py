import random
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from database.models import FavoriteUser


def search_users(vk_session, age, gender, city):
    """Поиск пользователей ВКонтакте по фильтрам: возраст, пол, город"""
    vk = vk_session.get_api()
    try:
        # Получаем ID города
        city_id = None
        if city:
            city_response = vk.database.getCities(q=city)
            if city_response['items']:
                city_id = city_response['items'][0]['id']

        response = vk.users.search(
            age_from=age,
            age_to=age,
            sex=gender,
            city=city_id,
            count=10,
            has_photo=1,
            fields="first_name,last_name,city,photo_max"
        )
        return response['items'] if 'items' in response else []
    except Exception as e:
        print(f"Ошибка при поиске пользователей: {e}")
        return []

def get_top_photos(vk_session, user_id):
    vk = vk_session.get_api()
    try:
        photos = vk.photos.get(owner_id=user_id, album_id='profile', count=10)
        sorted_photos = sorted(photos.get('items', []), key=lambda x: x.get('likes', {}).get('count', 0), reverse=True)
        return sorted_photos[:3]
    except Exception as e:
        print(f"Ошибка при получении фотографий: {e}")
        return []

def create_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Next', color=VkKeyboardColor.PRIMARY)
    return keyboard.get_keyboard()

def send_user_info(vk_session, user_id, user_info, photos):
    vk = vk_session.get_api()
    attachment = ','.join([f"photo{photo['owner_id']}_{photo['id']}" for photo in photos]) if photos else ''
    message = f"Имя: {user_info['first_name']} {user_info['last_name']}\nСсылка: https://vk.com/id{user_info['id']}"
    if not photos:
        message += "\nУ этого пользователя нет фотографий."
    try:
        vk.messages.send(user_id=user_id, message=message, attachment=attachment, random_id=random.randint(1, 1_000_000))
    except Exception as e:
        print(f"Ошибка при отправке информации: {e}")

def send_favorites(vk_session, user_id, db):
    favorites = db.query(FavoriteUser).filter(FavoriteUser.user_id == user_id).all()
    message = "Избранные:\n" + '\n'.join([f"{f.favorite_user.first_name} {f.favorite_user.last_name}: "
                                          f"https://vk.com/id{f.favorite_user.id}" for f in favorites])
    vk_session.get_api().messages.send(user_id=user_id, message=message or "У вас нет избранных.",
                                       random_id=random.randint(1, 1_000_000))
