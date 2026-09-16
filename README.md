# DONACIBO - Sistema di Gestione Raccolta Alimentare

Sistema web per la gestione delle schede di adesione alla raccolta alimentare.

## Caratteristiche

- Gestione schede di adesione
- Importazione dati da file Excel/CSV
- Tracking di presentazioni, consegne materiali e ritiri pacchi
- Sistema di note per ogni campo
- Generazione report PDF
- Gestione utenti (admin/volontario)
- Interfaccia responsive con design business

## Tecnologie

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript
- **Librerie**: 
  - Flask-SQLAlchemy (ORM)
  - Flask-Login (Autenticazione)
  - pandas (Gestione dati)
  - reportlab (Generazione PDF)

## Installazione

1. Clona il repository:
```bash
git clone <repository-url>
cd donacibo_project
```

2. Crea un ambiente virtuale:
```bash
python -m venv venv
source venv/bin/activate  # Su Windows: venv\Scripts\activate
```

3. Installa le dipendenze:
```bash
pip install -r requirements.txt
```

4. Configura le variabili d'ambiente (opzionale):
```bash
# Crea un file .env con:
SECRET_KEY=la-tua-secret-key
```

## Avvio

1. Avvia l'applicazione:
```bash
python app.py
```

2. Accedi a http://localhost:5000

## Credenziali Default

- **Admin**: username: `admin`, password: `admin123`
- **Volontario**: username: `volontario`, password: `volontario123`

⚠️ **Importante**: Cambia le password predefinite dopo il primo accesso.

## Struttura del Progetto

```
donacibo_project/
├── app.py                      # Applicazione Flask principale
├── requirements.txt            # Dipendenze Python
├── .gitignore                 # File ignorati da Git
├── README.md                  # Documentazione
├── static/                    # File statici
│   └── logo.svg              # Logo Donacibo
├── templates/                 # Template HTML
│   ├── dashboard.html        # Dashboard principale
│   ├── login.html            # Pagina di login
│   └── upload.html           # Pagina di upload file
└── donacibo.db               # Database SQLite (creato automaticamente)
```

## Funzionalità

### Dashboard
- Visualizzazione tutte le schede di adesione
- Modifica inline dei campi
- Gestione note per consegne, presentazioni e ritiri
- Filtri per istituto
- Visualizzazione dettagli scheda

### Upload
- Importazione dati da file Excel (.xlsx, .xls) o CSV
- Pulizia automatica dati esistenti
- Validazione formati file

### Report
- Generazione report PDF filtrabili
- Esportazione dati selezionati

## Formato File Excel/CSV

Il file di importazione deve contenere le seguenti colonne:
- nome e cognome referente
- telefono / email del referente
- nome istituto
- nome scuola
- grado
- indirizzo
- comune
- data inizio raccolta
- numero classi aderenti al progetto
- numero alunni partecipanti
- note
- numero presentazioni
- consegna materiale
- presentazioni
- ritiro pacchi
- kg raccolti

## Sicurezza

- Autenticazione utenti con Flask-Login
- Password hashed con werkzeug
- Ruoli utenti (admin/volontario)
- Accesso risorse protetto

## Licenza

Questo progetto è sviluppato per scopi di gestione raccolta alimentare.

## Supporto

Per problemi o domande, contatta l'amministratore di sistema.