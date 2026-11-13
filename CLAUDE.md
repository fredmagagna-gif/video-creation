# video-creation

Voice-over per video social con VoiceStudio (MCP locale, `.mcp.json`) + montaggio FFmpeg.
Rispondi all'utente in italiano.

- Skill: `voce-clonata` (una volta), `voiceover` (per ogni video). Doppiaggio: `docs/doppiaggio.md` (si fa nell'app).
- Lavori dell'utente in `progetti/<nome>/` (media ignorati da git). È anche l'unica
  cartella che VoiceStudio legge/scrive (`OMNIVOICE_MCP_BASE_PATH`).
- Codice in `videocreation/` (solo libreria standard); CLI in `scripts/`.
- Test: `python3 -m pytest` (serve ffmpeg).
- Non committare mai audio o video.
