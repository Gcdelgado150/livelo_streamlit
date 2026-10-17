"""Google-authenticated Streamlit preferences editor for Livelo monitoring."""

from __future__ import annotations

import streamlit as st

from google_sheets import (
    app_setup_message,
    app_workbooks,
    approved_emails,
    read_watchlists,
    save_watchlist,
    worksheet_names_from_secrets,
)


st.set_page_config(page_title="Livelo partner monitor", page_icon="💠")
st.title("Livelo partner monitor")
st.caption("Sign in with Google to manage your daily email watchlist.")

if not st.user.is_logged_in:
    st.write("Sign in with your Google account. Access is available to approved email addresses.")
    if st.button("Continue with Google", type="primary"):
        st.login()
    st.stop()

email = str(st.user.get("email", "")).strip().casefold()
email_verified = st.user.get("email_verified", False)
if not email or not (email_verified is True or str(email_verified).casefold() == "true"):
    st.error("Google did not provide a verified email address for this account.")
    if st.button("Sign out"):
        st.logout()
    st.stop()

if st.button("Sign out", key="signout"):
    st.logout()

try:
    access_book, preferences_book = app_workbooks(st.secrets)
    users_sheet, preferences_sheet = worksheet_names_from_secrets(st.secrets)
    if email not in approved_emails(access_book, users_sheet):
        st.error("This Google account is not approved yet. Contact the Livelo monitor owner.")
        st.stop()
    watchlists = read_watchlists(preferences_book, preferences_sheet)
    partners = watchlists.get(email, [])
except Exception as exc:
    st.error(app_setup_message())
    st.exception(exc)
    st.stop()

st.write(f"Signed in as **{email}**")
st.subheader("Your monitored partners")
st.write("Your email will contain the shared Top 10 plus the rates for these partners.")

with st.form("add_partner", clear_on_submit=True):
    partner = st.text_input("Partner name", placeholder="For example: Magalu")
    add_submit = st.form_submit_button("Add partner")

if add_submit:
    candidate = partner.strip()
    if not candidate:
        st.error("Enter a partner name.")
    elif any(value.casefold() == candidate.casefold() for value in partners):
        st.info("That partner is already in your watchlist.")
    else:
        try:
            save_watchlist(preferences_book, preferences_sheet, email, [*partners, candidate])
            st.rerun()
        except Exception as exc:
            st.error(f"Could not save your watchlist: {exc}")

if not partners:
    st.info("Your watchlist is empty. Add a partner above.")
for name in partners:
    column, action = st.columns([5, 1])
    column.write(name)
    if action.button("Remove", key=f"remove-{name}"):
        try:
            save_watchlist(
                preferences_book, preferences_sheet, email,
                [value for value in partners if value.casefold() != name.casefold()],
            )
            st.rerun()
        except Exception as exc:
            st.error(f"Could not update your watchlist: {exc}")
