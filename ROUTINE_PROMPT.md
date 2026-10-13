Installa le dipendenze con `python -m pip install -q -r requirements.txt` (usa `python -m pip`, non `pip`: nell'ambiente cloud `pip` installa per un altro Python). Poi esegui `python -m podcast_digest.main config.json > digest.json` nella root del repo e leggi `digest.json`. Il comando può richiedere 10-15 minuti: scarica e trascrive l'audio di ogni episodio.

Se "status" è "error": scrivi in `email_body.txt` un breve testo in italiano che spiega che il controllo giornaliero è fallito, con il messaggio di errore ricevuto. Invialo con `python -m podcast_digest.send_email config.json "Podcast Digest - controllo fallito" email_body.txt`.

Se "status" è "ok", "episodes" è vuota e "warnings" è vuota: non fare nulla, non inviare nessuna email.

Se "status" è "ok", "episodes" è vuota ma "warnings" non è vuota: invia un'email con solo gli avvisi, oggetto "Podcast Digest - avviso".

Altrimenti scrivi in `email_body.txt` un'email in italiano così strutturata:
1. Ogni elemento di "warnings", ciascuno su una riga che inizia con "⚠️".
2. Una riga "Trascrizioni: X su Y episodi", dove X è il numero di episodi con content_source "transcript" e Y il totale.
3. Se "feed_errors" non è vuota: una riga "Podcast non controllati oggi: " seguita dai nomi.
4. Gli episodi raggruppati per "podcast". Per ogni episodio: il titolo, un riassunto e il link "Ascolta su Spotify: <spotify_url>".

Per scrivere ogni riassunto leggi per intero il file indicato in "content_file" di quell'episodio.
- Se content_source è "transcript": riassunto di 2-4 frasi in italiano del contenuto reale dell'episodio (anche se l'episodio è in inglese). Ignora pubblicità e sponsor letti dentro l'episodio.
- Se content_source è "description_fallback": riassunto di 2-3 frasi dalle note dell'episodio, seguito da "(dalle note dell'episodio, non dalla trascrizione: <fallback_reason>)".
- Se content_source è "none": nessun riassunto, scrivi solo "(nessun contenuto disponibile: <fallback_reason>)". Non dedurre mai il contenuto dal solo titolo.

Infine invia l'email con `python -m podcast_digest.send_email config.json "🎧 Podcast del giorno" email_body.txt`.
