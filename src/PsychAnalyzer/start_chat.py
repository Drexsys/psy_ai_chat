import os

from core import engines

def start_char(model):
    analyzer = None
    model_name = ''
    match model:
        case 'g':
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                print("Помилка: Токен не знайдено!")
                return
            analyzer = engines.gemini.GeminiPsychAnalyzer(api_key)
            model_name = 'gemini-3.1-flash-lite'
        case 'o':
            api_key = os.getenv("GITHUB_API_KEY")
            if not api_key:
                print("Помилка: Токен не знайдено!")
                return
            analyzer = engines.openAI.OpenAIAnalyzer(api_key)
            model_name = 'gpt-4o-mini'

    if analyzer is None:
        return

    print("Чат розпочато. Напишіть 'exit' для аналізу.\n")

    while True:
        user_input = input("Ви: ")
        if user_input.lower() == 'exit':
            break

        print(f"\n(Психолог {model_name} аналізує...)")
        try:
            response = analyzer.get_response(user_input)
            print(f"Психолог: {response}\n")
        except Exception as e:
            print(f"Сталася помилка: {e}")

    print("\n--- ГЕНЕРУЄМО ПОРТРЕТ ---")
    profile = analyzer.generate_final_profile()
    if profile is not None:
        print(profile.model_dump_json(indent=2))

    return profile, model_name, analyzer.history
