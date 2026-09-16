# DONACIBO — Specifica completa del progetto

## 1. Panoramica
Web app **Flask** per la gestione delle *schede di adesione* alla raccolta alimentare nelle scuole. Permette login con ruoli, importazione dati da Excel/CSV, modifica inline dei dati nella dashboard, note per singolo campo, filtro per istituto e generazione di report PDF.

- **Lingua UI**: italiano
- **Ruoli**: `admin` (importa ed elimina) e `volontario` (solo consultazione/modifica)
- **Database**: SQLite (`instance/donacibo.db`)

## 2. Stack tecnologico
`Flask==3.0.0`, `Flask-SQLAlchemy==3.1.1`, `Flask-Login==0.6.3`, `pandas`, `openpyxl`, `werkzeug`, `reportlab`. Frontend in HTML/CSS/JS puro con template Jinja2.

## 3. Struttura file
```
donacibo_project/
├── app.py                 # app Flask, modelli, route
├── requirements.txt
├── .gitignore
├── README.md
├── instance/donacibo.db   # creato automaticamente
├── static/donacibo.png    # logo
└── templates/
    ├── login.html
    ├── upload.html
    └── dashboard.html
```

## 4. Configurazione applicazione
```python
app.config['SECRET_KEY'] = 'donacibo-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///donacibo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
login_manager.login_view = 'login'
```

## 5. Modelli database

**User** (`user`): `id`, `username` (unico), `password_hash`, `role` ('admin'|'volontario'). Eredita `UserMixin`.

**SchedaAdesione** (`scheda_adesione`):
- `id`
- `nome_cognome_referente` (str200, not null)
- `telefono_email` (str200, not null)
- `nome_istituto` (str200, not null)
- `nome_scuola` (str200, not null)
- `grado` (str50, not null)
- `indirizzo` (str300, not null)
- `comune` (str100, not null)
- `data_inizio_raccolta` (Date, null)
- `numero_classi_partecipanti` (Int, null)
- `numero_alunni_partecipanti` (Int, null)
- `note` (Text, null)
- `numero_presentazioni` (Int, default 0)
- `consegna_materiale` (str100, default '')
- `presentazioni` (str100, default '')
- `ritiro_pacchi` (str100, default '')
- `kg_raccolti` (Float, default 0.0)
- relazione `field_notes` → FieldNote con `cascade='all, delete-orphan'`

**FieldNote** (`field_note`): `id`, `scheda_id` (FK scheda_adesione.id), `field_name` ('consegna_materiale'|'presentazioni'|'ritiro_pacchi'), `note` (Text, default ''), `checkbox_value` (Bool, default False). Serve a memorizzare nota + checkbox per ogni singolo campo della scheda.

## 6. Route

| Metodo | Path | Regole | Comportamento |
|---|---|---|---|
| GET | `/` | — | redirect a dashboard se autenticato, altrimenti login |
| GET/POST | `/login` | — | verifica `check_password_hash`; su successo `login_user` + redirect dashboard; altrimenti flash "Credenziali non valide" |
| GET | `/logout` | login | `logout_user`, redirect login |
| GET | `/dashboard` | login | carica tutte le schede; per ogni scheda e per i 3 campi crea al volo la FieldNote mancante e l'attributo `field_note_<campo>`; render dashboard con `schede` e `is_admin` |
| GET/POST | `/upload` | login + admin | legge Excel/CSV con pandas, crea una SchedaAdesione per riga, commit; validazione estensione `.xlsx/.xls/.csv` |
| POST | `/update/<id>` | login | aggiorna `numero_presentazioni`, `consegna_materiale`, `presentazioni`, `ritiro_pacchi`, `kg_raccolti`; imposta `checkbox_value` delle FieldNote in base alla presenza di `<campo>_check` nel form |
| GET | `/api/scheda/<id>` | login | JSON dettagli scheda |
| POST | `/update_note/<id>` | login | aggiorna `scheda.note` |
| POST | `/update_field_note/<id>/<field_name>` | login | trova/crea FieldNote e salva `note` |
| POST | `/delete/<id>` | login + admin | elimina la scheda |
| GET/POST | `/report` | login | genera PDF |

### Report PDF (`/report`)
- `filter_text` da form (POST) o query string (GET).
- Filtro applicato confrontando `filter_text` (lowercase) con i valori dei campi `consegna_materiale`, `presentazioni`, `ritiro_pacchi`.
- PDF (reportlab, `landscape(A4)`): titolo "Report DONACIBO - <gg/mm/aaaa>", eventuale riga "Filtro: ...", tabella con colonne:
  **Istituto, Scuola, Grado, N° Presentazioni, Consegna Materiale, Presentazioni, Ritiro Pacchi**.
- Ritorna il file come download `report_donacibo_<timestamp>.pdf`.

### Inizializzazione (`init_db`)
`db.create_all()` + creazione utenti default se assenti:
- `admin` / `admin123` (role admin)
- `volontario` / `volontario123` (role volontario)

