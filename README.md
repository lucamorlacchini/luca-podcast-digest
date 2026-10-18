# Podcast Digest

Digest quotidiano via email degli episodi usciti **il giorno precedente** dei podcast che segui su Spotify, con un breve riassunto per ciascuno ricavato dalla **trascrizione reale dell'audio**.

Repo privato personale — non collegato a nessun ambiente aziendale. Contiene di proposito credenziali reali in `config.json` (vedi [Sicurezza e credenziali](#sicurezza-e-credenziali)).

## Come funziona

Ogni giorno alle **6:00 (ora italiana)** una routine cloud schedulata (Claude Code Routines):

1. Clona questo repo e installa le dipendenze.
2. Esegue `python -m podcast_digest.main config.json`, che per ogni podcast in `podcasts.json`:
   - legge il **feed RSS pubblico** del podcast e prende gli episodi usciti **ieri** (fuso Europe/Rome);
   - scarica l'audio, lo comprime (mono 16 kHz Opus, ~7 MB/ora) e lo trascrive con **Whisper su Groq** (`whisper-large-v3-turbo`);
   - salva ogni trascrizione in `out/NN.txt` e stampa su stdout un JSON indice (episodi, fonte del contenuto, errori, avvisi).
3. L'agente della routine legge le trascrizioni, scrive l'email in italiano (raggruppata per podcast, 2-4 frasi per episodio, link "Ascolta su Spotify") e la invia con `python -m podcast_digest.send_email` via **Gmail API**.

Le istruzioni esatte dell'agente sono in [`ROUTINE_PROMPT.md`](ROUTINE_PROMPT.md) — se le modifichi, aggiorna anche la routine.

Se non ci sono episodi nuovi, **non viene inviata nessuna email**. Se il controllo fallisce, arriva una breve email di alert. Nessuno stato persistente tra un'esecuzione e l'altra.

## Perché non l'API di Spotify

L'API di Spotify serve solo a leggere la lista dei podcast seguiti e quali episodi hai già ascoltato — non dà accesso né all'audio né alle trascrizioni. Da febbraio 2026 richiede inoltre che il proprietario dell'app abbia **Spotify Premium** (account attuale: non Premium). Quindi la lista dei podcast è mantenuta a mano in `podcasts.json` e il contenuto arriva dai feed RSS pubblici, dove gli stessi episodi sono pubblicati con l'audio scaricabile. Conseguenze:

- **Nessun filtro "già ascoltato"**: il digest include tutti gli episodi nuovi.
- **Nuovi podcast seguiti su Spotify** vanno aggiunti a `podcasts.json` (nome + `feed_url`; il feed si trova cercando il podcast su `https://itunes.apple.com/search?media=podcast&term=<nome>`, campo `feedUrl`).
- **Podcast esclusivi Spotify** (senza feed pubblico) non sono supportati. Alla configurazione iniziale (13/10/2026) tutti i 45 podcast seguiti avevano un feed pubblico.

## Configurazione (`config.json`)

| Chiave | Uso |
|---|---|
| `google_client_id`, `google_client_secret`, `google_refresh_token` | OAuth Google, scope `gmail.send` (invio email) |
| `email_to`, `email_from` | destinatario / mittente |
| `groq_api_key` | lasciare vuoto: la chiave Groq va nella variabile d'ambiente `GROQ_API_KEY` dell'ambiente della routine (vedi Sicurezza) |
| `groq_key_expires` | facoltativo: data di scadenza della chiave, se ne ha una (l'email avvisa 2 giorni e 1 giorno prima). La chiave attuale (18/10/2026) non scade. |
| `start_date` | gli episodi usciti prima di questa data non vengono mai trascritti (evita costi su episodi vecchi) |

## Costi

Groq fattura ~0,04 $ per ora di audio. Sui 45 podcast seguiti, negli ultimi 30 giorni prima dell'avvio: ~14 episodi e ~7 ore di audio al giorno → ~0,27 $/giorno, ~8 $/mese. Il piano gratuito di Groq ha limiti orari/giornalieri sull'audio: se vengono superati, gli episodi in eccesso ricadono sulle note dell'episodio (motivo indicato nell'email) — in quel caso conviene attivare il piano a consumo su console.groq.com.

## Setup da zero

1. **Google Cloud** (progetto "Podcast Digest"): Gmail API abilitata, app OAuth "In production", client Desktop; refresh token ottenuto con lo scope `https://www.googleapis.com/auth/gmail.send` (vedi cronologia git per la procedura dettagliata).
2. **Groq**: chiave da console.groq.com → API Keys, da inserire come variabile d'ambiente `GROQ_API_KEY` nell'ambiente cloud della routine (non in `config.json`).
3. **Ambiente cloud della routine con accesso di rete completo**: i file audio sono ospitati su decine di domini diversi (megaphone, spreaker, cloudfront, redirect di tracking come podtrac...), quindi un allowlist di domini non è praticabile. Senza accesso completo i download falliscono.
4. **Routine** (`RemoteTrigger`/skill `schedule`): cron `0 5 * * *` (6:00 ora solare) / `0 4 * * *` (6:00 ora legale), `sources` → questo repo, `allowed_tools: ["Bash", "Write", "Read"]`, prompt = `ROUTINE_PROMPT.md`.

## Manutenzione

- **Cambio ora legale/solare:** il cron è in UTC. Ora solare (da fine ottobre): `0 5 * * *`. Ora legale (da fine marzo): `0 4 * * *`. Va aggiornato a mano.
- **Scadenza chiave Groq:** aggiorna `GROQ_API_KEY` nell'ambiente della routine e `groq_key_expires` in `config.json`. Se la chiave è revocata, l'email lo segnala in cima.
- **Un feed smette di funzionare:** compare in "Podcast non controllati oggi" nell'email; cerca il nuovo `feedUrl` come sopra.

## Sicurezza e credenziali

`config.json` contiene credenziali reali ed è **committato di proposito**: è l'unico modo per la routine cloud di leggerle, dato che ogni run parte da un checkout fresco. Accettabile solo perché il repo è **privato**, a **uso personale** e non collegato ad ambienti aziendali. GitHub può bloccare i push che contengono segreti riconosciuti (push protection): va autorizzato esplicitamente.

Eccezione: **la chiave Groq non va mai nel repo.** La prima chiave, committata il 13/10/2026, è stata segnalata come esposta (GitHub secret scanning, GitGuardian) e dal 17/10/2026 risultava revocata (`401 Invalid API Key`), quindi niente trascrizioni. Ora il codice legge `GROQ_API_KEY` dalle variabili d'ambiente (con `groq_api_key` in `config.json` solo come ripiego per test locali, da non committare).

## Storia

Fino al 13/10/2026 il digest riguardava i video YouTube dei canali seguiti (trascrizioni via TranscriptAPI.com, poi rimasto senza crediti). Il codice è nella cronologia git (`youtube_digest/`).
