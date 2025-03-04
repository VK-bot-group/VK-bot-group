from keyboards import KeyboardBuilder
from abc import ABC, abstractmethod

class BotHandler(ABC):
    @abstractmethod
    def handler(self):
        pass

