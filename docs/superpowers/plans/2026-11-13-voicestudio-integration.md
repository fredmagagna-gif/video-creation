# Integrazione VoiceStudio — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Claude Code (sul Mac dell'utente) genera voice-over con la voce clonata via MCP VoiceStudio e monta il video social finale (voce + ducking + sottotitoli) con uno script FFmpeg; il doppiaggio è documentato come flusso nell'app.

**Architecture:** `.mcp.json` collega Claude al server MCP già esposto dall'app su `localhost:3900/mcp/`. Un pacchetto Python solo-stdlib (`videocreation/`) fa tre cose: aggiorna il file env del backend, ottiene i tempi parola-per-parola dall'endpoint di trascrizione compatibile OpenAI e costruisce/esegue il comando FFmpeg. Due skill Claude descrivono le ricette (clonare la voce una volta; fare un voice-over).

**Tech Stack:** Python ≥ 3.10 (solo libreria standard), pytest, FFmpeg/ffprobe con libass (Homebrew `ffmpeg`), VoiceStudio desktop su macOS Apple Silicon.

**Spec:** `docs/superpowers/specs/2026-11-13-voicestudio-integration-design.md`

## Fatti verificati sul sorgente VoiceStudio (risolvono i "da verificare" della spec)

- Variabili backend dell'app desktop: righe `KEY=value` in `~/.config/omnivoice/env` (letto all'avvio del backend; serve riavviare l'app). File da scrivere con permessi `0600`, preservando le altre righe (può contenere `HF_TOKEN`).
- Con `OMNIVOICE_MCP_OUTPUT_MODE=files` e `OMNIVOICE_MCP_BASE_PATH=<dir>`, `generate_speech` scrive `<dir>/<audio_id>.wav` e restituisce JSON con `output_path`, `audio_duration_s`. `clone_voice(name, ref_audio_path=..., ref_text=..., language=...)` legge file solo dentro la base path e restituisce `profile_id`.
- Trascrizione: `POST http://127.0.0.1:3900/v1/audio/transcriptions`, multipart con `file`, `response_format=verbose_json`, `timestamp_granularities[]=word` (e `segment`). Risposta: `{"text", "segments":[{"start","end","text"}], "words":[{"word","start","end"}]}`. Le parole senza tempi (numeri/simboli) vengono omesse dal server. HTTP 409 = modello ASR non installato. Da loopback non serve chiave; se l'utente ha impostato `OMNIVOICE_API_KEY`, inviarla come `Authorization: Bearer`.
- Binding voce→client: `PUT http://127.0.0.1:3900/api/mcp/bindings` JSON `{"client_id": "video-creation", "label": "video-creation", "profile_id": "<id>"}`; `GET /api/mcp/bindings` per leggerli. Health: `GET /health` (lo usa la CLI ufficiale).

## Global Constraints

- Base URL VoiceStudio: `http://127.0.0.1:3900` (override con env `VOICESTUDIO_URL`).
- Client MCP id: `video-creation` (header `X-OmniVoice-Client-Id`).
- `OMNIVOICE_MCP_BASE_PATH` = percorso assoluto di `<repo>/progetti` (non la radice: i WAV generati finiscono lì).
- Nessun media committato: `progetti/**` ignorato tranne `progetti/README.md` e `progetti/esempio/testo.md`.
- Nessuna dipendenza Python di runtime oltre la stdlib; `pytest` solo per sviluppo.
- Testo per l'utente (messaggi CLI, skill, docs) in italiano.
- Output del montaggio: `progetti/<nome>/out/<stem>_vo.mp4` e `progetti/<nome>/out/<stem>_vo.srt`; video H.264 `-crf 20 -preset medium`, audio AAC 192k, `-movflags +faststart`.

## Review Focus

