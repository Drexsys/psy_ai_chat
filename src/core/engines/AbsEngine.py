from abc import ABC, abstractmethod
from core.models import PsychProfile

class BasePsychAnalyzer(ABC):
    @abstractmethod
    def get_response(self, user_input: str) -> str:
        """Метод для підтримки діалогу"""
        pass

    @abstractmethod
    def generate_final_profile(self) -> PsychProfile:
        """Метод для генерації фінального JSON-портрета"""
        pass