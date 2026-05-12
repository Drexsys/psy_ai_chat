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
                username TEXT NOT NULL
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS models (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL UNIQUE
            );
        """)

        self.cursor.execute("""
            INSERT INTO  models (name) VALUES ('gemini-3.1-flash-lite');
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
                models_id INT REFERENCES models(id) ON DELETE CASCADE,
                res_id INT REFERENCES res(id) ON DELETE CASCADE,
                summary TEXT NOT NULL
            );
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id SERIAL PRIMARY KEY,
                chats_res_id INT REFERENCES chats_res ON DELETE CASCADE,
                answer TEXT NOT NULL,
                is_llm BOOLEAN NOT NULL
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

    def close(self):
        self.cursor.close()
        self.connect.close()
