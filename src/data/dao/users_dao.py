import psycopg2
from ..database.database import DatabaseClient
from ..model.user_model import UserModel


class UsersDAO:
    @staticmethod
    def create_user(user: UserModel):
        conn = DatabaseClient.connection
        with conn.cursor() as cursor:
            insert_query = """
                INSERT INTO users (username, email, password, first_name, last_name, date_of_birth, gender, phone, address, current_latitude, current_longitude, current_diseases, role, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            cursor.execute(
                insert_query,
                (
                    user.username,
                    user.email,
                    user.password,
                    user.first_name,
                    user.last_name,
                    user.date_of_birth,
                    user.gender,
                    user.phone,
                    user.address,
                    user.current_latitude,
                    user.current_longitude,
                    user.current_diseases,
                    user.role,
                    user.is_active,
                ),
            )
            user_id = cursor.fetchone()[0]
            conn.commit()
            user.id = user_id
            return user

    @staticmethod
    def get_user_by_id(user_id):
        conn = DatabaseClient.connection
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            row = cursor.fetchone()
            if row:
                return UserModel.from_row(row)
            return None

    @staticmethod
    def get_user_by_username(username):
        conn = DatabaseClient.connection
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            row = cursor.fetchone()
            return UserModel.from_row(row) if row else None

    @staticmethod
    def get_user_by_email(email):
        conn = DatabaseClient.connection
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            row = cursor.fetchone()
            return UserModel.from_row(row) if row else None

    @staticmethod
    def get_all_users():
        conn = DatabaseClient.connection
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users")
            rows = cursor.fetchall()
            return [UserModel.from_row(row) for row in rows]

    @staticmethod
    def update_user(user: UserModel):
        conn = DatabaseClient.connection
        with conn.cursor() as cursor:
            update_query = """
                UPDATE users SET first_name=%s, last_name=%s, date_of_birth=%s, gender=%s, phone=%s, address=%s, current_latitude=%s, current_longitude=%s, current_diseases=%s, role=%s, is_active=%s
                WHERE id=%s
            """
            cursor.execute(
                update_query,
                (
                    user.first_name,
                    user.last_name,
                    user.date_of_birth,
                    user.gender,
                    user.phone,
                    user.address,
                    user.current_latitude,
                    user.current_longitude,
                    user.current_diseases,
                    user.role,
                    user.is_active,
                    user.id,
                ),
            )
            conn.commit()
            return user

    @staticmethod
    def delete_user(user_id):
        conn = DatabaseClient.connection
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()
            return cursor.rowcount > 0
