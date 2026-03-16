"""
Servizio per le API IGDB (Internet Game Database)
Richiede un account Twitch Developer: https://dev.twitch.tv/
"""

import requests
import os
import time
from functools import lru_cache

class IGDBService:
    BASE_URL = "https://api.igdb.com/v4"
    AUTH_URL = "https://id.twitch.tv/oauth2/token"

    def __init__(self):
        self.client_id = os.getenv("IGDB_CLIENT_ID", "")
        self.client_secret = os.getenv("IGDB_CLIENT_SECRET", "")
        self._token = None
        self._token_expiry = 0
        self.available = bool(self.client_id and self.client_secret)

    def _get_token(self):
        """Ottieni o rinnova il token OAuth2 di Twitch."""
        if self._token and time.time() < self._token_expiry:
            return self._token

        try:
            resp = requests.post(self.AUTH_URL, params={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials"
            }, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            self._token = data["access_token"]
            self._token_expiry = time.time() + data["expires_in"] - 60
            return self._token
        except Exception as e:
            return None

    def _headers(self):
        token = self._get_token()
        if not token:
            return None
        return {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {token}"
        }

    def search_game(self, title: str) -> dict | None:
        """Cerca un gioco su IGDB per titolo."""
        if not self.available:
            return None

        headers = self._headers()
        if not headers:
            return None

        try:
            body = f"""
                search "{title}";
                fields name, summary, cover.url, genres.name, rating, 
                       first_release_date, involved_companies.company.name,
                       platforms.name, screenshots.url, themes.name;
                limit 1;
            """
            resp = requests.post(
                f"{self.BASE_URL}/games",
                headers=headers,
                data=body,
                timeout=10
            )
            resp.raise_for_status()
            results = resp.json()
            if results:
                return self._format_game(results[0])
            return None
        except Exception as e:
            return None

    def _format_game(self, raw: dict) -> dict:
        """Formatta i dati grezzi di IGDB."""
        # Cover URL: converti thumbnail in immagine grande
        cover_url = None
        if raw.get("cover", {}).get("url"):
            cover_url = "https:" + raw["cover"]["url"].replace("t_thumb", "t_cover_big")

        # Screenshots
        screenshots = []
        for s in raw.get("screenshots", [])[:3]:
            if s.get("url"):
                screenshots.append("https:" + s["url"].replace("t_thumb", "t_screenshot_med"))

        # Release date
        release_date = None
        if raw.get("first_release_date"):
            release_date = time.strftime(
                "%Y", time.gmtime(raw["first_release_date"])
            )

        return {
            "igdb_id": raw.get("id"),
            "igdb_name": raw.get("name"),
            "summary": raw.get("summary", ""),
            "cover_url": cover_url,
            "screenshots": screenshots,
            "genres": [g["name"] for g in raw.get("genres", [])],
            "themes": [t["name"] for t in raw.get("themes", [])],
            "platforms": [p["name"] for p in raw.get("platforms", [])],
            "igdb_rating": round(raw.get("rating", 0) / 10, 1) if raw.get("rating") else None,
            "release_year": release_date,
            "developer": next(
                (c["company"]["name"] for c in raw.get("involved_companies", [])
                 if c.get("company", {}).get("name")),
                None
            )
        }

    def get_similar_games(self, igdb_id: int, limit: int = 5) -> list:
        """Trova giochi simili dato un ID IGDB."""
        if not self.available:
            return []

        headers = self._headers()
        if not headers:
            return []

        try:
            body = f"""
                fields name, cover.url, genres.name, rating;
                where similar_games = {igdb_id};
                limit {limit};
            """
            resp = requests.post(
                f"{self.BASE_URL}/games",
                headers=headers,
                data=body,
                timeout=10
            )
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return []
