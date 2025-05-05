# backend/models/db.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Microcontrolleur(db.Model):
    _tablename_ = 'microcontrolleur'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    capteurs = db.relationship('Capteur', backref='microcontrolleur', lazy=True)
    device_states = db.relationship('DeviceState', backref='microcontrolleur', lazy=True)
    diagnostic_results = db.relationship('DiagnosticResult', backref='microcontrolleur', lazy=True)

class TypeCapteur(db.Model):
    _tablename_ = 'typescapteurs'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    unite = db.Column(db.String(50))
    capteurs = db.relationship('Capteur', backref='typecapteur', lazy=True)

class Capteur(db.Model):
    _tablename_ = 'capteurs'
    id = db.Column(db.Integer, primary_key=True)
    typecapteurid = db.Column(db.Integer, db.ForeignKey('typescapteurs.id'))
    etat = db.Column(db.String(50), nullable=False)
    microcontrolleurid = db.Column(db.Integer, db.ForeignKey('microcontrolleur.id'))
    donnees = db.relationship('DonneeCapteur', backref='capteur', lazy=True)
    diagnostic_results = db.relationship('DiagnosticResult', backref='capteur', lazy=True)

class DonneeCapteur(db.Model):
    _tablename_ = 'donneescapteurs'
    id = db.Column(db.Integer, primary_key=True)
    capteurid = db.Column(db.Integer, db.ForeignKey('capteurs.id'))
    valeur = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)

class DeviceState(db.Model):
    _tablename_ = 'device_states'
    id = db.Column(db.Integer, primary_key=True)
    microcontrolleurid = db.Column(db.Integer, db.ForeignKey('microcontrolleur.id'), nullable=False)
    cpu = db.Column(db.Float)
    ram = db.Column(db.Float)
    ram_total = db.Column(db.Float)
    temperature = db.Column(db.Float)
    storage = db.Column(db.Float)
    storage_total = db.Column(db.Float)
    uptime = db.Column(db.BigInteger)
    processes = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, nullable=False)

class DiagnosticResult(db.Model):
    _tablename_ = 'diagnostic_results'
    id = db.Column(db.Integer, primary_key=True)
    microcontrolleurid = db.Column(db.Integer, db.ForeignKey('microcontrolleur.id'), nullable=False)
    capteurid = db.Column(db.Integer, db.ForeignKey('capteurs.id'), nullable=True)
    result = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)

class Alerte(db.Model):
    _tablename_ = 'alertes'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    dateheure = db.Column(db.DateTime, nullable=False)
    statut = db.Column(db.String(50), nullable=False)
    capteurid = db.Column(db.Integer, db.ForeignKey('capteurs.id'), nullable=True)