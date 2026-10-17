# Livelo preferences app

This folder contains the Streamlit sign-in and partner-preference app. The daily scraper remains in the parent `Livelo` folder and reads the preferences from Google Sheets before sending the shared Top 10 and each user's monitored-partner results.

## Run locally

From the parent `Livelo` directory, install the root dependencies and start the app:

```powershell
py -m pip install -r .\requirements.txt
py -m streamlit run .\livelo_streamlit\app.py
```

Configure Google OAuth and the spreadsheet IDs in Streamlit secrets. Use the parent's `.streamlit/secrets.toml.example` as a template. Keep actual secrets, service-account JSON files, and `.env` out of Git.

The local daily process uses the parent `.env` and `GOOGLE_SERVICE_ACCOUNT_FILE`. The scheduled-task wrapper can be installed with:

```powershell
.\livelo_streamlit\install_daily_task.ps1
```