Entry point: `if __name__ == '__main__': init_db(); app.run(debug=True)`.

## 7. Formato file di importazione
Colonne riconosciute (nomi esatti, case-sensitive) dalle righe:

`nome e cognome referente`, `telefono / email del referente`, `nome istituto`, `nome scuola`, `grado`, `indirizzo`, `comune`, `data inizio raccolta`, `numero classi aderenti al progetto`, `numero alunni partecipanti`, `note`, `numero presentazioni`, `consegna materiale`, `presentazioni`, `ritiro pacchi`, `kg raccolti`.

Le date sono convertite con `pd.to_datetime(...).date()`; i valori `NaN`/`'nan'` sono trattati come stringa vuota.

## 8. Template e UI

### login.html
Card centrata su sfondo con gradiente blu (`#1e3a5f`→`#2c5282`), logo (`donacibo.png`, 360px), sottotitolo "Gestione raccolta alimentare nelle Scuole", form username/password, flash messages.

### upload.html
Header con logo (220px), "DONACIBO", pulsanti Dashboard/Logout. Card con area di upload (bordo tratteggiato) e anteprima file via JS `showFileInfo()`. Form `multipart/form-data` con campo `file`, accetta `.xlsx,.xls,.csv`.

### dashboard.html
- **Header**: logo (220px), username (ruolo), pulsante "Carica File" (solo admin), Logout.
- **Sezione filtri**: input "Filtra per Istituto" (`onkeyup=filterTable()`), pulsanti Filtra/Cancella; form report con input `filter_text` e pulsante "Report PDF".
- **Tabella** (colonne): Istituto, Scuola, Grado, **N° Presentazioni** (readonly, sfondo grigio), Consegna Materiale, Presentazioni, Ritiro Pacchi, Kg Raccolti, Dettagli, azioni.
- **Righe**: `<tr data-istituto="{{ scheda.nome_istituto }}">`.
- **Form per riga (IMPORTANTE)**: i form di modifica **non** circondano le `<tr>` (HTML non valido dentro `<tbody>`); sono definiti come form nascosti **prima della tabella**, con `id="rowform-<id>"`, `action=/update/<id>`, `method=POST`. Ogni input/checkbox/pulsante Salva è collegato via attributo `form="rowform-<id>"`.
- **Campi editabili** `consegna_materiale`/`presentazioni`/`ritiro_pacchi`: ricevono la classe `is-populated` quando il valore è non vuoto e diverso da `'nan'`. Ogni campo ha anche una checkbox e un pulsante 📝 che apre il modal note del campo.
- **Pulsanti**: Salva (submit), Dettagli (apre modal), Delete (admin, con `confirm`).
- **Modal**: `detailModal` (dettagli scheda da oggetto JS `schedeData`) e `fieldNoteModal` (gestione nota campo).
- **JS**: `openModal`, `closeModal`, `filterTable`, `clearFilter`, `deleteScheda`, `openFieldNoteModal`, `closeFieldNoteModal`.

`filterTable()` (comportamento corretto):
```js
const filterValue = document.getElementById('filterIstituto').value.trim().toLowerCase();
document.querySelectorAll('tbody tr').forEach(row => {
    const istituto = (row.getAttribute('data-istituto') || '').trim().toLowerCase();
    row.style.display = filterValue === '' || istituto.includes(filterValue) ? '' : 'none';
});
```

### Stile / palette
- Tema blu business: `#1e3a5f`, `#2c5282` (header con gradiente), testo `#4a5568`.
- Flash: errore `#fed7d7`/`#c53030`; successo `#c6f6d5`/`#2f855a`, bordo `#68d391`.
- **Verde di stato** (`#48bb78` bordo, `#2f855a` testo): usato **solo come bordo, mai come sfondo pieno**.
  - Campi popolati e pulsante Salva: bordo **5px**.
  - Pulsanti note (📝 con nota, "Salva Note"): bordo **3px**.
  - Hover: sfondo tenue `#e8f7ee` e bordo `#2f855a`.
- Pulsante **Dettagli**: bordo blu 5px, sfondo bianco, testo `#2b6cb0`.
- Pulsante **Delete**: sfondo neutro `#e2e8f0`, testo `#4a5568`.

## 9. Setup e avvio
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Accedere a `http://localhost:5000`. Credenziali default: `admin/admin123`, `volontario/volontario123`.

## 10. Note implementative chiave
1. **Form e tabelle**: mai mettere `<form>` dentro `<tbody>` attorno a `<tr>`; usare l'attributo HTML `form` per associare i controlli a un form esterno.
2. **Filtro istituto**: gestire anche il caso di `data-istituto` vuoto (non usare `if (istituto)` che salta la riga).
3. I valori `'nan'` dai file Excel vanno normalizzati a stringa vuota sia in import sia in visualizzazione.
4. Admin = può caricare file ed eliminare schede; volontario = sola modifica/consultazione.
