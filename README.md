# Livelo partner monitor web app

This Streamlit app lets approved users sign in with Google and manage their own partner watchlist. The daily scraper in the parent `Livelo` folder reads those watchlists from Google Sheets and sends each account its report. Google sign-in identifies the user; the app separately checks the `ApprovedUsers` sheet before allowing access.

## What you need

- Python 3.10 or newer
- A Google Cloud project
- Two Google spreadsheets: one for approved accounts and one for partner preferences
- Access to create Google OAuth credentials and a service account in that project

## 1. Create the spreadsheets

Create (or choose) two spreadsheets. Add a worksheet named `ApprovedUsers` to the first and put these exact column headers in row 1:

| email | approved |
| --- | --- |
| person@example.com | TRUE |

Only rows whose `approved` value is `true`, `yes`, `1`, `approved`, or `active` (case-insensitive) can use the app. Add one row per person you want to allow.

In the second spreadsheet, add a worksheet named `Preferences` with these headers:

| email | partners_json |
| --- | --- |
| person@example.com | `["Magalu","Booking"]` |

The app creates and updates a user's row when they change their list. `partners_json` must be a JSON array of partner names. Users must also be present and approved in the first spreadsheet.

Copy each spreadsheet ID from its URL. It is the text between `/d/` and `/edit`:

```text
https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
```

## 2. Set up Google OAuth sign-in

