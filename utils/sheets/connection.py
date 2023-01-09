import yaml

from utils.sheets.sheet_utils import SheetManager

with open("settings.local.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

client_id = config["GOOGLE_CLIENT_ID"]
client_secret = config["GOOGLE_CLIENT_SECRET"]


sheet = SheetManager(client_id, client_secret)