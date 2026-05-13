import json
from openai import OpenAI
from core.models import PsychProfile, ChatResponse
from .AbsEngine import BasePsychAnalyzer

class OpenAIAnalyzer(BasePsychAnalyzer):
    def __init__(self, api_key: str, model_id="gpt-4o-mini"):
        """
        api_key: ваш токен (OpenAI, GitHub або DeepSeek)
        model_id: назва моделі (напр. "gpt-4o-mini" або "deepseek-chat")
        base_url: URL шлюзу (для GitHub це "https://models.inference.ai.azure.com")
        """
        self.client = OpenAI(api_key=api_key, base_url="https://models.inference.ai.azure.com")
        self.model_id = model_id

        self.system_instruction = (
            "Ти — експерт-психолог. Твоє завдання — скласти портрет користувача за Big Five (OCEAN). "
            "Веди активне інтерв'ю: став уточнюючі питання, моделюй ситуації. "
            "Твоя відповідь ОБОВ'ЯЗКОВО має бути JSON-об'єктом."
        )

        self.history = [{"role": "system", "content": self.system_instruction}]

    def get_response(self, user_input: str) -> str:
        """Метод для підтримки розмови"""
        self.history.append({"role": "user", "content": user_input})

        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=self.history,
                response_format={"type": "json_object"}
            )

            raw_content = response.choices[0].message.content

            data = json.loads(raw_content)
            ai_text = data.get("response", "Вибачте, сталася помилка обробки.")

            self.history.append({"role": "assistant", "content": raw_content})

            return ai_text

        except Exception as e:
            return f"Помилка API: {str(e)}"

    def generate_final_profile(self) -> PsychProfile:
        prompt = (
            "Згенеруй повний JSON портрет особистості PsychProfile. "
            "ОБОВ'ЯЗКОВО включи такі поля: "
            "1. openness, conscientiousness, extraversion, agreeableness, neuroticism (числа 1-100); "
            "2. summary (текстовий висновок); "
            "3. key_quotes (список рядків із цитатами користувача). "
            "ВАЖЛИВО: Поверни ТІЛЬКИ чистий JSON без кореневих ключів типу 'response' чи 'PsychProfile'."
        )

        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=self.history + [{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        raw_data = json.loads(content)

        if len(raw_data) == 1 and isinstance(list(raw_data.values())[0], dict):
            raw_data = list(raw_data.values())[0]

        normalized_data = {}
        for key, value in raw_data.items():
            new_key = key.lower()

            if isinstance(value, dict) and 'score' in value:
                normalized_data[new_key] = value['score']
            else:
                normalized_data[new_key] = value

        if 'key_quotes' not in normalized_data:
            normalized_data['key_quotes'] = []
        if 'summary' not in normalized_data:
            normalized_data['summary'] = "Аналіз завершено."

        try:
            return PsychProfile(**normalized_data)
        except Exception as e:
            print(f"Помилка валідації: {e}")
            print(f"Отримані дані: {normalized_data}")
            return None
