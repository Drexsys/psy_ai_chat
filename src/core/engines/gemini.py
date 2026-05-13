import json
import time
from google import genai
from google.genai import types
from core.models import PsychProfile, ChatResponse
from .AbsEngine import BasePsychAnalyzer

class GeminiPsychAnalyzer(BasePsychAnalyzer):
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-3.1-flash-lite"
        self.history = []
        self.system_instruction = ("""
            Ти — провідний експерт-психометрист. Твоя місія: провести комплексне діагностичне інтерв'ю для формування детального профілю за моделлю Big Five (OCEAN).

            ОСНОВНИЙ ПРОТОКОЛ:
            Оцінювати за шкалою від 0 до 120
            1. ПОВНЕ ОХОПЛЕННЯ: Ти ПОВИНЕН дослідити всі 5 рис: Openness (Відкритість), Conscientiousness (Сумлінність), Extraversion (Екстраверсія), Agreeableness (Привітність), Neuroticism (Нейротизм).
            2. ГЛИБИНА: На кожну рису виділяй від 4 до 5 запитань. Загальна довжина інтерв'ю має складати приблизно 20-25 реплік для досягнення наукової валідності.
            3. ПРІОРИТЕТНІСТЬ: Починай з однієї риси та плавно переходь до іншої. Не перестрибуй хаотично.
            4. МЕТОД КЕЙСІВ: Використовуй розгорнуті ситуативні сценарії. Замість "Ви любите компанії?", запитай: "Уявіть, що ви на конференції, де нікого не знаєте. Як ви проведете першу годину?".
            5. КРОС-ВАЛІДАЦІЯ: Якщо відповідь суперечить попереднім даним, постав контрольне питання для уточнення.
            6. ОБМЕЖЕННЯ: Лише ОДНЕ питання за раз. Ніяких довгих вступів чи самоповторів.
            Твоя відповідь ОБОВ'ЯЗКОВО має бути у форматі JSON.
        """)

    def _get_config(self, response_model):
        """Конфігурація для генерації JSON-відповідей"""
        return types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_model,
            system_instruction=[types.Part.from_text(text=self.system_instruction)],
        )

    def get_response(self, user_input: str) -> str:
        """Метод для підтримки розмови"""
        attems = 0
        while attems < 10:
            try:
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
            except genai.errors.ServerError:
                print('Це може зайняти трохи часу')
                attems += 1
                time.sleep(10)

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
                time.sleep(10)

        print('Сталася помилка. Портрет сформувати не вдалося')
        return None