1. **Video senza traccia audio** (screen recording muto, b-roll): il montaggio deve funzionare con solo voce (+ musica se data). → test in Task 3.
2. **Voce più lunga del video**: non tagliare la voce; allungare il video congelando l'ultimo fotogramma (`tpad=stop_mode=clone`) e avvisare. → test in Task 3.
3. **Percorsi con spazi, apostrofi e accenti** (`progetti/l'estate è qui/`): il filtro `subtitles` di FFmpeg rompe sull'escaping; copiare l'SRT in una cartella temporanea con nome sicuro ed eseguire ffmpeg con `cwd` lì. → test in Task 3.
4. **Musica più corta del video**: va in loop fino alla fine dell'output. → test in Task 3.
5. **VoiceStudio spento o ASR non installato**: errore chiaro in italiano ("Apri VoiceStudio…" / "Installa un modello di trascrizione…"), mai traceback; `--no-sottotitoli` permette di montare comunque. → test in Task 2.

---

### Task 1: Scaffolding, `.mcp.json` e setup del file env

**Files:**
- Create: `pyproject.toml`, `.gitignore`, `.mcp.json`, `videocreation/__init__.py`, `videocreation/env_file.py`, `scripts/setup_voicestudio.py`, `progetti/README.md`, `progetti/esempio/testo.md`
- Test: `tests/test_env_file.py`

**Interfaces:**
- Produces: `upsert_env(path: Path, values: dict[str, str]) -> None`; `DEFAULT_ENV_PATH: Path = Path.home() / ".config/omnivoice/env"`; `scripts/setup_voicestudio.py [--env-file PATH]` scrive `OMNIVOICE_MCP_OUTPUT_MODE=files` e `OMNIVOICE_MCP_BASE_PATH=<abs repo>/progetti`, crea `progetti/`, stampa i passi successivi (riavviare VoiceStudio, aprire Claude Code nel repo).

- [ ] **Step 1:** `.mcp.json` = `{"mcpServers": {"voicestudio": {"type": "http", "url": "http://localhost:3900/mcp/", "headers": {"X-OmniVoice-Client-Id": "video-creation"}}}}`. `pyproject.toml` con package `videocreation`, `requires-python >=3.10`, extra dev `pytest`. `.gitignore`: `progetti/**`, `!progetti/README.md`, `!progetti/esempio/`, `!progetti/esempio/testo.md`, `__pycache__/`, `.venv/`, `.pytest_cache/`.
- [ ] **Step 2: Write failing tests** in `tests/test_env_file.py`:
  - `test_creates_file_with_0600`: file inesistente → contiene `OMNIVOICE_MCP_OUTPUT_MODE=files\n`, `stat.S_IMODE(mode) == 0o600`.
  - `test_preserves_other_keys_and_replaces_existing`: file `HF_TOKEN=abc\nOMNIVOICE_MCP_OUTPUT_MODE=resources\n# nota\n` → dopo upsert `{"OMNIVOICE_MCP_OUTPUT_MODE": "files"}` le righe sono `["HF_TOKEN=abc", "OMNIVOICE_MCP_OUTPUT_MODE=files", "# nota"]` (ordine preservato).
  - `test_quotes_paths_with_spaces_and_apostrophes`: valore `/Users/fred/Video Lavoro/l'estate` → riga `OMNIVOICE_MCP_BASE_PATH='/Users/fred/Video Lavoro/l\'estate'` (stessa codifica di VoiceStudio: valori fuori da `[A-Za-z0-9_\-./:@%+=,~]` tra apici singoli con `\\` e `\'` escapati).
  - `test_rejects_newlines`: valore con `\n` → `ValueError`.
- [ ] **Step 3:** Run `pytest tests/test_env_file.py -v` → FAIL (module missing).
- [ ] **Step 4:** Implement `upsert_env` and `scripts/setup_voicestudio.py` (crea la dir padre, scrittura atomica via file temporaneo + `os.replace`, poi `chmod 0600`).
- [ ] **Step 5:** Run `pytest -v` → PASS. Run `python scripts/setup_voicestudio.py --env-file /tmp/x/env` → stampa i passi e il file contiene le due chiavi.
- [ ] **Step 6:** Commit `feat: config MCP VoiceStudio e setup file env`.

### Task 2: Sottotitoli social dalla voce generata

