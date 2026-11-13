---
name: voce-clonata
description: Clona la voce dell'utente in VoiceStudio e la imposta come voce predefinita di questo progetto. Usala quando l'utente dice "clona la mia voce", "usa la mia voce come predefinita", "rifai la voce clonata" o quando un voice-over fallisce perché non c'è una voce associata.
---

# Clonare la voce (una volta sola)

Clona solo la voce dell'utente o di chi ha dato il consenso esplicito. Se il riferimento
sembra la voce di qualcun altro, chiedi conferma prima di procedere.

## 1. Registrazione di riferimento

L'utente deve mettere una registrazione in `progetti/_voce/riferimento.wav`
(vanno bene anche `.m4a`/`.mp3`: convertila con
`ffmpeg -i <file> -ac 1 -ar 24000 progetti/_voce/riferimento.wav`).

Se manca, spiega come registrarla:
- 10–30 secondi, una persona sola, tono naturale da video;
- stanza silenziosa, niente musica né eco, microfono a un palmo dalla bocca;
- meglio leggere un testo noto: passalo poi come `ref_text`.

## 2. Controlli

1. `check_health` (MCP voicestudio). Se fallisce: "Apri VoiceStudio e riprova".
2. `list_voices`: se esiste già un profilo con lo stesso nome, chiedi se sostituirlo
   o crearne uno nuovo.

## 3. Clonazione

Chiama `clone_voice` con:
- `name`: es. "Fred — voce video" (chiedi il nome se non lo sai);
- `ref_audio_path`: `"_voce/riferimento.wav"` (relativo a `progetti/`, che è la
  `OMNIVOICE_MCP_BASE_PATH`);
- `ref_text`: la trascrizione se l'utente l'ha letta da un testo, altrimenti ometti;
- `language`: `"it"` (o la lingua della registrazione).

Se l'errore dice che i percorsi sono rifiutati o `OMNIVOICE_MCP_BASE_PATH is not set`,
il setup non è stato fatto: fai lanciare `python scripts/setup_voicestudio.py` e
riavviare VoiceStudio.

Annota il `profile_id` restituito.

## 4. Renderla predefinita per questo repo

```bash
curl -sS -X PUT http://127.0.0.1:3900/api/mcp/bindings \
  -H 'Content-Type: application/json' \
  -d '{"client_id":"video-creation","label":"video-creation","profile_id":"<PROFILE_ID>"}'
curl -sS http://127.0.0.1:3900/api/mcp/bindings
```

Da qui in poi `generate_speech` senza `profile_id` usa questa voce.

## 5. Prova

`generate_speech(text="Ciao, questa è la mia voce clonata. Come suona?", language="it")`.
Sposta il file in `progetti/_voce/prova.wav` e chiedi all'utente di ascoltarlo.
Se suona male, la causa più comune è il riferimento (rumore, eco, musica): proponi di
registrarlo di nuovo invece di cambiare parametri.
