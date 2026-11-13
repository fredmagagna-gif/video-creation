# video-creation

Voice-over con la tua voce clonata per video social, gestito chiedendo a Claude.

- **Voice-over da testo** → Claude genera la voce con [VoiceStudio](https://github.com/debpalash/voicestudio)
  (locale, sul tuo Mac) e monta il video: voce sopra, musica/audio originale che si
  abbassano quando parli, sottotitoli brevi in stile social bruciati nel video + `.srt`.
- **Voce clonata** → una volta sola, poi è la voce predefinita del progetto.
- **Doppiaggio** → nell'app VoiceStudio, con la guida in [`docs/doppiaggio.md`](docs/doppiaggio.md).

## Prerequisiti

- Mac Apple Silicon con macOS 13.3+ e **VoiceStudio** installato
  (`brew install --cask debpalash/tap/voicestudio`), con un modello di sintesi vocale e
  uno di trascrizione (Whisper) scaricati dal Model Manager.
- **FFmpeg**: `brew install ffmpeg`
- **Python 3.10+** (quello di macOS/Homebrew va bene; nessuna libreria da installare).
- **Claude Code**.

## Setup (una volta)

1. Apri VoiceStudio almeno una volta e scarica i modelli.
2. Nel repo:
   ```bash
   python3 scripts/setup_voicestudio.py
   ```
   Scrive in `~/.config/omnivoice/env` due impostazioni: l'audio generato viene salvato
   come file (non passa nella chat) e VoiceStudio può leggere/scrivere solo in `progetti/`.
3. **Chiudi e riapri VoiceStudio.**
4. Apri Claude Code nella cartella del repo e approva il server MCP `voicestudio`
   (configurato in `.mcp.json`).
5. Registra 10–30 s della tua voce in `progetti/_voce/riferimento.wav` e chiedi a Claude
   **"clona la mia voce"**.

## Uso con Claude

Metti il video in `progetti/<nome>/` (es. `progetti/reel-errori/video.mp4`), poi:

- "Fai il voice-over di `progetti/reel-errori/video.mp4` con il testo in `testo.md`."
- "Scrivi un testo da 20 secondi per questo reel e fai il voice-over con tono energico."
- "Aggiungi `musica.mp3` sotto la voce e togli l'audio originale."
- "Fai anche la versione in inglese."

Il risultato è in `progetti/<nome>/out/<nome-video>_vo.mp4` (+ `.srt`).

## Montaggio senza Claude

```bash
python3 scripts/monta.py progetti/reel/video.mp4 progetti/reel/voce.wav \
  --musica progetti/reel/musica.mp3        # opzionale, va in loop
  # --togli-audio-originale                # elimina l'audio del video
  # --no-sottotitoli                       # senza trascrizione
```

## Problemi frequenti

| Sintomo | Soluzione |
|---|---|
| "Non riesco a raggiungere VoiceStudio" | Apri l'app; il backend ascolta su `localhost:3900`. |
| Claude riceve `wav_base64` invece di un file | Il setup non è attivo: rilancia `setup_voicestudio.py` e riavvia VoiceStudio. |
| "Nessun modello di trascrizione" (409) | Scarica un modello Whisper in VoiceStudio, o usa `--no-sottotitoli`. |
| "OMNIVOICE_MCP_BASE_PATH is not set" | Come sopra: setup + riavvio. |
| `FFmpeg non trovato` | `brew install ffmpeg` |

## Sviluppo

```bash
python3 -m pip install pytest
python3 -m pytest
```

I test del montaggio usano FFmpeg reale su clip sintetiche; non serve VoiceStudio.

## Licenze

VoiceStudio è AGPL-3.0; i modelli hanno licenze proprie (vedi Model Manager).
Clona solo voci di persone che hanno dato il consenso.
