import logging
import os.path
from datetime import datetime
from typing import List
from urllib.parse import urlparse

import requests
import vobject
from dateutil import tz
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from icalevents.icalevents import events
from icalevents.icalparser import Event
from lxml import etree
from requests.auth import HTTPBasicAuth

import settings

logger = logging.getLogger('app')


def sort_by_date(e: Event):
    return e.start.astimezone()


def get_events(max_number: int) -> List[Event]:
    cal_events = []
    for calendar_url in settings.CALENDAR_URLS:
        cal_events.extend(get_webdav_events(calendar_url, max_number))
    cal_events.sort(key=sort_by_date)
    return cal_events[:max_number]


def get_webdav_events(url: str, max_number: int) -> List[Event]:
    logger.info("Retrieving calendar infos")
    utc_timezone = tz.tzutc()
    current_timezone = tz.tzlocal()
    today_midnight = datetime.now(current_timezone).replace(hour=0, minute=0, second=0, microsecond=0)
    is_apple = "icloud" in url
    try:
        event_list = events(url, fix_apple=is_apple)
        event_list.sort(key=sort_by_date)

        start_count = 0
        for event in event_list:
            if event.all_day:
                event.start.replace(tzinfo=current_timezone)
            else:
                event.start.replace(tzinfo=utc_timezone)
                event.start = event.start.astimezone(current_timezone)

            # Multi-day events end at midnight of the previous/current
            # day and thus show up after they're over.
            if event.end == today_midnight:
                start_count += 1
                max_number += 1
        logger.info(
            "Got %s calendar-entries (capped to %s)",
            len(event_list) - start_count,
            max_number - start_count
        )
        return event_list[start_count:max_number]

    except Exception as e:
        logger.critical(e)
        return []


def get_birthdays_caldav() -> List[str]:
    logger.info("Retrieving contact (birthday) infos")
    try:
        session = requests.Session()
        session.auth = HTTPBasicAuth(settings.CALDAV_CONTACT_USER, settings.CALDAV_CONTACT_PWD)
        baseurl = urlparse(settings.CALDAV_CONTACT_URL).scheme + \
            '://' + urlparse(settings.CALDAV_CONTACT_URL).netloc

        resp = requests.request('PROPFIND', settings.CALDAV_CONTACT_URL, headers={'Depth': '1'})
        import pdb; pdb.set_trace()
        if resp.status_code != 207:
            raise RuntimeError('error in response from %s: %r' %
                               (settings.CALDAV_CONTACT_URL, r))

        vcardUrlList = []
        root = etree.XML(resp.text.encode())
        for link in root.xpath('./d:response/d:propstat/d:prop/d:getcontenttype[starts-with(.,"text/vcard")]/../../../d:href', namespaces={"d": "DAV:"}):
            vcardUrlList.append(baseurl + link.text)

        today = datetime.today()
        birthday_names: List[str] = []
        for vurl in vcardUrlList:
            r = requests.request("GET", vurl, auth=auth)
            vcard = vobject.readOne(r.text)
            if 'bday' in vcard.contents.keys():
                birthday = vcard.contents['bday'][0]
                try:
                    birthday_date = datetime.strptime(
                        birthday.value, "%Y-%m-%d")
                except ValueError:
                    # necessary, because multipe formats are used...
                    birthday_date = datetime.strptime(birthday.value, "%Y%m%d")

                if (birthday_date.day == today.day) and (birthday_date.month == today.month):
                    name = vcard.contents['fn'][0].value
                    birthday_names.append(name)
        return birthday_names
    except Exception as e:
        logger.critical(e)
        return []


def get_birthdays_google() -> List[str]:
    scopes = ["https://www.googleapis.com/auth/contacts.readonly"]
    logger.info("Retrieving contact (birthday) infos")
    today = datetime.today()
    birthday_names: List[str] = []

    creds = None
    if os.path.exists("token.json"):
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time.
        creds = Credentials.from_authorized_user_file("token.json", scopes)

    if not creds or not creds.valid:
        # If there are no (valid) credentials available, let the user log in.
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", scopes)
            creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(creds.to_json())
    try:
        service = build("people", "v1", credentials=creds)

        group = service.contactGroups().get(
            resourceName=f"contactGroups/{settings.GOOGLE_CONTACTS_GROUP}",
            maxMembers=100
        ).execute()

        results = service.people().getBatchGet(
            resourceNames=group.get("memberResourceNames"),
            personFields="names,birthdays",
        ).execute()
    except HttpError as e:
        logger.critical(e)
        return []

    for result in results.get("responses"):
        person = result.get("person")

        if person.get("birthdays") and person.get("birthdays")[0].get("date"):
            birthday = person.get("birthdays")[0].get("date")
            if (birthday.get("day") == today.day) and (birthday.get("month") == today.month) and person.get("names"):
                birthday_names.append(person.get("names")[0].get("displayName"))
    return birthday_names


def get_birthdays() -> List[str]:
    if settings.GOOGLE_CONTACTS_GROUP:
        return get_birthdays_google()
    elif settings.CALDAV_CONTACT_USER and settings.CALDAV_CONTACT_PWD:
        return get_birthdays_caldav()
