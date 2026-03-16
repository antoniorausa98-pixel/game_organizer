"""
Servizio per HowLongToBeat.com
Recupera quanto tempo ci vuole a finire un gioco.
"""

import requests
import json
import re

class HLTBService:
    BASE_URL = "https://howlongtobeat.com"
    API_URL = f"{BASE_URL}/api/search"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://howlongtobeat.com",
        "Content-Type": "application/json",
        "Origin": "https://howlongtobeat.com"
    }

    def search(self, title: str) -> dict | None:
        """Cerca i tempi di completamento per un gioco."""
        try:
            payload = {
                "searchType": "games",
                "searchTerms": title.split(),
                "searchPage": 1,
                "size": 5,
                "searchOptions": {
                    "games": {
                        "userId": 0,
                        "platform": "",
                        "sortCategory": "popular",
                        "rangeCategory": "main",
                        "rangeTime": {"min": None, "max": None},
                        "gameplay": {"perspective": "", "flow": "", "genre": ""},
                        "rangeYear": {"min": "", "max": ""},
                        "modifier": ""
                    },
                    "users": {"sortCategory": "postcount"},
                    "lists": {"sortCategory": "follows"},
                    "filter": "",
                    "sort": 0,
                    "randomizer": 0
                },
                "useCache": True
            }

            resp = requests.post(
                self.API_URL,
                headers=self.HEADERS,
                json=payload,
                timeout=10
            )
            resp.raise_for_status()
            data = resp.json()

            if data.get("data") and len(data["data"]) > 0:
                return self._format(data["data"][0])
            return None

        except Exception as e:
            return self._fallback_search(title)

    def _fallback_search(self, title: str) -> dict | None:
        """Fallback con scraping diretto della pagina di ricerca."""
        try:
            resp = requests.get(
                f"{self.BASE_URL}/search_results",
                params={"query": title},
                headers=self.HEADERS,
                timeout=10
            )
            # Se fallisce restituiamo None senza crashare
            return None
        except Exception:
            return None

    def _format(self, raw: dict) -> dict:
        """Formatta i tempi in ore leggibili."""
        def secs_to_hours(secs):
            if not secs or secs == 0:
                return None
            h = round(secs / 3600, 1)
            return h

        return {
            "hltb_id": raw.get("game_id"),
            "hltb_name": raw.get("game_name"),
            "main_story": secs_to_hours(raw.get("comp_main")),
            "main_extra": secs_to_hours(raw.get("comp_plus")),
            "completionist": secs_to_hours(raw.get("comp_100")),
            "all_styles": secs_to_hours(raw.get("comp_all")),
        }

    def format_time(self, hours) -> str:
        """Formatta le ore in stringa leggibile."""
        if hours is None:
            return "N/D"
        if hours < 1:
            return f"{int(hours * 60)}min"
        return f"{hours:.0f}h" if hours == int(hours) else f"{hours}h"
