"""
Assistente AI per la libreria giochi - powered by Google Gemini.
"""

import os
import google.generativeai as genai

SYSTEM_PROMPT = """Sei un assistente esperto di videogiochi chiamato "GamePal". 
Conosci la libreria di giochi dell'utente e puoi dare consigli personalizzati.

Sei appassionato, diretto e onesto. Non esitare a dare opinioni nette.
Parla in italiano. Usa emoji videoludiche con moderazione.

Quando consigli cosa giocare, considera:
- Lo stato attuale (Backlog, Playing, ecc.)
- Il genere preferito dell'utente dai suoi voti
- Quanto tempo ci vuole (HowLongToBeat)
- La qualità del gioco (voto personale e Metacritic)

Puoi rispondere a domande come:
- "Cosa dovrei giocare stasera?" 
- "Ho 2 ore libere, cosa mi consigli?"
- "Qual è il gioco migliore del mio backlog?"
- "Hai informazioni su [gioco]?"
- Qualsiasi domanda sui giochi in libreria
"""


class AIAssistant:
    def __init__(self):
        api_key = os.getenv("GOOGLLE_API_KEY", "")
        self.available = bool(api_key)
        if self.available:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")

    def chat(self, messages: list, library_context: str) -> str:
        if not self.available:
            return (
                "⚠️ Assistente AI non disponibile. "
                "Configura `GEMINI_API_KEY` nelle variabili d'ambiente per abilitarlo."
            )

        system = SYSTEM_PROMPT
        if library_context:
            system += f"\n\n--- LIBRERIA DELL'UTENTE ---\n{library_context}\n---"

        # Converti messaggi nel formato Gemini
        # Il primo messaggio di sistema va nel system_instruction
        history = []
        for m in messages[:-1]:
            role = "user" if m["role"] == "user" else "model"
            history.append({"role": role, "parts": [m["content"]]})

        last_message = messages[-1]["content"]

        try:
            model = genai.GenerativeModel(
                "gemini-1.5-flash",
                system_instruction=system
            )
            chat_session = model.start_chat(history=history)
            response = chat_session.send_message(last_message)
            return response.text
        except Exception as e:
            return f"❌ Errore Gemini: {str(e)}"

    def quick_recommend(self, library_context: str, constraint: str = "") -> str:
        prompt = "Guardando la mia libreria, cosa mi consigli di giocare adesso?"
        if constraint:
            prompt += f" {constraint}"
        return self.chat([{"role": "user", "content": prompt}], library_context)
