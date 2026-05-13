import psycopg2

class DB_connection:
    def __init__(self):
        self.connect = psycopg2.connect(
            host='localhost',
            port='5433',
            dbname='psy_ai_chat',
            user='postgres',
            password='password'
        )
        self.cursor = self.connect.cursor()

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT NOT NULL UNIQUE
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS models (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL UNIQUE
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS res (
                id SERIAL PRIMARY KEY,
                openness INT NOT NULL,
                conscientiousness INT NOT NULL,
                extraversion INT NOT NULL,
                agreeableness INT NOT NULL,
                neuroticism INT NOT NULL
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS chats_res (
                id SERIAL PRIMARY KEY,
                user_id INT REFERENCES users(id) ON DELETE CASCADE,
                model_id INT REFERENCES models(id) ON DELETE CASCADE,
                res_id INT REFERENCES res(id) ON DELETE CASCADE,
                summary TEXT NOT NULL
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id SERIAL PRIMARY KEY,
                chats_res_id INT REFERENCES chats_res ON DELETE CASCADE,
                answer TEXT NOT NULL,
                role TEXT NOT NULL
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS true_res (
                id SERIAL PRIMARY KEY,
                user_id INT REFERENCES users(id) ON DELETE CASCADE,
                res_id INT REFERENCES res(id) ON DELETE CASCADE
            );
        """)

        self.connect.commit()

        self.cursor.execute("SELECT COUNT(*) FROM models;")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute("""
                INSERT INTO models (name)
                VALUES ('gemini-3.1-flash-lite'),
                        ('gpt-4o-mini');
            """)

            self.connect.commit()

    def close(self):
        self.cursor.close()
        self.connect.close()

    def create_user(self, username):
        try:
            self.cursor.execute("""
                INSERT INTO users (username)
                    VALUES (%s)
                RETURNING id;
            """, (username,))
            self.connect.commit()

            return self.cursor.fetchone()[0]
        except psycopg2.errors.UniqueViolation:
            self.connect.rollback()
            return None

    def find_user(self, username):
        self.cursor.execute("""
            SELECT id FROM users
            WHERE username = %s;
        """, (username,))
        id = self.cursor.fetchone()

        if id is None:
            return None
        return id[0]

    def add_res_f_llm(self, res, model_name, user_id):
        self.cursor.execute("""
            INSERT INTO res (
                openness, conscientiousness, extraversion, agreeableness, neuroticism)
                VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
        """, (res.openness, res.conscientiousness, res.extraversion, res.agreeableness, res.neuroticism))
        res_id = self.cursor.fetchone()[0]

        self.cursor.execute("""
            SELECT id FROM models
            WHERE name = %s;
        """, (model_name,))
        model_id = self.cursor.fetchone()[0]

        self.cursor.execute("""
            INSERT INTO chats_res (
                user_id, model_id, res_id, summary)
                Values (%s, %s, %s, %s)
            RETURNING id;
        """, (user_id, model_id, res_id, res.summary))

        self.connect.commit()

        return self.cursor.fetchone()[0]

    def add_conversation(self, history, res_id):
        """Зберігає історію повідомлень, незалежно від формату (Gemini або OpenAI)"""
        for entry in history:
            # 1. Визначаємо роль (user/model/assistant/system)
            if hasattr(entry, 'role'):
                role = entry.role # Формат Gemini
            else:
                role = entry.get('role') # Формат OpenAI

            # 2. Визначаємо контент (текст повідомлення)
            if hasattr(entry, 'parts'):
                # Формат Gemini: збираємо текст із частин
                content = "".join([p.text for p in entry.parts if p.text])
            else:
                # Формат OpenAI/GitHub: беремо значення за ключем 'content'
                content = entry.get('content', '')

            # Якщо повідомлення пусте (наприклад, технічний JSON), ігноруємо або чистимо
            if not content:
                continue

            # 3. Записуємо в базу
            try:
                self.cursor.execute(
                    "INSERT INTO conversations (chats_res_id, answer, role) VALUES (%s, %s, %s);",
                    (res_id, role, content)
                )
            except Exception as e:
                print(f"Помилка запису повідомлення в БД: {e}")

        self.connect.commit()
