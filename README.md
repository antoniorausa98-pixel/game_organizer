# 🎮 Game Library Manager

App Streamlit per gestire la tua collezione di giochi multi-piattaforma con:
- 📚 Libreria unificata (Steam, Epic Games, GOG, Xbox ecc.)
- 📊 Statistiche e grafici interattivi
- 🌐 Integrazione IGDB (copertine, descrizioni, voti)
- ⏱️ Integrazione HowLongToBeat (tempi di completamento)
- 🤖 Assistente AI GamePal (powered by Claude)

---

## 🚀 Setup rapido

### 1. Installa le dipendenze

```bash
pip install -r requirements.txt
```

### 2. Configura le API key

Copia il file `.env.example` in `.env`:

```bash
cp .env.example .env
```

Poi apri `.env` e compila:

```env
# OBBLIGATORIO per l'assistente AI
ANTHROPIC_API_KEY=sk-ant-...

# OPZIONALE per copertine e info giochi
IGDB_CLIENT_ID=...
IGDB_CLIENT_SECRET=...
```

#### Come ottenere le API key:

**Anthropic (AI Assistant):**
1. Vai su [console.anthropic.com](https://console.anthropic.com)
2. Crea un account e vai su "API Keys"
3. Crea una nuova key e incollala nel `.env`

**IGDB (Info giochi):**
1. Registrati su [dev.twitch.tv](https://dev.twitch.tv/console)
2. Crea una nuova applicazione
3. Copia `Client ID` e genera un `Client Secret`
4. Incollali nel `.env`

### 3. Avvia l'app

```bash
streamlit run app.py
```

L'app si aprirà su `http://localhost:8501`

---

## 📂 Struttura del progetto

```
game-library/
├── app.py                  # App Streamlit principale
├── requirements.txt        # Dipendenze Python
├── .env.example            # Template variabili d'ambiente
├── .env                    # Le tue API key (non committare!)
├── data/
│   ├── games_sample.csv    # Dati di esempio
│   └── my_games.csv        # La tua libreria (auto-creato)
└── services/
    ├── data_manager.py     # Gestione dati e CSV
    ├── igdb_service.py     # Client API IGDB
    ├── hltb_service.py     # Client HowLongToBeat
    └── ai_assistant.py     # Assistente AI con Claude
```

---

## 📋 Formato CSV

Il file CSV deve avere queste colonne (le altre sono opzionali):

| Colonna | Tipo | Valori |
|---------|------|--------|
| `title` | str | Nome del gioco |
| `platform` | str | Steam, Epic Games, GOG, Xbox / Game Pass, ecc. |
| `status` | str | Backlog, Playing, Completed, Dropped, On Hold |
| `genre` | str | RPG, Action, FPS, ecc. |
| `year` | int | Anno di uscita |
| `personal_rating` | float | 0.0 - 10.0 |
| `notes` | str | Note libere |

---

## 🔧 Estensioni future

- [ ] Connessione diretta Steam API (importazione automatica)
- [ ] Supporto GOG Galaxy API
- [ ] Sincronizzazione cloud (Google Drive / Dropbox)
- [ ] Notifiche per saldi (IsThereAnyDeal)
- [ ] Export per Notion / Obsidian
- [ ] App mobile con Streamlit Cloud
