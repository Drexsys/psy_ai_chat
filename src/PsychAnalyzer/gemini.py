import os
from core.engine import PsychAnalyzer

def start_char():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Помилка: Токен не знайдено!")
        return

    analyzer = PsychAnalyzer(api_key)
    print("Чат розпочато. Напишіть 'exit' для аналізу.\n")

    while True:
        user_input = input("Ви: ")
        if user_input.lower() == 'exit':
            break

        # Отримуємо відповідь (ШІ буде «думати» завдяки Thinking High)
        print("\n(Психолог аналізує...)")
        try:
            response = analyzer.get_response(user_input)
            print(f"Психолог: {response}\n")
        except Exception as e:
            print(f"Сталася помилка: {e}")

    print("\n--- ГЕНЕРУЄМО ПОРТРЕТ ---")
    profile = analyzer.generate_final_profile()
    print(profile.model_dump_json(indent=2))

    return profile, 'gemini-3.1-flash-lite'
