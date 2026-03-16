"""
Servizio per le API RAWG (rawg.io)
Documentazione: https://rawg.io/apidocs
API key gratuita: https://rawg.io/apidocs (20.000 req/mese)
"""

import requests
import os


class RAWGService:
    BASE_URL = "https://api.rawg.io/api"

    def __init__(self):
        self.api_key = os.getenv("RAWG_API_KEY", "")
        self.available = bool(self.api_key)

    def _params(self, extra: dict = None) -> dict:
        p = {"key": self.api_key}
        if extra:
            p.update(extra)
        return p

    def search_game(self, title: str) -> dict | None:
        """Cerca un gioco su RAWG per titolo e restituisce i dati formattati."""
        if not self.available:
            return None
        try:
            resp = requests.get(
                f"{self.BASE_URL}/games",
                params=self._params({"search": title, "page_size": 1, "search_precise": True}),
                timeout=10
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])
            if not results:
                # Fallback senza search_precise
                resp2 = requests.get(
                    f"{self.BASE_URL}/games",
                    params=self._params({"search": title, "page_size": 1}),
                    timeout=10
                )
                resp2.raise_for_status()
                results = resp2.json().get("results", [])

            if results:
                return self._fetch_details(results[0]["slug"])
            return None
        except Exception:
            return None

    def _fetch_details(self, slug: str) -> dict | None:
        """Recupera i dettagli completi di un gioco tramite slug."""
        try:
            resp = requests.get(
                f"{self.BASE_URL}/games/{slug}",
                params=self._params(),
                timeout=10
            )
            resp.raise_for_status()
            return self._format_game(resp.json())
        except Exception:
            return None

    def _format_game(self, raw: dict) -> dict:
        """Formatta i dati grezzi di RAWG nel formato interno."""
        # Cover: RAWG usa background_image come copertina principale
        cover_url = raw.get("background_image", "")

        # Screenshots aggiuntivi (campo non sempre presente, recuperato separatamente se serve)
        screenshots = []

        # Generi
        genres = [g["name"] for g in raw.get("genres", [])]

        # Piattaforme
        platforms = [
            p["platform"]["name"] for p in raw.get("platforms", [])
        ]

        # Developer / Publisher
        developer = None
        for dev in raw.get("developers", []):
            developer = dev["name"]
            break

        publisher = None
        for pub in raw.get("publishers", []):
            publisher = pub["name"]
            break

        # Metacritic score → scala 0-10
        metacritic = raw.get("metacritic")
        rawg_rating = round(raw.get("rating", 0), 1) if raw.get("rating") else None

        # Anno uscita
        release_date = raw.get("released", "")
        release_year = release_date[:4] if release_date else None

        # Tags leggibili (es. "Singleplayer", "Open World")
        tags = [t["name"] for t in raw.get("tags", []) if t.get("language") == "eng"][:8]

        return {
            "rawg_id": raw.get("id"),
            "rawg_slug": raw.get("slug"),
            "rawg_name": raw.get("name"),
            "summary": raw.get("description_raw", raw.get("description", ""))[:600],
            "cover_url": cover_url,
            "screenshots": screenshots,
            "genres": genres,
            "platforms": platforms,
            "developer": developer,
            "publisher": publisher,
            "rawg_rating": rawg_rating,         # scala 0-5 (RAWG)
            "metacritic": metacritic,            # 0-100
            "release_year": release_year,
            "release_date": release_date,
            "tags": tags,
            "website": raw.get("website", ""),
            "playtime_avg": raw.get("playtime"),  # ore medie (dato RAWG)
            "esrb": raw.get("esrb_rating", {}).get("name") if raw.get("esrb_rating") else None,
        }

    def get_screenshots(self, slug: str, limit: int = 3) -> list[str]:
        """Recupera gli screenshot di un gioco."""
        if not self.available:
            return []
        try:
            resp = requests.get(
                f"{self.BASE_URL}/games/{slug}/screenshots",
                params=self._params({"page_size": limit}),
                timeout=10
            )
            resp.raise_for_status()
            return [s["image"] for s in resp.json().get("results", [])]
        except Exception:
            return []

    def get_similar_games(self, slug: str, limit: int = 5) -> list[dict]:
        """Recupera giochi simili (serie o stesso publisher)."""
        if not self.available:
            return []
        try:
            resp = requests.get(
                f"{self.BASE_URL}/games/{slug}/game-series",
                params=self._params({"page_size": limit}),
                timeout=10
            )
            resp.raise_for_status()
            return [
                {"name": g["name"], "cover_url": g.get("background_image", "")}
                for g in resp.json().get("results", [])
            ]
        except Exception:
            return []
