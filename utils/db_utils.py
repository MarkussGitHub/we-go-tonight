import psycopg2
from uuid import uuid4, UUID

class DBManager:
    def __init__(self, host, dbname, user, password):
        self.host = host
        self.dbname = dbname
        self.user = user
        self.password = password
        self.conn = psycopg2.connect(
            dbname=self.dbname,
            user=self.user,
            password=self.password,
            host=self.host,
            port="5432",
        )
        self.cursor = self.conn.cursor()
        self.conn.commit()

    def _convert_account_to_dict(self, raw):
        """Converts raw account from db to dict."""
        return {
            "id": raw[0],
            "created_at": raw[1],
            "telegram_name": raw[2],
            "telegram_user_id": raw[3],
            "refered_by": raw[4],
            "is_staff": raw[5],
            "is_moderator": raw[6],
        }

    def _convert_advert_to_dict(self, raw):
        """Converts raw advert from db to dict."""
        return {
            "id": raw[0],
            "advert_msg_id": raw[1],
            "created_at": raw[2],
            "send_time": raw[3],
            "owner_id": raw[4],
        }

    def create_account(self, telegram_user, ref):
        """Creates new account in db."""
        telegram_name = telegram_user.first_name
        telegram_user_id = telegram_user.id

        try:
            UUID(str(ref))

        except ValueError:
            ref = None

        if ref:
            self.cursor.execute(
                "INSERT INTO account (id, telegram_name, telegram_user_id, refered_by)"
                f"VALUES ('{uuid4()}', '{telegram_name}', '{telegram_user_id}', '{ref}');"
            )

        else:
            self.cursor.execute(
                "INSERT INTO account (id, telegram_name, telegram_user_id)"
                f"VALUES ('{uuid4()}', '{telegram_name}', '{telegram_user_id}');"
            )
        self.conn.commit()

    def get_account(self, telegram_user_id):
        """Returns account from db by telegram_user_id."""
        self.cursor.execute(
            f"SELECT * FROM account WHERE telegram_user_id = '{telegram_user_id}'")
        self.conn.commit()
        raw_result = self.cursor.fetchone()

        if not raw_result:
            return None

        result = self._convert_account_to_dict(raw_result)

        return result

    def get_advert(self, advert_id):
        """Returns advert from db by advert_id."""
        self.cursor.execute(
            f"SELECT * FROM advert WHERE id = '{advert_id}'")
        self.conn.commit()
        raw_result = self.cursor.fetchone()

        if not raw_result:
            return False

        result = self._convert_advert_to_dict(raw_result)

        return result

    def get_advert_by_user(self, telegram_user_id):
        """Returns advert from db by telegram_user_id."""
        self.cursor.execute(
            f"SELECT * FROM advert WHERE owner_id = '{telegram_user_id}'")
        self.conn.commit()
        raw_result = self.cursor.fetchone()

        if not raw_result:
            return False

        result = self._convert_advert_to_dict(raw_result)

        return result
    
    def delete_advert(self, advert_id):
        """Returns account from db by telegram_user_id."""
        self.cursor.execute(
            f"DELETE FROM advert WHERE id = '{advert_id}'")
        self.conn.commit()
        
        return None
    
    def create_advert(self, advert_msg_id, owner_id):
        """Creates new advert in db."""
        uuid = uuid4()
        self.cursor.execute(
            "INSERT INTO advert (id, advert_msg_id, owner_id)"
            f"VALUES ('{uuid}', '{advert_msg_id}', '{owner_id}');"
        )

        self.conn.commit()
        return str(uuid)
        
    def get_account_by_owner_id(self, advert_owner_id):
        """Returns account from db by telegram_user_id."""
        self.cursor.execute(
            f"SELECT * FROM account WHERE id = '{advert_owner_id}'")
        self.conn.commit()
        raw_result = self.cursor.fetchone()

        if not raw_result:
            return None

        result = self._convert_account_to_dict(raw_result)

        return result