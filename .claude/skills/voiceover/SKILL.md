---
name: voiceover
description: Genera un voice-over con la voce clonata dell'utente tramite VoiceStudio e lo monta sul video (voce sopra, musica abbassata quando parla, sottotitoli). Usala quando l'utente chiede "voice-over", "narrazione", "metti la mia voce sul video", "dai voce a questo reel".
---

# Voice-over su un video social

## Input

- Una cartella `progetti/<nome>/` con il video (`video.mp4` o simile).
- Il testo: `progetti/<nome>/testo.md` oppure scritto in chat. Se manca, chiedilo.
- Opzionali: `musica.*` nella cartella; lingua (default italiano); stile di lettura.

## Passi

1. **Controlla VoiceStudio**: `check_health`. Se fallisce: "Apri VoiceStudio e riprova".

2. **Adatta il testo** (solo se l'utente lo chiede o se è chiaramente troppo lungo):
   - durata video con `ffprobe -v error -show_entries format=duration -of csv=p=0 <video>`;
   - in italiano ~2.5 parole al secondo: resta sotto `durata × 2.5` parole;
   - stile social: frasi brevi, gancio nei primi 2 secondi, chiamata all'azione finale.
   Mostra il testo finale all'utente prima di generare se l'hai modificato.

3. **Genera la voce**: `generate_speech(text=..., language="it")`.
   - Non passare `profile_id`: il progetto usa la voce associata (skill `voce-clonata`).
   - `instruct` solo se l'utente chiede uno stile ("energico", "calmo", "sussurrato").
   - Testi oltre ~600 caratteri: genera un paragrafo per volta, poi concatena:
     `printf "file '%s'\n" parte1.wav parte2.wav > lista.txt && ffmpeg -f concat -safe 0 -i lista.txt -c copy voce.wav`.
   - Se la risposta contiene `wav_base64` invece di `output_path`, fermati: il setup
     non è attivo. Fai lanciare `python scripts/setup_voicestudio.py` e riavviare VoiceStudio.

4. **Sposta l'audio**: `mv "<output_path>" progetti/<nome>/voce.wav`.

5. **Monta**:
   ```bash
   python scripts/monta.py progetti/<nome>/video.mp4 progetti/<nome>/voce.wav [--musica progetti/<nome>/musica.mp3] [--togli-audio-originale] [--no-sottotitoli]
   ```
   - `--togli-audio-originale` se il video ha già una voce parlata o rumore inutile.
   - Se esce con codice 2 (VoiceStudio non raggiungibile o senza modello di
     trascrizione), riferisci il messaggio e proponi `--no-sottotitoli`.

6. **Riporta** all'utente: percorso del video finale e dell'`.srt`, durata della voce
   rispetto al video (lo script avvisa se ha dovuto allungare il video), e suggerisci
   di controllare i sottotitoli nell'`.srt` (nomi propri e numeri possono essere sbagliati).

## Altre lingue

Per una versione in un'altra lingua dello stesso testo: traduci tu il testo,
poi `generate_speech(text=<traduzione>, language="en")` ecc., e salva come
`voce_en.wav`; il video in uscita prende il nome dal video sorgente, quindi usa
`--out-dir progetti/<nome>/out_en`. Per doppiare un video *già parlato* usa invece
l'app (vedi `docs/doppiaggio.md`).