1. In [Google Cloud Console](https://console.cloud.google.com/), create or select a project.
2. Configure the Google Auth Platform / OAuth consent screen. Choose an audience appropriate for your users. If the app is in testing mode, add every intended account as a test user. Complete any required app details and scopes; Streamlit requests basic OpenID Connect identity scopes (`openid`, `profile`, and `email`).
3. Open **Google Auth Platform > Clients** (or **APIs & Services > Credentials**, depending on the Console view) and create an OAuth client with application type **Web application**.
4. Add this authorized redirect URI for local use, exactly as written:

   ```text
   http://localhost:8501/oauth2callback
   ```

   The redirect URI must match the app's `redirect_uri` exactly. If you deploy the app, add its public callback URI too, such as `https://your-app.example.com/oauth2callback`, and set that same URL in the deployed secrets. Keep the local URI if you will still run locally.

5. Create the client and copy its client ID and client secret. Treat the client secret as a password.

## 3. Give the app access to Google Sheets

The app uses a service account to read the approval list and read/write preferences. This is separate from each user's Google OAuth sign-in.

1. Enable the **Google Sheets API** in the same Google Cloud project that contains the service account:
   - Open [Google Cloud Console](https://console.cloud.google.com/). Make sure you are signed in to the Google account that owns or can manage the project.
   - Use the project selector at the top of the page to select the project you used for this app. The project name should match the project used for the service account whose key you will put in `secrets.toml`.
   - Open **APIs & Services > Library** from the navigation menu, or go directly to the [Google Sheets API page](https://console.cloud.google.com/apis/library/sheets.googleapis.com). If asked, select the same project again.
   - Search for **Google Sheets API**, open its result, and click **Enable**. If the page shows **Manage** instead, the API is already enabled. It can take a short time for a new API activation to become available.
   - If you cannot see the project or the Enable button, ask the project owner/admin to grant you access to manage APIs, or have them enable the API.

   Enabling the API allows the project to make Sheets API requests; it does not grant spreadsheet access by itself. The service account still needs to be shared on each spreadsheet in step 4 below.
2. Create a service account and a JSON key for it:
   - In Google Cloud Console, confirm the project selector is still set to the project where you enabled the Sheets API.
   - Open **IAM & Admin > Service Accounts** and click **Create service account**. You can also open the [Service Accounts page](https://console.cloud.google.com/iam-admin/serviceaccounts) and select the project there.
   - Enter a name such as `livelo-streamlit-sheets`; Google will fill in a service account ID. The ID becomes an email address like `livelo-streamlit-sheets@your-project-id.iam.gserviceaccount.com`. Add an optional description such as `Reads approval list and updates Livelo partner preferences`, then click **Create and continue**.
   - On **Grant this service account access to project**, you do not need to add a project role for this app. Click **Continue**, then **Done**. Access to the actual spreadsheets will be granted by sharing each sheet with the service account in step 4.
   - In the service accounts list, click the new account's email/name. Open the **Keys** tab, choose **Add key > Create new key**, select **JSON**, then click **Create**. Your browser downloads the key file. Google only lets you download a newly created private key once, so save it somewhere private while setting up the app. If **Create new key** is unavailable, your Google Workspace/Cloud organization may block service-account key creation; ask its administrator about an approved credential method.
   - Do not upload the JSON key to GitHub, share it in chat/email, or put it in a public folder. It contains a private key that lets the app act as this service account. After copying its values into Streamlit secrets, keep the original in a secure location or delete the downloaded copy if it is no longer needed. If it is exposed, delete/revoke that key in the service account's **Keys** tab and create a replacement.
3. Open the downloaded JSON key file and copy its fields into the `[google_service_account]` section of `secrets.toml` in the next step. The JSON object includes fields such as `type`, `project_id`, `private_key_id`, `private_key`, and `client_email`. Preserve the private key's newlines (TOML represents them as `\n`). The `client_email` value is the address you will share the spreadsheets with.
4. Share each spreadsheet with the service account:
   - In the downloaded service-account JSON key, find the `client_email` line. Copy the full email address after the colon, including the `@...iam.gserviceaccount.com` part. It is the app's account address; it is not your personal Google email.
   - Open the first spreadsheet (the one with the `ApprovedUsers` tab) in Google Sheets and click **Share** in the upper-right corner.
   - Paste the service account email into **Add people, groups, and calendar events**. Select **Editor** as its role, then click **Send** or **Share** to confirm. If Google Sheets offers to notify people, notification is optional; the permission is what matters.
   - Repeat these same steps for the second spreadsheet (the one with the `Preferences` tab), using the same service account email and **Editor** role. Editor is needed there because the app saves watchlist changes. The app only reads the approved-users spreadsheet, but it still needs permission to open it.

   When finished, the service account email should appear in the sharing list for both spreadsheets. If Sheets says it cannot share with that address, double-check that you copied `client_email` exactly and that external sharing is allowed by your Google Workspace administrator.

## 4. Create local Streamlit secrets

From the `Livelo` directory, make the local secrets folder and copy the example:

```powershell
New-Item -ItemType Directory -Force .\livelo_streamlit\.streamlit
Copy-Item .\livelo_streamlit\.streamlit\secrets.toml.example .\livelo_streamlit\.streamlit\secrets.toml
notepad .\livelo_streamlit\.streamlit\secrets.toml
```

Fill in the values in the copied file:

- `[auth]`: OAuth client ID and secret from step 2, the exact local redirect URI above, and a long random `cookie_secret` (for example, generate one with `py -c "import secrets; print(secrets.token_urlsafe(48))"`). Keep the Google server metadata URL as shown in the example.
- `[google_sheets]`: the two spreadsheet IDs from step 1 and the worksheet names. The names must match the tabs in your spreadsheets.
- `[google_service_account]`: all fields from the service-account JSON key from step 3.

The checked-in `.streamlit/secrets.toml.example` is a template only. The real `.streamlit/secrets.toml` is ignored by Git. Do not commit it, the downloaded key, or screenshots/logs containing credentials.

For a deployed app, put the same TOML sections and values in the hosting platform's Streamlit secrets configuration. Use the deployed OAuth redirect URI there and in Google Cloud.

## 5. Install and run locally

From the `Livelo` directory in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r .\livelo_streamlit\requirements.txt
py -m streamlit run .\livelo_streamlit\app.py
```

Open the local URL Streamlit prints (normally `http://localhost:8501`) and choose **Continue with Google**. Sign in with an account that is both allowed as an OAuth test user (if the consent screen is in testing) and listed with an active approval value in `ApprovedUsers`. Add or remove partners in the app; the app saves changes to `Preferences`.

If OAuth reports a redirect URI mismatch, make sure the running port, `[auth].redirect_uri`, and the OAuth client's authorized redirect URI are identical. If Sheets access fails, check that the IDs and tab names are correct and that both sheets are shared with the service account email.

## Daily email scraper

The daily scraper and its scheduled task are configured separately from this web app. Follow the parent [Livelo README](../README.md) for scraper dependencies and scheduling. The scraper uses `Livelo/.env` and its own read-only Google Sheets service-account setup; the Streamlit app's `[google_service_account]` settings are for the web app.

## References

- [Streamlit user authentication and OIDC configuration](https://docs.streamlit.io/develop/concepts/connections/authentication)
- [Google OAuth 2.0 for web server applications](https://developers.google.com/identity/protocols/oauth2/web-server)
