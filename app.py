from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
from datetime import datetime
import os
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = 'donacibo-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///donacibo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin' or 'volontario'

class SchedaAdesione(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_cognome_referente = db.Column(db.String(200), nullable=False)
    telefono_email = db.Column(db.String(200), nullable=False)
    nome_istituto = db.Column(db.String(200), nullable=False)
    nome_scuola = db.Column(db.String(200), nullable=False)
    grado = db.Column(db.String(50), nullable=False)
    indirizzo = db.Column(db.String(300), nullable=False)
    comune = db.Column(db.String(100), nullable=False)
    data_inizio_raccolta = db.Column(db.Date, nullable=True)
    numero_classi_partecipanti = db.Column(db.Integer, nullable=True)
    numero_alunni_partecipanti = db.Column(db.Integer, nullable=True)
    note = db.Column(db.Text, nullable=True)
    numero_presentazioni = db.Column(db.Integer, default=0)
    consegna_materiale = db.Column(db.String(100), default='')
    presentazioni = db.Column(db.String(100), default='')
    ritiro_pacchi = db.Column(db.String(100), default='')
    kg_raccolti = db.Column(db.Float, default=0.0)
    # Relazione con le note dei campi
    field_notes = db.relationship('FieldNote', backref='scheda', lazy=True, cascade='all, delete-orphan')

class FieldNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scheda_id = db.Column(db.Integer, db.ForeignKey('scheda_adesione.id'), nullable=False)
    field_name = db.Column(db.String(50), nullable=False)  # 'consegna_materiale', 'presentazioni', 'ritiro_pacchi'
    note = db.Column(db.Text, default='')
    checkbox_value = db.Column(db.Boolean, default=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Credenziali non valide', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    schede = SchedaAdesione.query.all()
    # Preload field notes for efficiency
    for scheda in schede:
        for field_name in ['consegna_materiale', 'presentazioni', 'ritiro_pacchi']:
            field_note = FieldNote.query.filter_by(scheda_id=scheda.id, field_name=field_name).first()
            if not field_note:
                # Create empty field note if it doesn't exist
                field_note = FieldNote(scheda_id=scheda.id, field_name=field_name)
                db.session.add(field_note)
                db.session.flush()  # Flush to get the ID if needed
            setattr(scheda, f'field_note_{field_name}', field_note)
    db.session.commit()
    return render_template('dashboard.html', schede=schede, is_admin=current_user.role == 'admin')

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if current_user.role != 'admin':
        flash('Accesso negato. Solo gli amministratori possono caricare file.', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Nessun file selezionato', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('Nessun file selezionato', 'error')
            return redirect(request.url)
        
        if file and file.filename.endswith(('.xlsx', '.xls', '.csv')):
            try:
                # Read file with pandas
                if file.filename.endswith('.csv'):
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(file)
                
                # Insert new data (append to existing)
                for _, row in df.iterrows():
                    scheda = SchedaAdesione(
                        nome_cognome_referente=row.get('nome e cognome referente', ''),
                        telefono_email=row.get('telefono / email del referente', ''),
                        nome_istituto=row.get('nome istituto', ''),
                        nome_scuola=row.get('nome scuola', ''),
                        grado=row.get('grado', ''),
                        indirizzo=row.get('indirizzo', ''),
                        comune=row.get('comune', ''),
                        data_inizio_raccolta=pd.to_datetime(row.get('data inizio raccolta')).date() if pd.notna(row.get('data inizio raccolta')) else None,
                        numero_classi_partecipanti=int(row.get('numero classi aderenti al progetto', 0)) if pd.notna(row.get('numero classi aderenti al progetto')) else None,
                        numero_alunni_partecipanti=int(row.get('numero alunni partecipanti', 0)) if pd.notna(row.get('numero alunni partecipanti')) else None,
                        note=row.get('note', ''),
                        numero_presentazioni=int(row.get('numero presentazioni', 0)) if pd.notna(row.get('numero presentazioni')) else 0,
                        consegna_materiale=str(row.get('consegna materiale', '')) if pd.notna(row.get('consegna materiale')) and str(row.get('consegna materiale', '')).lower() != 'nan' else '',
                        presentazioni=str(row.get('presentazioni', '')) if pd.notna(row.get('presentazioni')) and str(row.get('presentazioni', '')).lower() != 'nan' else '',
                        ritiro_pacchi=str(row.get('ritiro pacchi', '')) if pd.notna(row.get('ritiro pacchi')) and str(row.get('ritiro pacchi', '')).lower() != 'nan' else '',
                        kg_raccolti=float(row.get('kg raccolti', 0)) if pd.notna(row.get('kg raccolti')) else 0.0
                    )
                    db.session.add(scheda)
                
                db.session.commit()
                flash('File caricato con successo!', 'success')
                return redirect(url_for('dashboard'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Errore durante il caricamento: {str(e)}', 'error')
        else:
            flash('Formato file non supportato. Usa .xlsx, .xls o .csv', 'error')
    
    return render_template('upload.html')

@app.route('/update/<int:id>', methods=['POST'])
@login_required
def update_scheda(id):
    scheda = SchedaAdesione.query.get_or_404(id)
    
    # Update editable fields
    scheda.numero_presentazioni = int(request.form.get('numero_presentazioni', 0))
    scheda.consegna_materiale = request.form.get('consegna_materiale', '')
    scheda.presentazioni = request.form.get('presentazioni', '')
    scheda.ritiro_pacchi = request.form.get('ritiro_pacchi', '')
    scheda.kg_raccolti = float(request.form.get('kg_raccolti', 0))
    
    # Update field notes and checkboxes in the separate table
    for field_name in ['consegna_materiale', 'presentazioni', 'ritiro_pacchi']:
        field_note = FieldNote.query.filter_by(scheda_id=id, field_name=field_name).first()
        if not field_note:
            field_note = FieldNote(scheda_id=id, field_name=field_name)
            db.session.add(field_note)
        
        checkbox_value = f'{field_name}_check' in request.form
        field_note.checkbox_value = checkbox_value
    
    db.session.commit()
    flash('Dati aggiornati con successo!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/api/scheda/<int:id>')
@login_required
def get_scheda_details(id):
    scheda = SchedaAdesione.query.get_or_404(id)
    return jsonify({
        'nome_cognome_referente': scheda.nome_cognome_referente,
        'telefono_email': scheda.telefono_email,
        'indirizzo': scheda.indirizzo,
        'comune': scheda.comune,
        'data_inizio_raccolta': scheda.data_inizio_raccolta.strftime('%d/%m/%Y') if scheda.data_inizio_raccolta else 'N/A',
        'numero_classi_partecipanti': scheda.numero_classi_partecipanti if scheda.numero_classi_partecipanti else 'N/A',
        'numero_alunni_partecipanti': scheda.numero_alunni_partecipanti if scheda.numero_alunni_partecipanti else 'N/A',
        'note': scheda.note if scheda.note else '',
        'numero_presentazioni': scheda.numero_presentazioni
    })

@app.route('/update_note/<int:id>', methods=['POST'])
@login_required
def update_note(id):
    scheda = SchedaAdesione.query.get_or_404(id)
    scheda.note = request.form.get('note', '')
    db.session.commit()
    flash('Note aggiornate con successo!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/update_field_note/<int:id>/<field_name>', methods=['POST'])
@login_required
def update_field_note(id, field_name):
    scheda = SchedaAdesione.query.get_or_404(id)
    
    note_content = request.form.get('note', '')
    
    # Find or create the field note record
    field_note = FieldNote.query.filter_by(scheda_id=id, field_name=field_name).first()
    if not field_note:
        field_note = FieldNote(scheda_id=id, field_name=field_name)
        db.session.add(field_note)
    
    field_note.note = note_content
    db.session.commit()
    flash('Nota campo aggiornata con successo!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_scheda(id):
    if current_user.role != 'admin':
        flash('Accesso negato. Solo gli amministratori possono eliminare schede.', 'error')
        return redirect(url_for('dashboard'))
    
    scheda = SchedaAdesione.query.get_or_404(id)
    db.session.delete(scheda)
    db.session.commit()
    flash('Scheda eliminata con successo!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/report', methods=['GET', 'POST'])
@login_required
def generate_report():
    filter_text = request.form.get('filter_text', '').strip() if request.method == 'POST' else request.args.get('filter_text', '').strip()
    
    # Get all schede
    schede = SchedaAdesione.query.all()
    
    # Apply filter if provided
    if filter_text:
        filtered_schede = []
        for scheda in schede:
            # Get field notes for this scheda
            field_notes = {}
            for field_name in ['consegna_materiale', 'presentazioni', 'ritiro_pacchi']:
                field_note = FieldNote.query.filter_by(scheda_id=scheda.id, field_name=field_name).first()
                if field_note:
                    field_notes[field_name] = scheda.__dict__.get(field_name, '')
            
            # Check if any of the fields match the filter
            if (filter_text.lower() in field_notes.get('consegna_materiale', '').lower() or
                filter_text.lower() in field_notes.get('presentazioni', '').lower() or
                filter_text.lower() in field_notes.get('ritiro_pacchi', '').lower()):
                filtered_schede.append(scheda)
        schede = filtered_schede
    
    # Generate PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    elements = []
    
    # Title
    styles = getSampleStyleSheet()
    title = Paragraph(f"Report DONACIBO - {datetime.now().strftime('%d/%m/%Y')}", styles['Title'])
    elements.append(title)
    
    if filter_text:
        filter_paragraph = Paragraph(f"Filtro: {filter_text}", styles['Normal'])
        elements.append(filter_paragraph)
    
    elements.append(Paragraph("<br/>", styles['Normal']))
    
    # Table data
    table_data = [
        ['Istituto', 'Scuola', 'Grado', 'N° Presentazioni', 'Consegna Materiale', 'Presentazioni', 'Ritiro Pacchi']
    ]
    
    for scheda in schede:
        # Get field values
        consegna_materiale = scheda.consegna_materiale or ''
        presentazioni = scheda.presentazioni or ''
        ritiro_pacchi = scheda.ritiro_pacchi or ''
        
        table_data.append([
            scheda.nome_istituto,
            scheda.nome_scuola,
            scheda.grado,
            scheda.numero_presentazioni,
            consegna_materiale,
            presentazioni,
            ritiro_pacchi
        ])
    
    # Create table
    table = Table(table_data, colWidths=[2.5*inch, 2*inch, 1*inch, 1.3*inch, 1.7*inch, 1.7*inch, 1.7*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'report_donacibo_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
        mimetype='application/pdf'
    )

def init_db():
    with app.app_context():
        db.create_all()
        
        # Create default users if they don't exist
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
        
        if not User.query.filter_by(username='volontario').first():
            volontario = User(
                username='volontario',
                password_hash=generate_password_hash('volontario123'),
                role='volontario'
            )
            db.session.add(volontario)
        
        db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
