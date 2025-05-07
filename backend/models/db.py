# backend/models/db.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSONB

db = SQLAlchemy()

class Microcontrolleur(db.Model):
    __tablename__ = 'microcontrolleur'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    capteurs = db.relationship('Capteur', backref='microcontrolleur', lazy=True)

class TypeCapteur(db.Model):
    __tablename__ = 'typescapteurs'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    unite = db.Column(db.String(50))
    capteurs = db.relationship('Capteur', backref='typecapteur', lazy=True)

class Capteur(db.Model):
    __tablename__ = 'capteurs'
    id = db.Column(db.Integer, primary_key=True)
    typecapteurid = db.Column(db.Integer, db.ForeignKey('typescapteurs.id'))
    etat = db.Column(db.String(50), nullable=False)
    microcontrolleurid = db.Column(db.Integer, db.ForeignKey('microcontrolleur.id'))
    donnees = db.relationship('DonneeCapteur', backref='capteur', lazy=True)

class DonneeCapteur(db.Model):
    __tablename__ = 'donneescapteurs'
    id = db.Column(db.Integer, primary_key=True)
    capteurid = db.Column(db.Integer, db.ForeignKey('capteurs.id'))
    valeur = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)

class Alerte(db.Model):
    __tablename__ = 'alertes'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    dateheure = db.Column(db.DateTime, nullable=False)
    statut = db.Column(db.String(50), nullable=False)
    etudiantid = db.Column(db.Integer, db.ForeignKey('etudiants.id'), nullable=True)
    capteurid = db.Column(db.Integer, db.ForeignKey('capteurs.id'), nullable=True)
    enseignantid = db.Column(db.Integer, db.ForeignKey('enseignants.id'), nullable=True)
    technicienid = db.Column(db.Integer, db.ForeignKey('techniciens.id'), nullable=True)

class Etablissement(db.Model):
    __tablename__ = 'etablissements'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    adresse = db.Column(db.String(255))
    classes = db.relationship('Classe', backref='etablissement', lazy=True)

class Classe(db.Model):
    __tablename__ = 'classes'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    etablissementid = db.Column(db.Integer, db.ForeignKey('etablissements.id'))
    etudiants = db.relationship('Etudiant', backref='classe', lazy=True)
    cours = db.relationship('Cours', backref='classe', lazy=True)
    emploidutemps = db.relationship('EmploiDuTemps', backref='classe', lazy=True)

class Etudiant(db.Model):
    __tablename__ = 'etudiants'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    classeid = db.Column(db.Integer, db.ForeignKey('classes.id'))
    photopath = db.Column(db.String(255))
    embedding = db.Column(db.LargeBinary)
    presences = db.relationship('Presence', backref='etudiant', lazy=True)
    alertes = db.relationship('Alerte', backref='etudiant', lazy=True)

class Enseignant(db.Model):
    __tablename__ = 'enseignants'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    statut = db.Column(db.String(50))
    cours = db.relationship('Cours', backref='enseignant', lazy=True)
    alertes = db.relationship('Alerte', backref='enseignant', lazy=True)

class Cours(db.Model):
    __tablename__ = 'cours'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    enseignantid = db.Column(db.Integer, db.ForeignKey('enseignants.id'))
    classeid = db.Column(db.Integer, db.ForeignKey('classes.id'))
    dateheure = db.Column(db.DateTime, nullable=False)

class Presence(db.Model):
    __tablename__ = 'presences'
    id = db.Column(db.Integer, primary_key=True)
    etudiantid = db.Column(db.Integer, db.ForeignKey('etudiants.id'))
    statut = db.Column(db.String(50), nullable=False)
    date_heure = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

class Technicien(db.Model):
    __tablename__ = 'techniciens'
    id = db.Column(db.Integer, primary_key=True)
    utilisateurid = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    specialite = db.Column(db.String(100))
    alertes = db.relationship('Alerte', backref='technicien', lazy=True)

class Utilisateur(db.Model):
    __tablename__ = 'utilisateur'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    motdepasse = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    techniciens = db.relationship('Technicien', backref='utilisateur', lazy=True)
    admins = db.relationship('Admin', backref='utilisateur', lazy=True)
    directeurs = db.relationship('Directeur', backref='utilisateur', lazy=True)
    user_systems = db.relationship('UserSystem', backref='utilisateur', lazy=True)

class Admin(db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    utilisateurid = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    permissions = db.Column(db.Text)

class Directeur(db.Model):
    __tablename__ = 'directeur'
    id = db.Column(db.Integer, primary_key=True)
    utilisateurid = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)

class EmploiDuTemps(db.Model):
    __tablename__ = 'emploidutemps'
    id = db.Column(db.Integer, primary_key=True)
    classeid = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    emploidutemps = db.Column(JSONB, nullable=False)

class InstanceSysteme(db.Model):
    __tablename__ = 'instance_systeme'
    system_id = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255))
    status = db.Column(db.String(255))
    user_systems = db.relationship('UserSystem', backref='instance_systeme', lazy=True)

class UserSystem(db.Model):
    __tablename__ = 'user_system'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    system_id = db.Column(db.String(255), db.ForeignKey('instance_systeme.system_id'), nullable=False)
    connected_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_token'
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(10), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    expiry_date = db.Column(db.DateTime, nullable=False)