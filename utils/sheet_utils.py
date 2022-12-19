import requests
import json
import logging
import yaml
from copy import deepcopy

from uuid import uuid4
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SheetManager:
    def __init__(self, client_id, client_secret) -> None:
        self.base_url = "https://sheets.googleapis.com/v4/spreadsheets/"
        self.base_oauth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.client_id = client_id
        self.client_secret = client_secret

    def log_exception(func):
        def handle_exception(self):
            try:
                func(self)
            except Exception as e:
                logger.info("Something went wrong:", e)
        return handle_exception

    def _save_event_list(self, events_sheet: list) -> None:
        placeholders = events_sheet[0]

        event_list = []

        for event in events_sheet[1:]:
            event_list.append(dict(zip(placeholders, event)))

        result = {
            "last_updated": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
            "events": {
                "today": {
                    "Concerts/Parties": [],
                    "Culture": [],
                    "Workshop": [],
                    "Food/Drinks": [],
                    "Art/Literature": [],
                    "Theatre/Stand up": [],
                },
                "week": {
                    "Concerts/Parties": [],
                    "Culture": [],
                    "Workshop": [],
                    "Food/Drinks": [],
                    "Art/Literature": [],
                    "Theatre/Stand up": [],
                },
                "month": {
                    "Concerts/Parties": [],
                    "Culture": [],
                    "Workshop": [],
                    "Food/Drinks": [],
                    "Art/Literature": [],
                    "Theatre/Stand up": [],
                },
            }
        }
        today_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        today = datetime.strptime(today_str, "%d/%m/%Y %H:%M")
        week_str = (datetime.now()+timedelta(days=7)).strftime("%d/%m/%Y %H:%M")
        week = datetime.strptime(week_str, "%d/%m/%Y %H:%M")
        month_str = (datetime.now()+timedelta(days=31)).strftime("%d/%m/%Y %H:%M")
        month = datetime.strptime(month_str, "%d/%m/%Y %H:%M")
        for event in event_list:
            if not event.get("start_date"):
                continue

            else:
                start_date = datetime.strptime(event["start_date"], "%d/%m/%Y %H:%M")

            if start_date == today:
                result["events"]["today"][event["event_type"]].append(event)

            if start_date <= week and start_date >= today:
                result["events"]["week"][event["event_type"]].append(event)

            if start_date <= month and start_date >= today:
                result["events"]["month"][event["event_type"]].append(event)

        result_sorted = deepcopy(result)

        for date_key, date_value in result["events"].items():
            for event_key, event_value in date_value.items():
                result_sorted["events"][date_key][event_key] = sorted(event_value, key=lambda x: datetime.strptime(x["start_date"], "%d/%m/%Y %H:%M"))

        with open('data/event_list.json', 'w') as f:
            json.dump(result_sorted, f, indent=4)
            logger.info("Event list saved to file.")

    @property
    def code(self) -> str:
        url = input("Enter url after oauth:  ")

        parse_result = urlparse(url)
        dict_result = parse_qs(parse_result.query)

        return dict_result["code"][0]

    @property
    def access_token(self) -> str:
        return self._access_token

    @access_token.setter
    def access_token(self, value: str) -> None:
        self._access_token = value

    @property
    def access_token_expiry(self) -> datetime:
        return self._access_token_expiry

    @access_token_expiry.setter
    def access_token_expiry(self, value: str) -> None:
        self._access_token_expiry = value

    @property
    def access_token_expired(self) -> bool:
        if datetime.now() >= self._access_token_expiry:
            return True

        else:
            return False

    @property
    def refresh_token(self) -> str:
        return self._refresh_token

    @refresh_token.setter
    def refresh_token(self, value: str) -> None:
        self._refresh_token = value

    @log_exception
    def get_oauth_link(self) -> None:
        logger.info("Getting oauth link")
        resp = requests.get(
            url=self.base_oauth_url,
            params=(
                ("client_id", self.client_id),
                ("redirect_uri", "http://localhost:53767"),
                ("response_type", "code"),
                ("scope", "https://www.googleapis.com/auth/spreadsheets.readonly"),
                ("access_type", "offline"),
                ("state", uuid4()),
            ),
            allow_redirects=False
        )

        print("Authorize:", resp.url)

    @log_exception
    def get_access_token(self) -> None:
        self.get_oauth_link()
        logger.info("Getting access token")
        r = requests.post(
            url=self.token_url,
            data={
                "grant_type": "authorization_code",
                "code": self.code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": "http://localhost:53767",
            }
        ).json()

        print(r)

        self.access_token = r["access_token"]
        self.access_token_expiry = datetime.now() + timedelta(seconds=r["expires_in"])
        self.refresh_token = r["refresh_token"]

    @log_exception
    def refresh_access_token(self) -> None:
        logger.info("Refreshing access token")
        r = requests.post(
            url=self.token_url,
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
        ).json()

        self.access_token = r["access_token"]
        self.access_token_expiry = datetime.now() + timedelta(seconds=r["expires_in"])

    @log_exception
    def get_sheet(self) -> None:
        if not hasattr(self, "access_token"):
            with open("settings.local.yaml", "r") as f:
                config = yaml.load(f, Loader=yaml.FullLoader)
            self.refresh_token = config["GOOGLE_REFRESH_TOKEN"]
            self.refresh_access_token()

        if hasattr(self, "access_token") and self.access_token_expired:
            self.refresh_access_token()

        logger.info("Getting sheet")

        r = requests.get(
            url=self.base_url + "1GnS2Soa3llJcxUugvsORYrz0jLkgfZgCKVyJwkn45jc/values/Events!A1:N",
            headers={
                "Authorization": f"Bearer {self.access_token}"
            }
        ).json()

        self._save_event_list(r["values"])