import psycopg2
from uuid import uuid4, UUID

class DBManager:
    def __init__(self, host, dbname, user, password, port):
        self.host = host
        self.port = port
        self.dbname = dbname
        self.user = user
        self.password = password
        self.conn = psycopg2.connect(
            dbname=self.dbname,
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
        )
        self.cursor = self.conn.cursor()
        self.conn.commit()
        self.create_tables()
    
    def create_tables(self):
        self.cursor.execute("""
        BEGIN;


        CREATE TABLE IF NOT EXISTS public.account
        (
            id uuid NOT NULL,
            created timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
            telegram_name character varying(36) COLLATE pg_catalog."default",
            telegram_user_id character varying(256) COLLATE pg_catalog."default" NOT NULL,
            refered_by uuid,
            is_staff boolean NOT NULL DEFAULT false,
            CONSTRAINT user_pkey PRIMARY KEY (id)
        );

        CREATE TABLE IF NOT EXISTS public.advert
        (
            id uuid NOT NULL,
            advert_msg_id character varying(128) COLLATE pg_catalog."default" NOT NULL,
            created_at time with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
            send_time time with time zone DEFAULT CURRENT_TIMESTAMP,
            owner_id uuid,
            FOREIGN KEY (owner_id) REFERENCES account(id),
            CONSTRAINT advert_pkey PRIMARY KEY (id)
        );

        END;
        """)
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
            "lang": raw[6],
            "joined_group": raw[7],
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

    def create_account(self, telegram_user, ref=None):
        """Creates new account in db."""
        telegram_name = telegram_user.first_name
        telegram_user_id = telegram_user.id

        try:
            UUID(str(ref))

        except ValueError:
            ref = None

        if ref:
            sql_query = "INSERT INTO account (id, telegram_name, telegram_user_id, refered_by) VALUES (%s, %s, %s, %s)"
            data = (str(uuid4()), telegram_name, telegram_user_id, ref,)
            self.cursor.execute(sql_query, data)

        else:
            sql_query = "INSERT INTO account (id, telegram_name, telegram_user_id) VALUES (%s, %s, %s)"
            data = (str(uuid4()), telegram_name, telegram_user_id,)
            self.cursor.execute(sql_query, data)
        self.conn.commit()

    def get_account(self, telegram_user_id: str):
        """Returns account from db by telegram_user_id."""
        sql_query = "SELECT * FROM account WHERE telegram_user_id = '%s'"
        data = (telegram_user_id,)
        self.cursor.execute(sql_query, data)
        self.conn.commit()
        raw_result = self.cursor.fetchone()

        if raw_result:
            result = self._convert_account_to_dict(raw_result)
            return result

    def get_advert(self, advert_id):
        """Returns advert from db by advert_id."""
        try:
            UUID(str(advert_id))

        except ValueError:
            return False

        sql_query = "SELECT * FROM advert WHERE id = %s"
        data = (advert_id,)
        self.cursor.execute(sql_query, data)
        self.conn.commit()
        raw_result = self.cursor.fetchone()

        if raw_result:
            result = self._convert_advert_to_dict(raw_result)
            return result

    def get_advert_by_user(self, telegram_user_id):
        """Returns advert from db by telegram_user_id."""
        sql_query = "SELECT * FROM advert WHERE owner_id = '%s'"
        data = (telegram_user_id,)
        self.cursor.execute(sql_query, data)
        self.conn.commit()
        raw_result = self.cursor.fetchone()

        if raw_result:
            result = self._convert_advert_to_dict(raw_result)
            return result
    
    def delete_advert(self, advert_id):
        """Returns account from db by telegram_user_id."""
        sql_query = "DELETE FROM advert WHERE id = %s"
        data = (advert_id,)
        self.cursor.execute(sql_query, data)
        self.conn.commit()
        
        return None
    
    def create_advert(self, advert_msg_id, owner_id):
        """Creates new advert in db."""
        uuid = uuid4()
        sql_query = "INSERT INTO advert (id, advert_msg_id, owner_id) VALUES (%s, %s, %s)"
        data = (str(uuid), advert_msg_id, owner_id,)
        self.cursor.execute(sql_query, data)

        self.conn.commit()
        return str(uuid)
        
    def get_account_by_owner_id(self, advert_owner_id):
        """Returns account from db by telegram_user_id."""
        sql_query = "SELECT * FROM account WHERE id = %s"
        data = (advert_owner_id,)
        self.cursor.execute(sql_query, data)
        self.conn.commit()
        raw_result = self.cursor.fetchone()

        if raw_result:
            result = self._convert_account_to_dict(raw_result)
            return result

    def update_selected_lang(self, user, lang):
        """Updates user language in db."""
        sql_query = """UPDATE account
            SET lang = %s
            WHERE telegram_user_id = %s"""
        data = (lang, str(user),)
        self.cursor.execute(sql_query, data)

        self.conn.commit()

    def update_joined_group(self, user, joined):
        """Updates user joined group in db."""
        sql_query = """UPDATE account
            SET joined_group = %s
            WHERE telegram_user_id = %s"""
        data = (joined, str(user),)
        self.cursor.execute(sql_query, data)

        self.conn.commit()

    def get_joined_group_status(self, user):
        """Returns account from db by telegram_user_id."""
        sql_query = "SELECT * FROM account WHERE telegram_user_id = %s"
        data = (str(user),)
        self.cursor.execute(sql_query, data)
        self.conn.commit()
        raw_result = self.cursor.fetchone()

        if raw_result:
            result = self._convert_account_to_dict(raw_result)
            print(result["joined_group"])
            return result["joined_group"]