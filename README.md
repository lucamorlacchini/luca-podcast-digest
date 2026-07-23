# Podcast Digest

Digest quotidiano via email dei video pubblicati oggi dai canali YouTube seguiti.
Repo privato personale — non collegato a nessun ambiente aziendale.

Vedi `config.example.json` per le variabili richieste in `config.json` (mai committare `config.json` in un repo pubblico — questo repo lo fa intenzionalmente perché è privato e a uso personale).

## Limitazioni note

- **Nessun filtro "già visto".** L'API di YouTube non espone la cronologia di visione (rimossa dal 2016) — il digest include tutti i video nuovi di oggi dai canali seguiti, anche se già visti.
- **Trascrizione reale spesso non disponibile.** Nel collaudo del 23/07/2026, 0 video su 44 hanno ottenuto una trascrizione reale (tutti fallback su descrizione) — le richieste a YouTube per il contenuto dei sottotitoli risultavano bloccate/vuote da questo ambiente, non per assenza di sottotitoli sui video stessi. Da verificare se il comportamento cambia sull'infrastruttura cloud dove gira la routine schedulata.
