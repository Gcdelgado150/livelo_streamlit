"""Google Sheets access for the standalone preferences web app."""

from __future__ import annotations

import json

import gspread

SHEETS_SCOPE = "https://www.googleapis.com/auth/spreadsheets"


def app_workbooks(secrets):
    info = dict(secrets["google_service_account"])
    client = gspread.service_account_from_dict(info, scopes=[SHEETS_SCOPE])
    config = secrets["google_sheets"]
    return (
        client.open_by_key(str(config["access_spreadsheet_id"])),
        client.open_by_key(str(config["preferences_spreadsheet_id"])),
    )


def approved_emails(book, worksheet_name: str) -> set[str]:
    result = set()
    for row in book.worksheet(worksheet_name).get_all_records():
        email = str(row.get("email", "")).strip().casefold()
        approved = str(row.get("approved", "")).strip().casefold()
        if email and approved in {"true", "yes", "1", "approved", "active"}:
            result.add(email)
    return result


def read_watchlists(book, worksheet_name: str) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for row in book.worksheet(worksheet_name).get_all_records():
        email = str(row.get("email", "")).strip().casefold()
        raw = row.get("partners_json", "")
        if not email or not raw:
            continue
        try:
            partners = json.loads(str(raw))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid partners_json value for {email}.") from exc
        if not isinstance(partners, list) or any(not isinstance(name, str) for name in partners):
            raise ValueError(f"partners_json for {email} must be a JSON array of partner names.")
        result[email] = list(dict.fromkeys(name.strip() for name in partners if name.strip()))
    return result


def save_watchlist(book, worksheet_name: str, email: str, partners: list[str]) -> None:
    worksheet = book.worksheet(worksheet_name)
    values = worksheet.get_all_values()
    if not values or [value.strip().casefold() for value in values[0][:2]] != ["email", "partners_json"]:
        raise ValueError(f"{worksheet_name} must start with columns: email, partners_json.")
    clean_email = email.strip().casefold()
    encoded = json.dumps(list(dict.fromkeys(partners)), ensure_ascii=False)
    matches = [
        index for index, row in enumerate(values[1:], start=2)
        if row and row[0].strip().casefold() == clean_email
    ]
    if matches:
        worksheet.update_cell(matches[0], 2, encoded)
        for duplicate in reversed(matches[1:]):
            worksheet.delete_rows(duplicate)
    else:
        worksheet.append_row([clean_email, encoded], value_input_option="RAW")


def worksheet_names_from_secrets(secrets) -> tuple[str, str]:
    config = secrets["google_sheets"]
    return str(config.get("approved_users_worksheet", "ApprovedUsers")), str(
        config.get("preferences_worksheet", "Preferences")
    )


def app_setup_message() -> str:
    return (
        "Configure Streamlit OIDC and Google Sheets secrets. Use columns email, approved "
        "for the access sheet and email, partners_json for preferences."
    )
