Installa le dipendenze con `python -m pip install -q -r requirements.txt` (usa `python -m pip`, non `pip`: nell'ambiente cloud `pip` installa per un altro Python). Poi esegui `python -m podcast_digest.main config.json > digest.json` nella root del repo e leggi `digest.json`. Esegui questo comando in primo piano (non in background) con timeout 600000 e attendi che finisca: scarica e trascrive l'audio di ogni episodio e di solito richiede 3-6 minuti.

Se "status" è "error": scrivi in `email_body.txt` un breve testo in italiano che spiega che il controllo giornaliero è fallito, con il messaggio di errore ricevuto. Invialo con `python -m podcast_digest.send_email config.json "Podcast Digest - controllo fallito" email_body.txt`.

Se "status" è "ok", "episodes" è vuota e "warnings" è vuota: non fare nulla, non inviare nessuna email.

Se "status" è "ok", "episodes" è vuota ma "warnings" non è vuota: invia un'email con solo gli avvisi, oggetto "Podcast Digest - avviso".

Altrimenti scrivi in `email_body.txt` un'email in italiano così strutturata:
1. Ogni elemento di "warnings", ciascuno su una riga che inizia con "⚠️".
2. Una riga "Trascrizioni: X su Y episodi", dove X è il numero di episodi con content_source "transcript" e Y il totale.
3. Se "feed_errors" non è vuota: una riga "Podcast non controllati oggi: " seguita dai nomi.
4. Gli episodi raggruppati per "podcast". Per ogni episodio: il titolo, un riassunto e il link "Ascolta su Spotify: <spotify_url>".

Scrivi ogni paragrafo e ogni punto elenco su una sola riga, senza andare a capo a metà frase: l'email viene impaginata in automatico.

Per scrivere ogni riassunto leggi per intero il file indicato in "content_file" di quell'episodio.
- Se content_source è "transcript": riassunto in italiano del contenuto reale dell'episodio (anche se l'episodio è in inglese), così strutturato:
  - un paragrafo di 5-6 frasi che dice di cosa parla l'episodio, chi parla (conduttori, ospiti), il contesto e la tesi o il messaggio principale;
  - poi i punti chiave come elenco puntato (righe che iniziano con "- "), in base a "content_words": 4-5 punti sotto le ~2.500 parole, 7-9 punti fino a ~8.000 parole, 10-12 punti oltre. Ogni punto è di 1-2 frasi concrete: fatti, numeri, nomi, argomentazioni, esempi e opinioni degli ospiti, con chi sostiene cosa quando conta. Evita frasi generiche come "si parla di economia".
  - Nelle rassegne stampa e nei notiziari (più notizie diverse nello stesso episodio) fai un punto per ogni notizia.
  - Ignora pubblicità e sponsor letti dentro l'episodio. Riporta solo ciò che è detto nella trascrizione, senza aggiungere conoscenze esterne.
- Se content_source è "description_fallback": riassunto di 2-3 frasi dalle note dell'episodio, seguito da "(dalle note dell'episodio, non dalla trascrizione: <fallback_reason>)".
- Se content_source è "none": nessun riassunto, scrivi solo "(nessun contenuto disponibile: <fallback_reason>)". Non dedurre mai il contenuto dal solo titolo.

Infine invia l'email con `python -m podcast_digest.send_email config.json "🎧 Podcast del giorno" email_body.txt`.

Non fare commit né push: i file generati (`digest.json`, `email_body.txt`, `out/`) sono temporanei e ignorati da git.
