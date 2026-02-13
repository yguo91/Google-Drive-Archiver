"""
Google OAuth2 authentication handling.

SETUP INSTRUCTIONS:
==================
1. Go to https://console.cloud.google.com/
2. Create a new project (or select existing)
3. Enable the Google Drive API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Drive API"
   - Click "Enable"
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - If prompted, configure the OAuth consent screen:
     - User Type: External (or Internal for Workspace)
     - Fill in app name, user support email, developer contact
     - Add scope: https://www.googleapis.com/auth/drive
     - Add yourself as a test user
   - Application type: "Desktop app"
   - Name: "Drive Archiver" (or any name)
   - Click "Create"
5. Download the credentials:
   - Click the download icon next to your new credential
   - Save the file as "credentials.json" in the app folder
   - Or place it in %APPDATA%/DriveArchiver/credentials.json

The app will automatically detect and use the credentials file.
"""

import os
from pathlib import Path
from typing import Optional, Tuple

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from storage.config import get_token_path, get_credentials_path

# Required OAuth scopes for Drive access
SCOPES = ["https://www.googleapis.com/auth/drive"]


class AuthError(Exception):
    """Authentication error."""
    pass


class CredentialsMissingError(AuthError):
    """Raised when credentials.json is not found."""

    def __init__(self):
        super().__init__(
            "credentials.json not found. Please follow the setup instructions:\n"
            "1. Go to https://console.cloud.google.com/\n"
            "2. Create a project and enable Google Drive API\n"
            "3. Create OAuth 2.0 Desktop credentials\n"
            "4. Download and save as 'credentials.json' in the app folder"
        )


def get_credentials() -> Optional[Credentials]:
    """Load saved credentials if they exist and are valid."""
    token_path = get_token_path()

    if not token_path.exists():
        return None

    try:
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

        # Check if credentials need refresh
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            save_credentials(creds)

        if creds and creds.valid:
            return creds
        return None
    except Exception:
        return None


def save_credentials(creds: Credentials) -> None:
    """Save credentials to file."""
    token_path = get_token_path()
    token_path.parent.mkdir(parents=True, exist_ok=True)
    with open(token_path, "w", encoding="utf-8") as f:
        f.write(creds.to_json())


def authenticate() -> Tuple[Credentials, str]:
    """
    Run the OAuth flow to authenticate the user.

    Returns:
        Tuple of (credentials, user_email)

    Raises:
        CredentialsMissingError: If credentials.json is not found
        AuthError: If authentication fails
    """
    creds_path = get_credentials_path()

    if not creds_path.exists():
        raise CredentialsMissingError()

    try:
        flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
        creds = flow.run_local_server(port=0)
        save_credentials(creds)

        # Get user email from token info
        email = get_user_email(creds)

        return creds, email
    except Exception as e:
        raise AuthError(f"Authentication failed: {e}")


def get_user_email(creds: Credentials) -> str:
    """Get the email address of the authenticated user."""
    from googleapiclient.discovery import build

    try:
        service = build("drive", "v3", credentials=creds)
        about = service.about().get(fields="user").execute()
        return about.get("user", {}).get("emailAddress", "Unknown")
    except Exception:
        return "Unknown"


def revoke_credentials() -> None:
    """Delete saved credentials (disconnect)."""
    token_path = get_token_path()
    if token_path.exists():
        token_path.unlink()


def is_authenticated() -> bool:
    """Check if valid credentials exist."""
    creds = get_credentials()
    return creds is not None and creds.valid
