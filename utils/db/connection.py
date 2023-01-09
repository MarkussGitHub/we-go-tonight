import yaml

from utils.db.db_utils import DBManager

with open("settings.local.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

host = config["DB_HOST"]
port = config["DB_PORT"]
dbname = config["DB_NAME"]
user = config["DB_USER"]
password = config["DB_PASSWORD"]

db = DBManager(host, dbname, user, password, port)