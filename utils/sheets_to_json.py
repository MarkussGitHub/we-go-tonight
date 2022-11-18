from __future__ import print_function
import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = '1GnS2Soa3llJcxUugvsORYrz0jLkgfZgCKVyJwkn45jc'
RANGE = 'Lapa1!A1:J'


def extract_event_list() -> list:
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('sheets', 'v4', credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                    range=RANGE).execute()
        events_sheet = result.get('values', [])
    except HttpError as err:
        print(err)

    return events_sheet


def save_event_list(events_sheet: list) -> None:
    placeholders = events_sheet[0] 

    event_list = []

    for event in events_sheet[1:]:
        event_list.append(dict(zip(placeholders, event)))

    result = {
        "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "events": {}
    }

    for event in event_list:
        if event["event_type"] not in result["events"]:
            result["events"][event["event_type"]] = []
            result["events"][event["event_type"]].append(event)

        else:
            result["events"][event["event_type"]].append(event)

    with open('data/event_list.json', 'w') as f:
        json.dump(result, f, indent=4)
