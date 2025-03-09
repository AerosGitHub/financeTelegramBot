import os

import psycopg2
import bcrypt


class DB:
    user = os.environ['DB_LOGIN']
    password = os.environ['DB_PASSWORD']
    dbname = 'financeTelegramBot'
    host = 'localhost'
    connect = None
    cursor = None

    def get_connect(self):
        self.connect = psycopg2.connect(host=self.host, user=self.user, password=self.password, dbname=self.dbname)
        self.cursor = self.connect.cursor()

    def close_connect(self):
        self.cursor.close()
        self.connect.close()

    def check_telegram_id(self, telegram_id) -> bool:
        self.get_connect()
        self.cursor.execute("""
            SELECT *
            FROM public."Users"
            WHERE "TelegramID"='{}'
            """.format(telegram_id))
        row = self.cursor.fetchone()
        self.close_connect()
        return False if row is None else True

    def check_login(self, login) -> bool:
        self.get_connect()
        self.cursor.execute("""
            SELECT *
            FROM public."Users"
            WHERE "Login"='{}'
            """.format(login))
        row = self.cursor.fetchone()
        self.close_connect()
        return False if row is None else True

    def check_password(self, login, password) -> bool:
        self.get_connect()
        self.cursor.execute("""
        SELECT *
        FROM public."Users"
        WHERE "Login" = '{}'
        """.format(login))
        row = self.cursor.fetchone()
        return bcrypt.checkpw(password.encode('utf-8'), row[2].encode('utf-8'))

    def set_user(self, login, password, control_phrase) -> str:
        salt = bcrypt.gensalt()
        hash_pwd = bcrypt.hashpw(password.encode('utf-8'), salt)
        print(hash_pwd)
        self.get_connect()
        self.cursor.execute("""
        INSERT INTO public."Users"("Login", "Password", "ControlPhrase")
        VALUES (%s, %s, %s)
        """, (login, hash_pwd.decode('utf-8'), control_phrase))
        print(self.cursor.statusmessage)
        self.connect.commit()
        self.close_connect()
        return ('Account has been created successfully\n'
                'Please note that the account you created is not linked to telegram. To link it, you must run the '
                '/connect command.')

    def set_telegram_id(self, telegram_id, login):
        self.get_connect()
        self.cursor.execute("""
            UPDATE public."Users" SET "TelegramID" = %s WHERE "Login" = %s
            """, (telegram_id, login))
        self.connect.commit()
        self.close_connect()
        return 'Telegram successfully set'
