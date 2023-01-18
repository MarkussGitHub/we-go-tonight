import json
import logging
from copy import deepcopy
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

import requests
import yaml

logger = logging.getLogger(__name__)

class SheetManager:
    def __init__(self, client_id, client_secret) -> None:
        self.base_url = "https://sheets.googleapis.com/v4/spreadsheets/"
        self.base_oauth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.client_id = client_id
        self.client_secret = client_secret

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

        pages_by_event_type = {
            "Concerts/Parties": {
                "page_used_space": 1,
                "page": 1
            },
            "Culture": {
                "page_used_space": 1,
                "page": 1
            },
            "Workshop": {
                "page_used_space": 1,
                "page": 1
            },
            "Food/Drinks": {
                "page_used_space": 1,
                "page": 1
            },
            "Art/Literature": {
                "page_used_space": 1,
                "page": 1
            },
            "Theatre/Stand up": {
                "page_used_space": 1,
                "page": 1
            },
        }

        prev_date = datetime.min
        for event in event_list:
            if not event.get("start_date"):
                continue
            event["id"] = str(uuid4())
            event["start_date"] = event["start_date"].strip()

            try:
                start_date = datetime.strptime(event["start_date"], "%d/%m/%Y %H:%M")
            except ValueError as e:
                print(event["event_name"], event["start_date"], e)

            if start_date < today or start_date > month:
                continue

            if pages_by_event_type[event["event_type"]]["page_used_space"] >= 8:
                pages_by_event_type[event["event_type"]]["page"] += 1
                pages_by_event_type[event["event_type"]]["page_used_space"] = 1

            if start_date.date() > prev_date.date():
                prev_date = event["start_date"]
                prev_date = datetime.strptime(prev_date, "%d/%m/%Y %H:%M")
                pages_by_event_type[event["event_type"]]["page_used_space"] += 1
            pages_by_event_type[event["event_type"]]["page_used_space"] += 1
            event["page"] = pages_by_event_type[event["event_type"]]["page"]

            if event.get("end_date"):
                event["end_date"] = event["end_date"].strip()

                try:
                    end_date = datetime.strptime(event["end_date"].strip(), "%d/%m/%Y %H:%M")
                except ValueError as e:
                    print(event["event_name"], e.args)

                ongoing_date = start_date
                while not (end_date.date() == ongoing_date.date()):
                    ev_copy = deepcopy(event)
                    open_during = ev_copy.get("open_during", "").split(", ")
                    ev_copy["start_date"] = ongoing_date.strftime("%d/%m/%Y %H:%M")
                    if str(ongoing_date.weekday() + 1) in open_during:
                        if ongoing_date.date() == today.date():
                            result["events"]["today"][event["event_type"]].append(ev_copy)

                        if ongoing_date <= week and ongoing_date >= today:
                            result["events"]["week"][ev_copy["event_type"]].append(ev_copy)

                        if ongoing_date <= month and ongoing_date >= today:
                            result["events"]["month"][event["event_type"]].append(ev_copy)

                    ongoing_date += timedelta(days=1)


            if start_date.date() == today.date():
                result["events"]["today"][event["event_type"]].append(event)

            if start_date <= week and start_date >= today:
                result["events"]["week"][event["event_type"]].append(event)

            if start_date <= month and start_date >= today:
                result["events"]["month"][event["event_type"]].append(event)

        with open('data/event_list.json', 'w') as f:
            json.dump(result, f, indent=4)
            logger.info("Event list saved to file.")

    def _save_places_list(self, place_sheet: list) -> None:
        placeholders = place_sheet[0]

        place_list = []

        for place in place_sheet[1:]:
            place_list.append(dict(zip(placeholders, place)))

        pages_by_place_type = {
            "Bar": {
                "page_used_space": 1,
                "page": 1
            },
            "Restaurant": {
                "page_used_space": 1,
                "page": 1
            },
            "Cafe": {
                "page_used_space": 1,
                "page": 1
            },
            "Club": {
                "page_used_space": 1,
                "page": 1
            },
            "Fest": {
                "page_used_space": 1,
                "page": 1
            },
            "Unique": {
                "page_used_space": 1,
                "page": 1
            },
            "Cinema": {
                "page_used_space": 1,
                "page": 1
            },
            "Concert venue": {
                "page_used_space": 1,
                "page": 1
            },
            "Gallery": {
                "page_used_space": 1,
                "page": 1
            },
        }

        result = {
            "last_updated": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
            "places": {
                "Bar": [],
                "Restaurant": [],
                "Cafe": [],
                "Club": [],
                "Fest": [],
                "Unique": [],
                "Cinema": [],
                "Concert venue": [],
                "Gallery": []
            }
        }

        for place in place_list:
            if len(place) < 5:
                print(f"PLEASE CHECK {place['place_name']}, A LOT OF FIELDS ARE MISSING")
                continue
            place_type = place["place_type"]

            try:
                result["places"][place_type].append(place)
            except KeyError as e:
                place_type = e.args[0]
                place_name = place["place_name"]
                if place_type:
                    print(f"PLACE TYPE FOR {place_name} IS UNKNOWN, PLEASE ASK DEVELOPER TO UPDATE PLACE TYPES")
                else:
                    print(f"PLACE TYPE FOR {place_name} CAN'T BE EMPTY")
            else:
                if pages_by_place_type[place["place_type"]]["page_used_space"] < 10:
                    pages_by_place_type[place["place_type"]]["page_used_space"] += 1
                else:
                    pages_by_place_type[place["place_type"]]["page_used_space"] = 1
                    pages_by_place_type[place["place_type"]]["page"] += 1
                place["page"] = pages_by_place_type[place["place_type"]]["page"]

            

        with open('data/place_list.json', 'w') as f:
            json.dump(result, f, indent=4)
            logger.info("Place list saved to file.")

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


    def sort_events_sheet(self) -> None:
        data = {
            "requests": [{
            "sortRange": {
                "range": {
                "sheetId": "300000580",
                "startRowIndex": 1,
                "endRowIndex": 1000000,
                "startColumnIndex": 0,
                "endColumnIndex": 14
                },
                "sortSpecs": [{
                "dimensionIndex": 7,
                "sortOrder": "ASCENDING"
                }]
            }
            }]
        }

        r = requests.post(
            url=self.base_url + "1GnS2Soa3llJcxUugvsORYrz0jLkgfZgCKVyJwkn45jc:batchUpdate",
            headers={
                "Authorization": f"Bearer {self.access_token}"
            },
            json=data
        )


    def get_events_sheet(self) -> None:
        if not hasattr(self, "access_token"):
            with open("settings.local.yaml", "r") as f:
                config = yaml.load(f, Loader=yaml.FullLoader)
            self.refresh_token = config["GOOGLE_REFRESH_TOKEN"]
            self.refresh_access_token()

        if hasattr(self, "access_token") and self.access_token_expired:
            self.refresh_access_token()

        logger.info("Getting events sheet")
        self.sort_events_sheet()

        r = requests.get(
            url=self.base_url + "1GnS2Soa3llJcxUugvsORYrz0jLkgfZgCKVyJwkn45jc/values/Events!A1:N",
            headers={
                "Authorization": f"Bearer {self.access_token}"
            }
        ).json()

        self._save_event_list(r["values"])


    def get_places_sheet(self) -> None:
        if not hasattr(self, "access_token"):
            with open("settings.local.yaml", "r") as f:
                config = yaml.load(f, Loader=yaml.FullLoader)
            self.refresh_token = config["GOOGLE_REFRESH_TOKEN"]
            self.refresh_access_token()

        if hasattr(self, "access_token") and self.access_token_expired:
            self.refresh_access_token()

        logger.info("Getting places sheet")

        r = requests.get(
            url=self.base_url + "1GnS2Soa3llJcxUugvsORYrz0jLkgfZgCKVyJwkn45jc/values/Places!A1:S",
            headers={
                "Authorization": f"Bearer {self.access_token}"
            }
        ).json()

        self._save_places_list(r["values"])
 

    def get_sheets(self) -> None:
        self.get_events_sheet()
        self.get_places_sheet()