# Podcast Digest

Digest quotidiano via email dei video pubblicati **il giorno precedente** dai canali YouTube che segui, con un breve riassunto per ciascuno (dal contenuto reale del video quando disponibile, altrimenti dalla descrizione ufficiale).

Repo privato personale — non collegato a nessun ambiente aziendale. Contiene di proposito credenziali reali in `config.json` (vedi [Sicurezza e credenziali](#sicurezza-e-credenziali)).

## Come funziona

Ogni giorno alle **6:00 (ora italiana)** una routine cloud schedulata (Claude Code Routines):

1. Clona questo repo e installa le dipendenze (`pip install -r requirements.txt`).
2. Esegue `python -m youtube_digest.main config.json`, che:
   - si autentica su Google con il refresh token salvato in `config.json`;
   - recupera l'elenco dei canali YouTube seguiti (`subscriptions.list`);
   - per ciascun canale, recupera i video pubblicati **ieri** (fuso orario Europe/Rome) dalla sua playlist "uploads" — non "oggi": la routine gira alle 6:00, quando la giornata corrente è iniziata da poche ore, quindi il target è sempre il giorno precedente per coprire un'intera giornata di uscite (vedi `youtube_digest/main.py`, funzione `run`);
   - per ogni video, prova a scaricarne la trascrizione (sottotitoli) con `youtube-transcript-api`; se non disponibile, usa la descrizione ufficiale del video come fallback;
   - stampa su stdout un JSON con la lista dei video e il relativo contenuto.
3. L'agente della routine legge quel JSON e compone il testo dell'email in italiano (raggruppata per canale, con riassunto di 2-3 frasi per video).
4. L'agente invia l'email eseguendo `python -m youtube_digest.send_email config.json "<oggetto>" <file-corpo>`, che manda il messaggio **direttamente via Gmail API** (non tramite un connettore MCP — vedi [perché](#perché-linvio-passa-da-uno-script-e-non-da-un-connettore-mcp)).

Se non ci sono video nuovi quel giorno, **non viene inviata nessuna email**. Se il controllo fallisce (es. token scaduto), viene inviata una breve email di alert invece del digest.

Non c'è nessuno stato persistente tra un'esecuzione e l'altra: tutto si ricalcola da zero ogni giorno.

## Struttura del progetto

```
luca-podcast-digest/
├── config.json                  # credenziali reali (committate di proposito, vedi sotto)
├── config.example.json          # template delle chiavi richieste, senza valori reali
├── requirements.txt
├── youtube_digest/
│   ├── youtube_client.py        # auth Google + canali seguiti + video di oggi
│   ├── transcript.py            # trascrizione video (fallback a None se non disponibile)
│   ├── main.py                  # orchestrazione: produce il JSON dei video di oggi
│   └── send_email.py            # invio email diretto via Gmail API
└── tests/                       # un file di test per ciascun modulo sopra
```

## Setup da zero (se va rifatto su un altro account)

1. **Repo GitHub privato** — già fatto per questo repo.
2. **Google Cloud Console** (progetto "Podcast Digest" — [console.cloud.google.com](https://console.cloud.google.com)):
   - Abilitare **YouTube Data API v3** e **Gmail API** (APIs & Services → Library).
   - **Google Auth Platform** → Pubblico: tipo utente **External**, stato **"In production"** (evita la scadenza del refresh token a 7 giorni prevista in stato "Testing" — per uno scope sensibile come questo, un'app personale non verificata funziona comunque cliccando oltre l'avviso "Google non ha verificato questa app").
   - **Client** → Crea client OAuth, tipo **Desktop app**. Serve `client_id` e `client_secret`.
3. **Autorizzazione OAuth una tantum** (scope combinati: lettura YouTube + invio Gmail):
   ```
   https://accounts.google.com/o/oauth2/v2/auth?client_id=CLIENT_ID&redirect_uri=http%3A%2F%2F127.0.0.1%3A8888%2Fcallback&response_type=code&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fyoutube.readonly%20https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fgmail.send&access_type=offline&prompt=consent
   ```
   Apri il link, accetta, e dall'URL di redirect (`http://127.0.0.1:8888/callback?code=...`) copia il valore di `code`. Poi scambialo per un refresh token:
   ```bash
   curl -X POST https://oauth2.googleapis.com/token \
     -d grant_type=authorization_code -d code=IL_CODE \
     -d redirect_uri=http://127.0.0.1:8888/callback \
     -u CLIENT_ID:CLIENT_SECRET
   ```
4. Compilare `config.json` (vedi `config.example.json` per le chiavi richieste: `google_client_id`, `google_client_secret`, `google_refresh_token`, `email_to`, `email_from`).
5. **Collegare GitHub a claude.ai** (https://claude.ai/customize/connectors) — necessario perché la routine cloud possa clonare un repo GitHub.
6. Creare la routine (`RemoteTrigger`/skill `schedule`): cron giornaliero, `sources` → questo repo, `allowed_tools: ["Bash", "Write"]`, nessun `mcp_connections` necessario.

## Manutenzione

- **Cambio ora legale/solare:** il cron della routine è fissato in UTC. È impostato per le 6:00 CEST (ora legale, `0 4 * * *`). Quando torna l'ora solare (fine ottobre), l'orario locale effettivo slitterà di un'ora (diventerà le 5:00) finché il cron non viene aggiornato manualmente a `0 5 * * *`.
- **Refresh token revocato/scaduto:** in teoria non scade mai con l'app in stato "In production" (vedi sopra), ma se Google dovesse richiedere la verifica dell'app in futuro, l'autorizzazione andrebbe rifatta seguendo lo step 3 sopra.
- **Aggiungere/rimuovere canali seguiti:** non serve toccare nulla qui — basta seguire/smettere di seguire un canale direttamente su YouTube, il digest si adatta automaticamente al giorno dopo.

## Sicurezza e credenziali

`config.json` contiene credenziali reali (Google client id/secret, refresh token) ed è **committato di proposito**, non in `.gitignore`: è l'unico modo per la routine cloud di leggerle a ogni esecuzione, dato che ogni run parte da un checkout fresco del repo senza altro stato persistente. Questo è accettabile solo perché:
- il repo è **privato** e a **uso personale** (nessun collaboratore);
- non è in nessun modo collegato ad ambienti aziendali.

GitHub blocca automaticamente (push protection) i push che contengono segreti riconosciuti, anche su repo privati: è normale, e per questo repo va autorizzato esplicitamente ("I'll fix it later") ogni volta che un push introduce o modifica una credenziale.

## Perché l'invio passa da uno script e non da un connettore MCP

La prima versione della routine usava il connettore MCP Microsoft 365 (Outlook) per comporre e inviare l'email direttamente dall'agente. In pratica, le chiamate agli strumenti del connettore fallivano in silenzio dentro le routine schedulate (bug noto della piattaforma, [issue #61027](https://github.com/anthropics/claude-code/issues/61027): le routine dovrebbero poter usare i connettori MCP senza chiedere conferma, ma di fatto la conferma viene richiesta e non arriva mai). Risultato: nessuna email arrivava mai.

La soluzione adottata è che `youtube_digest/send_email.py` invia l'email **direttamente via Gmail API**, usando le stesse credenziali OAuth Google già usate per leggere YouTube (con lo scope aggiuntivo `gmail.send`). L'agente della routine continua a comporre il testo dell'email (è bravo a scrivere un riassunto naturale), ma la consegna è affidata al nostro script, non a un tool MCP — bypassando così il bug alla radice.

## Limitazioni note

- **Nessun filtro "già visto".** L'API di YouTube non espone la cronologia di visione (rimossa dal 2016, nessuno scope OAuth la ripristina) — il digest include tutti i video nuovi di oggi dai canali seguiti, anche se già visti. L'email lo ricorda sempre con una riga fissa in testa.
- **Trascrizione reale spesso non disponibile.** Nel collaudo del 23/07/2026, 0 video su 44 hanno ottenuto una trascrizione reale (tutti fallback su descrizione) — le richieste a YouTube per il contenuto dei sottotitoli risultavano bloccate/vuote dall'ambiente di sviluppo usato per il test, non per assenza di sottotitoli sui video stessi (verificato anche su un video notoriamente sottotitolato). Da monitorare se il comportamento è diverso sull'infrastruttura cloud dove gira la routine in produzione.
- **Nessuna paginazione su `get_todays_videos`.** Per ogni canale si controllano solo i 10 upload più recenti (`youtube_digest/youtube_client.py`). Per un canale molto prolifico, se pubblica molti video nuovi *oggi* prima che la routine giri, i video di *ieri* possono uscire da questa finestra e non venire inclusi nel digest. Non ancora corretto (richiederebbe paginare finché non si esce dalla data target) — da tenere presente se noti assenze sospette da canali ad alta frequenza di pubblicazione.
