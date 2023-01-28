import sqlite3
import sqlalchemy
import uuid
from typing import Optional


sqlite3.register_adapter(uuid.UUID, lambda u: u.bytes_le)
sqlite3.register_converter("UUID", lambda b: uuid.UUID(bytes_le=b))


class nmlDB:
    """
    Database Schema:

    users:
        - user_uuid (PK)
        - user_email
        - first_name
        - last_name

    image_sessions:
        - session_id (PK)
        - date
        - user_uuid
    """

    def __init__(self):
        self.conn = sqlite3.connect(
            "nml.db", detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )

        # Cursor to execute commands
        self.cursor = self.conn.cursor()

        # Create users Table
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS users (
                user_uuid UUID PRIMARY KEY NOT NULL UNIQUE,
                user_email text NOT NULL UNIQUE,
                first_name text NOT NULL,
                last_name text NOT NULL
            );"""
        )

        # Create image_sessions Table
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS image_sessions (
                session_id INT PRIMARY KEY NOT NULL UNIQUE,
                date text NOT NULL,
                user_uuid UUID NOT NULL UNIQUE,
                FOREIGN KEY (user_uuid) REFERENCES users(user_uuid)
            );"""
        )

        self.conn.commit()

    def get_users_all(self):
        self.cursor.execute("""SELECT * FROM users;""")
        results = self.cursor.fetchall()
        print(results)

    def get_image_sessions_all(self):
        self.cursor.execute("""SELECT * FROM image_sessions;""")
        print(self.cursor.fetchall())

    def insert_new_user(
        self, user_email: str, first_name: str, last_name: str
    ) -> uuid.UUID:
        user_uuid = uuid.uuid4()

        with self.conn:
            self.cursor.execute(
                """INSERT INTO users(user_uuid, user_email, first_name, last_name)
                VALUES (?, ?, ?, ?);""",
                (user_uuid, user_email, first_name, last_name),
            )

        return user_uuid

    def get_uuid_by_email(self, user_email: str) -> Optional[uuid.UUID]:
        self.cursor.execute(
            """SELECT user_uuid FROM users WHERE user_email = ?""", (user_email,)
        )
        results = self.cursor.fetchone()
        if results:
            return results[0]
        return None


if __name__ == "__main__":
    user_db = nmlDB()
    # new_user_uuid = user_db.insert_new_user("test.email@email.com", "ct", "firm")
    # print(f"New user uuid = {new_user_uuid}, type = {type(new_user_uuid)}")

    # new_user_uuid = user_db.insert_new_user("email.test@email.com", "user", "test")
    # print(f"New user uuid = {new_user_uuid}, type = {type(new_user_uuid)}")

    user_db.get_users_all()
    queried_user_uuid = user_db.get_uuid_by_email("email.test@email.com")
    print(queried_user_uuid)

    queried_user_uuid = user_db.get_uuid_by_email("email.tesat@email.com")
    print(queried_user_uuid)