**Files:**
- Create: `videocreation/voicestudio.py`, `videocreation/subtitles.py`
- Test: `tests/test_subtitles.py`, `tests/test_voicestudio.py`

**Interfaces:**
- Produces:
  - `class VoiceStudioError(Exception)` (messaggio già in italiano, pronto per l'utente).
  - `transcribe_words(audio: Path, base_url: str = "http://127.0.0.1:3900", language: str | None = None, api_key: str | None = None, timeout: float = 600) -> dict` — restituisce il JSON `verbose_json` (multipart costruito con stdlib, `urllib.request`).
  - `words_to_srt(words: list[dict], max_words: int = 4, max_chars: int = 28, max_gap: float = 0.6) -> str`
  - `transcript_to_srt(result: dict) -> str` — usa `words` se non vuoto, altrimenti `segments`; `""` se entrambi vuoti.

- [ ] **Step 1: Write failing tests** `tests/test_subtitles.py`:
  - `test_groups_words_in_short_cues`: 9 parole consecutive (0.3 s ciascuna, senza pause) con `max_words=4` → 3 cue (4+4+1); prima cue `1\n00:00:00,000 --> 00:00:01,200\n…`.
  - `test_breaks_on_pause`: pausa di 1.0 s tra parola 2 e 3 → nuova cue alla parola 3 anche se `max_words` non raggiunto.
  - `test_breaks_on_max_chars`: parole lunghe che superano 28 caratteri → spezzate prima.
  - `test_timestamp_format_over_one_hour`: `3725.5` → `01:02:05,500`.
  - `test_falls_back_to_segments`: `{"words": [], "segments": [{"start": 0, "end": 2.5, "text": " Ciao a tutti "}]}` → una cue `Ciao a tutti` 0→2.5.
  - `test_empty_transcript`: `{"text": "", "words": [], "segments": []}` → `""`.
- [ ] **Step 2: Write failing tests** `tests/test_voicestudio.py` con un `http.server` locale in thread su porta libera:
  - `test_sends_multipart_with_word_granularity`: il server registra la richiesta; assert path `/v1/audio/transcriptions`, body contiene `name="response_format"` → `verbose_json`, `name="timestamp_granularities[]"` → `word` e `segment`, e il nome file.
  - `test_bearer_when_api_key`: con `api_key="k"` header `Authorization: Bearer k`.
  - `test_connection_refused_message`: porta chiusa → `VoiceStudioError` il cui messaggio contiene `"Apri VoiceStudio"`.
  - `test_409_asr_missing_message`: server risponde 409 → messaggio contiene `"modello di trascrizione"`.
- [ ] **Step 3:** Run `pytest tests/test_subtitles.py tests/test_voicestudio.py -v` → FAIL.
- [ ] **Step 4:** Implement both modules. Base URL default letto da env `VOICESTUDIO_URL`, API key da env `OMNIVOICE_API_KEY` se non passata.
- [ ] **Step 5:** Run → PASS.
- [ ] **Step 6:** Commit `feat: sottotitoli brevi da trascrizione VoiceStudio`.

### Task 3: Montaggio FFmpeg (`scripts/monta.py`)

**Files:**
- Create: `videocreation/media.py`, `videocreation/montaggio.py`, `scripts/monta.py`
- Test: `tests/test_montaggio.py` (integrazione con ffmpeg reale su clip sintetiche; `pytest.skip` se `ffmpeg` manca)

**Interfaces:**
- Consumes: `transcribe_words`, `transcript_to_srt`, `VoiceStudioError` (Task 2).
- Produces:
  - `probe(path: Path) -> MediaInfo` con `@dataclass MediaInfo: duration: float; has_audio: bool; width: int | None; height: int | None` (via `ffprobe -show_streams -show_format -of json`).
  - `build_command(video: Path, voce: Path, out: Path, *, info_video: MediaInfo, durata_voce: float, musica: Path | None = None, srt_name: str | None = None, audio_originale: str = "abbassa", volume_musica: float = 0.25) -> list[str]` — `audio_originale` ∈ `{"abbassa", "togli"}`; `srt_name` è un nome file relativo alla cwd di esecuzione.
  - `monta(video: Path, voce: Path, *, musica: Path | None = None, sottotitoli: bool = True, audio_originale: str = "abbassa", out_dir: Path | None = None) -> tuple[Path, Path | None]` — restituisce (mp4, srt o None). `out_dir` default `video.parent / "out"`.
  - CLI: `python scripts/monta.py VIDEO VOCE [--musica FILE] [--no-sottotitoli] [--togli-audio-originale]`; stampa i percorsi finali; su `VoiceStudioError` stampa il messaggio e suggerisce `--no-sottotitoli`, exit 2.

Comportamento del filtro (decisioni da rispettare):
- Fondo = audio originale (se `has_audio` e non `togli`) mixato con musica (`-stream_loop -1`, `volume=volume_musica`); se non c'è fondo, l'audio è solo la voce.
- Ducking: `sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400` con la voce come sidechain (voce duplicata con `asplit`), poi `amix=inputs=2:duration=first:normalize=0` (fondo, voce), `alimiter=limit=0.95`.
- Durata output = `max(video, voce + 0.5)`; se la voce supera il video: `tpad=stop_mode=clone:stop_duration=<diff>` e avviso su stderr. Fondo e voce `apad` + `-t <durata>`.
- Sottotitoli: `subtitles=<srt_name>:force_style='Fontname=Arial,FontSize=14,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=0,Alignment=2,MarginV=60'`. `monta()` scrive l'SRT in una `TemporaryDirectory` come `subs.srt`, esegue ffmpeg con `cwd` lì e percorsi assoluti per input/output, poi copia l'SRT in `out/<stem>_vo.srt`. Trascrizione vuota → niente sottotitoli + avviso.

- [ ] **Step 1: Write failing tests** (fixture che genera con ffmpeg: video 3 s 360x640 `testsrc` con audio `sine`, video 3 s muto, voce 2 s `sine=880`, voce 5 s, musica 1 s; `transcribe_words` monkeypatchato per restituire 3 parole):
  - `test_probe_detects_audio_and_size`: `has_audio` True/False sulle due clip, `width == 360`, `height == 640`, `duration ≈ 3.0 ± 0.1`.
  - `test_basic_mix_with_subtitles`: `monta(video, voce_2s)` → mp4 esiste, `probe(mp4).duration ≈ 3.0 ± 0.2`, `has_audio`, SRT esiste e contiene `-->`.
  - `test_silent_video` (Review Focus 1): video muto + voce → output ha audio.
  - `test_voice_longer_than_video` (RF 2): voce 5 s su video 3 s → durata output ≈ 5.5 ± 0.2.
  - `test_odd_paths` (RF 3): file copiati in `tmp/l'estate è qui/clip 1.mp4` → mp4 prodotto con sottotitoli.
  - `test_short_music_loops` (RF 4): musica 1 s → durata output ≈ 3.0 ± 0.2 e stream audio presente fino alla fine (`ffmpeg -ss 2.5 -t 0.4 … volumedetect` mean_volume > -60 dB).
  - `test_togli_audio_originale`: `build_command(..., audio_originale="togli")` non contiene `[0:a]` nel filtergraph.
  - `test_cli_voicestudio_down` (RF 5): `transcribe_words` solleva `VoiceStudioError("Apri VoiceStudio…")` → `main([...])` ritorna 2 e stderr contiene `--no-sottotitoli`.
- [ ] **Step 2:** Run `pytest tests/test_montaggio.py -v` → FAIL.
- [ ] **Step 3:** Implement `media.py`, `montaggio.py`, `scripts/monta.py` (`main(argv: list[str] | None = None) -> int`).
- [ ] **Step 4:** Run `pytest -v` → all PASS. Esegui a mano `python scripts/monta.py` su una clip di test e guarda un fotogramma (`ffmpeg -ss 1 -frames:v 1 frame.png`) per verificare che i sottotitoli siano leggibili in basso al centro.
- [ ] **Step 5:** Commit `feat: montaggio voce, ducking e sottotitoli`.

### Task 4: Skill per Claude, guida doppiaggio, README

**Files:**
- Create: `.claude/skills/voce-clonata/SKILL.md`, `.claude/skills/voiceover/SKILL.md`, `docs/doppiaggio.md`, `README.md`, `CLAUDE.md`
- Test: `tests/test_docs.py`

**Interfaces:**
- Consumes: `scripts/setup_voicestudio.py` (Task 1), `scripts/monta.py` CLI (Task 3), tool MCP `check_health`, `clone_voice`, `generate_speech`, `list_voices`.

Contenuto richiesto:
- `voce-clonata` (frontmatter `name: voce-clonata`, `description` che scatta su "clona la mia voce", "voce predefinita"): registrazione 10–30 s pulita in `progetti/_voce/riferimento.wav` (consigli: stanza silenziosa, tono naturale, niente musica) → `check_health` → `clone_voice(name=..., ref_audio_path="_voce/riferimento.wav", ref_text=<trascrizione se nota>, language="it")` → `curl -X PUT http://127.0.0.1:3900/api/mcp/bindings -H 'Content-Type: application/json' -d '{"client_id":"video-creation","label":"video-creation","profile_id":"<id>"}'` → verifica con `GET` e un `generate_speech` di prova. Ricorda: clonare solo voci con consenso.
- `voiceover` (scatta su "voice-over", "narrazione", "metti la mia voce sul video"): input = cartella `progetti/<nome>/` con video e `testo.md` (o testo in chat) → se chiesto, adatta il testo alla durata del video (≈ 2.5 parole/s in italiano) e allo stile social (frasi brevi, hook nei primi 2 s) → `check_health` → `generate_speech(text=..., language="it")` (niente `profile_id`: usa il binding) → `mv` di `output_path` in `progetti/<nome>/voce.wav` → `python scripts/monta.py <video> progetti/<nome>/voce.wav [--musica ...]` → riporta i percorsi e la durata. Se `generate_speech` restituisce `wav_base64` invece di `output_path`, fermati e rimanda al setup (`OMNIVOICE_MCP_OUTPUT_MODE` non attivo). Per testi lunghi (> ~600 caratteri) genera per paragrafi e concatena con `ffmpeg -f concat`.
- `docs/doppiaggio.md`: passi nell'app (Dub → sorgente file/URL → lingua parlata/speaker → lingua target e traduttore → modalità: **Autofit** default per i social, **Cinematic** per contenuti curati → revisione segmenti, voce = profilo clonato → generare → export MP4 con musica di fondo mantenuta + SRT; sottotitoli bruciati opzionali). Nota: per clip con tagli rapidi preferire Autofit; esportare uno ZIP per lingua se servono più lingue.
- `README.md`: cosa fa; prerequisiti (VoiceStudio su Mac Apple Silicon, `brew install ffmpeg`, Python ≥ 3.10, Claude Code); setup in 4 passi (installa VoiceStudio e scarica un modello TTS + uno di trascrizione → `python scripts/setup_voicestudio.py` → riavvia VoiceStudio → apri Claude Code nel repo e approva il server `voicestudio`); esempi di richieste a Claude; uso diretto di `monta.py`; risoluzione problemi (porta 3900, `wav_base64` in output, 409 ASR).
- `CLAUDE.md` breve: struttura repo, skill disponibili, `pytest` per i test, lingua italiana per l'utente.

- [ ] **Step 1: Write failing test** `tests/test_docs.py`: `test_mcp_json_valid` (JSON valido, url `http://localhost:3900/mcp/`, header client id `video-creation`); `test_skills_have_frontmatter` (ogni `.claude/skills/*/SKILL.md` inizia con `---`, ha `name:` uguale al nome cartella e `description:`); `test_readme_mentions_setup` (README contiene `setup_voicestudio.py` e `monta.py`).
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Scrivi i file.
- [ ] **Step 4:** Run `pytest -v` → all PASS.
- [ ] **Step 5:** Commit `docs: skill voiceover e voce clonata, guida doppiaggio, README`.
