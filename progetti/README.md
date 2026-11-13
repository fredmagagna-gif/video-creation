# progetti/

Una cartella per video. Video, audio e risultati non vengono committati (vedi `.gitignore`).

```
progetti/
  _voce/riferimento.wav     registrazione per clonare la tua voce (una volta)
  <nome-video>/
    video.mp4               il video sorgente
    testo.md                il testo del voice-over
    musica.mp3              (opzionale) musica di sottofondo
    voce.wav                generata da VoiceStudio
    out/<nome>_vo.mp4       video finale
    out/<nome>_vo.srt       sottotitoli
```

Questa cartella è anche l'unica che VoiceStudio può leggere e scrivere
(`OMNIVOICE_MCP_BASE_PATH`): i WAV generati compaiono qui con un nome tipo
`a1b2c3.wav`, e Claude li sposta nella cartella del video.
