"""
One-time script to generate a Google Drive OAuth2 refresh token.

Run this LOCALLY (not on Render). It will open a browser for you to
authorize access to your Google Drive, then print the refresh token
to copy into your Render environment variables.

Usage:
    python generate_drive_token.py

Requirements (already in your venv):
    pip install google-auth-oauthlib
"""

import json
from google_auth_oauthlib.flow import InstalledAppFlow

# ------------------------------------------------------------------ #
#  PASTE your OAuth2 Client ID and Secret here (Desktop app type).   #
#  Get them from: Google Cloud Console → Credentials →               #
#  Create Credentials → OAuth 2.0 Client ID → Desktop app            #
# ------------------------------------------------------------------ #
CLIENT_ID = "[OAUTH_CLIENT_ID]"
CLIENT_SECRET = "[OAUTH_CLIENT_SECRET]"
# ------------------------------------------------------------------ #

SCOPES = ["https://www.googleapis.com/auth/drive"]

client_config = {
    "installed": {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
    }
}

flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)
creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")

print("\n" + "=" * 60)
print("SUCCESS! Copy these values into your Render environment:")
print("=" * 60)
print(f"\nGOOGLE_DRIVE_CLIENT_ID     = {CLIENT_ID}")
print(f"GOOGLE_DRIVE_CLIENT_SECRET = {CLIENT_SECRET}")
print(f"GOOGLE_DRIVE_REFRESH_TOKEN = {creds.refresh_token}")
print("\n" + "=" * 60)
print("Also keep your GOOGLE_DRIVE_FOLDER_ID set to your Drive folder.")
print("=" * 60 + "\n")
