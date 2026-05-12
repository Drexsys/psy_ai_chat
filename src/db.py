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

        self.cursor.execute("SELECT COUNT(*) FROM models;")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute("""
                INSERT INTO models (name)
                VALUES ('gemini-3.1-flash-lite');
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
        """, (user_id, model_id, res_id, res.summary))

        self.connect.commit()
