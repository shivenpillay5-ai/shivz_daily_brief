from __future__ import annotations

"""Read-only Google Calendar integration for the couple brief."""

from datetime import date, datetime, time
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from daily_brief.config import GoogleCalendarConfig
from daily_brief.models import CalendarEvent


GOOGLE_CALENDAR_READONLY_SCOPE = "https://www.googleapis.com/auth/calendar.readonly"
SCOPES = [GOOGLE_CALENDAR_READONLY_SCOPE]


def authorize_google_calendar(config: GoogleCalendarConfig) -> None:
    """Run the local OAuth flow and save a reusable Calendar API token."""
    _build_google_calendar_service(config)


def fetch_google_calendar_events(
    config: GoogleCalendarConfig,
    start_datetime: datetime,
    end_datetime: datetime,
    timezone_name: str,
) -> list[CalendarEvent]:
    """Fetch events from configured calendars in a bounded local time window."""
    if not config.enabled:
        return []

    service = _build_google_calendar_service(config)
    events: list[CalendarEvent] = []

    for calendar in config.calendars:
        response = (
            service.events()
            .list(
                calendarId=calendar.calendar_id,
                timeMin=start_datetime.isoformat(),
                timeMax=end_datetime.isoformat(),
                maxResults=config.max_events_per_calendar,
                singleEvents=True,
                orderBy="startTime",
                timeZone=timezone_name,
            )
            .execute()
        )
        for item in response.get("items", []):
            if isinstance(item, dict):
                events.append(
                    parse_google_calendar_event(
                        item,
                        calendar_id=calendar.calendar_id,
                        calendar_name=calendar.label,
                        timezone_name=timezone_name,
                    )
                )

    return sorted(events, key=lambda event: event.start)


def parse_google_calendar_event(
    item: dict[str, Any],
    calendar_id: str,
    calendar_name: str,
    timezone_name: str,
) -> CalendarEvent:
    start_payload = _as_mapping(item.get("start"))
    end_payload = _as_mapping(item.get("end"))
    start, all_day = _parse_google_datetime(start_payload, timezone_name)
    end, _ = _parse_google_datetime(end_payload, timezone_name) if end_payload else (
        None,
        False,
    )

    return CalendarEvent(
        calendar_id=calendar_id,
        calendar_name=calendar_name,
        title=str(item.get("summary") or "Busy"),
        start=start,
        end=end,
        all_day=all_day,
        location=str(item.get("location") or ""),
    )


def _build_google_calendar_service(config: GoogleCalendarConfig):
    _use_system_certificate_store()
    build, credentials_cls, installed_app_flow_cls, request_cls = _google_imports()
    creds = None

    if config.token_file.exists():
        creds = credentials_cls.from_authorized_user_file(str(config.token_file), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(request_cls())
        else:
            if not config.credentials_file.exists():
                raise FileNotFoundError(
                    "Google Calendar credentials file was not found: "
                    f"{config.credentials_file}. Download a Desktop OAuth client JSON "
                    "from Google Cloud and save it there."
                )
            flow = installed_app_flow_cls.from_client_secrets_file(
                str(config.credentials_file),
                SCOPES,
            )
            creds = flow.run_local_server(port=0)

        config.token_file.parent.mkdir(parents=True, exist_ok=True)
        config.token_file.write_text(creds.to_json(), encoding="utf-8")

    return build("calendar", "v3", credentials=creds)


def _google_imports():
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError(
            "Google Calendar packages are not installed. Run "
            "`python -m pip install -e .` after pulling this change."
        ) from exc

    return build, Credentials, InstalledAppFlow, Request


def _use_system_certificate_store() -> None:
    try:
        import truststore
    except ImportError:
        return

    truststore.inject_into_ssl()


def _parse_google_datetime(
    payload: dict[str, Any],
    timezone_name: str,
) -> tuple[datetime, bool]:
    date_time = payload.get("dateTime")
    if isinstance(date_time, str) and date_time.strip():
        return _parse_rfc3339(date_time), False

    date_value = payload.get("date")
    if isinstance(date_value, str) and date_value.strip():
        local_date = date.fromisoformat(date_value)
        return datetime.combine(local_date, time.min, _timezone(timezone_name)), True

    raise ValueError("Google Calendar event did not include a start date or dateTime.")


def _parse_rfc3339(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def _timezone(timezone_name: str):
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return None


def _as_mapping(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}
