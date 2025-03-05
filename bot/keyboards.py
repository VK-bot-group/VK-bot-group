from vk_api.keyboard import VkKeyboard, VkKeyboardColor


class KeyboardBuilder:
    """Метод создания клавиатуры."""

    def __init__(self):
        self.keyboard = VkKeyboard(one_time=True)

    def add_button(self, label, color=VkKeyboardColor.PRIMARY):
        self.keyboard.add_button(label, color)

    def add_line(self):
        self.keyboard.add_line()

    def get_keyboard(self):
        return self.keyboard.get_keyboard()
