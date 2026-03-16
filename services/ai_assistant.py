"""
Assistente AI per la libreria giochi - powered by Claude.
"""

import os
import anthropic

SYSTEM_PROMPT = """Sei un assistente esperto di videogiochi chiamato "GamePal". 
Conosci la libreria di giochi dell'utente e puoi dare consigli personalizzati.

Sei appassionato, diretto e onesto. Non esitare a dare opinioni nette.
Parla in italiano. Usa emoji videoludiche con moderazione.

Quando consigli cosa giocare, considera:
- Lo stato attuale (Backlog, Playing, ecc.)
- Il genere preferito dell'utente dai suoi voti
- Quanto tempo ci vuole (HowLongToBeat)
- La qualità del gioco (voto personale e IGDB)

Puoi rispondere a domande come:
- "Cosa dovrei giocare stasera?" 
- "Ho 2 ore libere, cosa mi consigli?"
- "Qual è il gioco migliore del mio backlog?"
- "Hai informazioni su [gioco]?"
- Qualsiasi domanda sui giochi in libreria
"""


class AIAssistant:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.available = bool(api_key)
        if self.available:
            self.client = anthropic.Anthropic(api_key=api_key)

    def chat(self, messages: list, library_context: str) -> str:
        """
        Invia un messaggio all'assistente.
        
        Args:
            messages: Lista di messaggi {role, content}
            library_context: Testo con la libreria corrente
            
        Returns:
            Risposta dell'assistente come stringa
        """
        if not self.available:
            return (
                "⚠️ Assistente AI non disponibile. "
                "Configura `ANTHROPIC_API_KEY` nel file `.env` per abilitarlo."
            )

        system = SYSTEM_PROMPT
        if library_context:
            system += f"\n\n--- LIBRERIA DELL'UTENTE ---\n{library_context}\n---"

        # Converti messaggi nel formato Anthropic
        formatted = []
        for m in messages:
            formatted.append({
                "role": m["role"],
                "content": m["content"]
            })

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system=system,
                messages=formatted
            )
            return response.content[0].text
        except anthropic.AuthenticationError:
            return "❌ API key non valida. Controlla il file `.env`."
        except anthropic.RateLimitError:
            return "⏳ Troppe richieste. Aspetta un momento e riprova."
        except Exception as e:
            return f"❌ Errore: {str(e)}"

    def quick_recommend(self, library_context: str, constraint: str = "") -> str:
        """Raccomandazione rapida senza storico conversazione."""
        prompt = "Guardando la mia libreria, cosa mi consigli di giocare adesso?"
        if constraint:
            prompt += f" {constraint}"

        return self.chat([{"role": "user", "content": prompt}], library_context)
