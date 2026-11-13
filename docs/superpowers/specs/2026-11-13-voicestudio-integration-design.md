# Integrazione VoiceStudio — design

Data: 2026-11-13 · Stato: bozza da approvare

## Perché

Video social di vario tipo (clip brevi, spesso verticali, con sottotitoli e musica). Si vuole:
voice-over da testo, doppiaggio in altre lingue, tutto con la propria voce clonata, pilotando il
lavoro chiedendo a Claude in conversazione. VoiceStudio gira in locale su Mac Apple Silicon.

## Obiettivi

- Claude Code (sul Mac, in questo repo) vede VoiceStudio come server MCP senza configurazioni manuali.
- Con una richiesta tipo "fai il voice-over di `progetti/lancio/video.mp4` con questo testo"
  Claude genera l'audio con la voce clonata e produce il video finale con voce, musica abbassata
  sotto la voce e sottotitoli.
- La voce clonata si crea una volta e diventa la voce predefinita del progetto.
- Il doppiaggio ha una guida passo-passo per farlo nell'app VoiceStudio.

## Non-obiettivi

- Doppiaggio automatizzato via Claude (approccio B, eventualmente in futuro).
- Montaggio creativo (tagli, transizioni, grafica): resta nell'editor dell'utente.
- Far girare VoiceStudio nel cloud o in Docker.

## Anti-obiettivi

- Audio base64 che passa dentro la conversazione con Claude (riempie il contesto): i file devono
  restare su disco.
- Media (video/audio) committati nel repo.

## Approcci considerati

- **A — Claude per voice-over, app per il doppiaggio** ✅ scelto dall'utente: poco codice, doppiaggio
  della qualità migliore disponibile (separazione musica/voce e timing dell'app).
- B — Tutto via Claude, doppiaggio incluso: molto più codice, serve Demucs per la musica, timing
  peggiore sulle clip veloci. Rinviato.
- C — Solo configurazione MCP: lascia fuori il montaggio audio+sottotitoli, che è il pezzo che fa
  risparmiare più tempo.

## Design

1. **`.mcp.json`** alla radice: server `voicestudio`, trasporto HTTP su
   `http://localhost:3900/mcp/`, header `X-OmniVoice-Client-Id: video-creation`.
2. **Uscita su file**: il backend VoiceStudio va avviato con
   `OMNIVOICE_MCP_OUTPUT_MODE=files` e `OMNIVOICE_MCP_BASE_PATH=<percorso del repo>`, così
   `generate_speech` scrive WAV nel repo invece di restituire base64. Guida nel README.
3. **Voce clonata**: procedura una tantum (registrazione pulita 10–30 s → `clone_voice` →
   `profile_id`), poi binding del client `video-creation` a quel profilo via
   `/api/mcp/bindings`, così ogni `generate_speech` usa la tua voce senza specificarla.
4. **Struttura progetti**: `progetti/<nome>/` con `video.*` (sorgente), `testo.md`, opzionale
   `musica.*`, e `out/` per i risultati. Media in `.gitignore`.
5. **Script di montaggio** `scripts/monta.py` (Python standard + FFmpeg da Homebrew):
   - input: video, voce WAV, musica opzionale, opzioni sottotitoli e formato;
   - mixa la voce sopra l'audio originale/musica con ducking (musica che si abbassa quando parli);
   - sottotitoli: SRT ottenuto trascrivendo la voce generata, poi bruciati nel video
     (stile leggibile su verticale) e salvati anche come `.srt` a parte;
   - output: `out/<nome>_vo.mp4` (+ `.srt`).
6. **Skill Claude** `.claude/skills/voiceover/SKILL.md`: la ricetta che Claude segue
   (controlla `check_health` → rifinisce il testo se richiesto → `generate_speech` →
   `monta.py` → riporta il percorso del file finale).
7. **Guida doppiaggio** `docs/doppiaggio.md`: passi nell'app (Dub → sorgente → lingua →
   modalità Autofit/Cinematic → revisione → export MP4 con musica originale + SRT) con le
   impostazioni consigliate per i social.
8. **Test**: test automatici dello script di montaggio su clip sintetiche generate con FFmpeg
   (senza bisogno di VoiceStudio). Il collaudo end-to-end con VoiceStudio lo fa l'utente sul Mac.

## Da verificare in implementazione (calls del builder)

- Come impostare le variabili d'ambiente del backend nell'app desktop (Impostazioni/Integrazioni
  oppure `launchctl setenv`); se non possibile, fallback documentato.
- Se `/v1/audio/transcriptions` (compatibile OpenAI) restituisce timestamp/SRT; altrimenti
  sottotitoli via `transcribe` MCP o whisper locale.
- Formato esatto della richiesta a `/api/mcp/bindings`.
