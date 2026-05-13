import json
import time
from google import genai
from google.genai import types
from core.models import PsychProfile, ChatResponse
from .AbsEngine import BasePsychAnalyzer

class GeminiPsychAnalyzer(BasePsychAnalyzer):
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        # Використовуємо модель, яка була у вашому списку
        self.model_id = "gemini-3.1-flash-lite"
        self.history = []
        self.system_instruction = (
            "Ти професійний психолог. Твоє завдання — вести діалог з користувачем, "
            "щоб скласти його портрет за методологією Big Five (OCEAN). "
            "Будь емпатичним, став уточнюючі питання."
        )

    def _get_config(self, response_model):
        """Конфігурація для генерації JSON-відповідей"""
        return types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_model,
            system_instruction=[types.Part.from_text(text=self.system_instruction)],
        )

    def get_response(self, user_input: str) -> str:
        """Метод для підтримки розмови"""
        self.history.append(types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_input)]
        ))

        response = self.client.models.generate_content(
            model=self.model_id,
            contents=self.history,
            config=self._get_config(ChatResponse)
        )

        data = json.loads(response.text)
        ai_text = data.get("response", "")

        self.history.append(types.Content(
            role="model",
            parts=[types.Part.from_text(text=ai_text)]
        ))

        return ai_text

    # ЦЕЙ МЕТОД МАЄ БУТИ ВСЕРЕДИНІ КЛАСУ
    def generate_final_profile(self):
        attems = 0
        while attems < 10:
            try:
                """Аналізує історію чату та повертає структурований JSON портрет"""
                prompt = "На основі нашого діалогу сформуй повний психологічний портрет за схемою JSON."

                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=self.history + [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
                    config=self._get_config(PsychProfile)
                )

                return PsychProfile(**json.loads(response.text))
            except genai.errors.ServerError:
                print('Це може зайняти трохи часу')
                attems += 1
                time.sleep(1)

        print('Сталася помилка. Портрет сформувати не вдалося')
        return None
