class Person:
    def __init__(self):
        self.first_name= ''
        self.last_name= ''
        self.sex = 0
        self.bdate = None
        self.photo = None
        self.city = 0
    
    def get_info(self,vk_session, person_id):
        
        user_info = vk_session.users.get(user_ids=person_id, fields="first_name, last_name, sex, city, bdate,photo_100")
        self.first_name = user_info[0]["first_name"]
        self.last_name = user_info[0]["last_name"]

        self.sex = user_info[0]["sex"]
        self.bdate = user_info[0]["bdate"]
        self.city = user_info[0]["city"]
        self.photo = user_info[0]["photo_100"]

    def __str__(self):
        return f'{self.first_name} {self.last_name}'
    
    def get_top_photos(vk_session, user_id):
        vk = vk_session.get_api()
        try:
            photos = vk.photos.get(owner_id=user_id, album_id='profile', count=10)
            sorted_photos = sorted(photos.get('items', []), key=lambda x: x.get('likes', {}).get('count', 0), reverse=True)
            return sorted_photos[:3]
        except Exception as e:
            print(f"Ошибка при получении фотографий: {e}")
            return []