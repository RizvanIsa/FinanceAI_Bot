import os
from typing import Sequence

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


def get_credentials(
    client_secret_path: str,
    token_path: str = "secrets/token.json",
    scopes: Sequence[str] | None = None,
) -> Credentials:
    """
    Получает OAuth credentials для Google API.

    - При первом запуске откроется браузер и попросит доступ.
    - Токен сохранится в token.json, дальше будет использоваться автоматически.
    """
    if scopes is None:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]

    if not client_secret_path or not os.path.exists(client_secret_path):
        raise FileNotFoundError(
            f"OAuth client secret file not found: {client_secret_path}"
        )

    creds: Credentials | None = None

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Авто-обновление токена
            creds.refresh(Request())
        else:
            # Первый вход через браузер
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, scopes)
            creds = flow.run_local_server(port=0)

        # Сохраняем токен локально
        os.makedirs(os.path.dirname(token_path), exist_ok=True)
        with open(token_path, "w", encoding="utf-8") as token_file:
            token_file.write(creds.to_json())

    return creds
