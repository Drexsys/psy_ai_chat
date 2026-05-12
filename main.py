from dotenv import load_dotenv
from PsychAnalyzer.gemini import start_char
from src.db import DB_connection
from src.services.user import User

load_dotenv()

db = DB_connection()

def menu():
    while True:
        print('Увійти [l], Створити користувача [c], вийти [e]')
        choice = input().strip().lower()

        match choice:
            case 'l':
                user = User.login(db)
                if user is not None:
                    return user
                print('Такого користувача не має. Спробуйте ще раз.\n')

            case 'c':
                user = User.create(db)
                if user is not None:
                    return user
                print('Username має бути унікальним. Спробуйте ще раз.\n')

            case 'e':
                return None

            case _:
                print('Невідома команда. Будь ласка, оберіть l, c або e.\n')

def choose_llm(user):
    while True:
        print('Виберіть модель для спілкування: Gemini [g]')
        choice = input().strip().lower()

        match choice:
            case 'g':
                return start_char()

            case _:
                print('Невідома команда.\n')

    return None

def main():
    user = menu()
    if user is None:
        return

    profile, model_name = choose_llm(user)
    if profile is None:
        return

    db.add_res_f_llm(profile, model_name, user.id)

if __name__ == "__main__":
    main()

db.close()
