# Doppiare un video con VoiceStudio

Il doppiaggio (video già parlato → altra lingua, con la tua voce) si fa nell'app
VoiceStudio: separa voce e musica e adatta i tempi meglio di uno script.
Claude qui non interviene; per un voice-over *nuovo* su un video usa la skill
`voiceover` (chiedi a Claude "fai il voice-over di …").

## Passi

1. **Apri Dub** (dalla barra laterale o cercando "Dub").
2. **Sorgente**: trascina il video (o incolla un URL e premi *Ingest*).
   - Lingua parlata: lascia *Auto* o scegli Italiano.
   - Numero di speaker: 1 per i tuoi video a camera; di più per interviste.
   - Se hai già i sottotitoli giusti, importa l'`.srt`: salti la trascrizione.
3. **Attendi** preparazione e trascrizione.
4. **Lingua di destinazione e traduttore**.
   - Traduttore: *Agent* o *API* (LLM) danno il testo più naturale; *Google*, *Argos* o
     *NLLB* vanno bene per bozze veloci.
5. **Modalità di qualità**
   - **Autofit** — scelta predefinita per i social: adatta la durata delle frasi ai tempi
     originali, regge bene i tagli rapidi.
   - **Cinematic** — per contenuti curati dove conta l'interpretazione.
   - *Fast* — solo per un'anteprima.
6. **Revisione**: leggi la traduzione segmento per segmento. Accorcia le frasi troppo
   lunghe (le lingue come il tedesco o il francese si allungano). Imposta come voce il
   tuo **profilo clonato** (creato con la skill `voce-clonata`).
7. **Genera**, poi ascolta l'anteprima.
8. **Esporta**
   - Video MP4 **con la musica di fondo mantenuta** (background mixing).
   - Sottotitoli `.srt` a parte (utile per caricarli sulla piattaforma) e, se vuoi,
     bruciati nel video.
   - Più lingue: esporta lo ZIP per lingua (contiene tracce e segmenti).

Salva i risultati in `progetti/<nome>/out/` per tenerli insieme agli altri file del video.

## Consigli per i social

- Clip con tagli serrati: Autofit e frasi tradotte brevi; meglio riscrivere che
  accelerare la voce.
- Controlla nomi propri, marchi e numeri nella revisione: sono gli errori più frequenti.
- Il primo secondo conta: se la traduzione dell'hook è debole, riscrivila a mano.
- Pubblica lo stesso video in più lingue come post separati o con la funzione
  multi-traccia audio della piattaforma, se disponibile.
