# routes/microcontrolleur.py
from flask import Blueprint, jsonify, request
from datetime import datetime
from ..models.db import db, Microcontrolleur, TypeCapteur, Capteur, DonneeCapteur, Alerte
import json

microcontrolleur_bp = Blueprint('microcontrolleur', __name__, url_prefix='/api')

@microcontrolleur_bp.route('/microcontrollers', methods=['GET'])
def get_microcontrollers():
    microcontrollers = Microcontrolleur.query.all()
    return jsonify({
        'microcontrollers': [{'id': mc.id, 'nom': mc.nom} for mc in microcontrollers]
    })

@microcontrolleur_bp.route('/microcontrollers/register', methods=['POST'])
def register_microcontroller():
    data = request.get_json()
    if not data or 'nom' not in data or 'identifier' not in data:
        return jsonify({'error': 'Missing nom or identifier'}), 400

    # Check if microcontroller exists by identifier
    existing = Microcontrolleur.query.filter_by(nom=data['identifier']).first()
    if existing:
        # Return existing microcontroller ID and associated sensor IDs
        sensors = Capteur.query.filter_by(microcontrolleurid=existing.id).all()
        return jsonify({
            'message': 'Microcontroller already registered',
            'id': existing.id,
            'sensors': {s.etat: s.id for s in sensors}
        }), 200

    try:
        # Create microcontroller
        microcontroller = Microcontrolleur(nom=data['nom'])
        db.session.add(microcontroller)
        db.session.flush()  # Get microcontroller.id

        # Create sensor types if they don't exist
        sensor_types = {
            'cpu': {'nom': 'CPU Usage', 'unite': '%'},
            'ram': {'nom': 'RAM Usage', 'unite': 'MB'},
            'temperature': {'nom': 'Temperature', 'unite': 'C'},
            'storage': {'nom': 'Storage Usage', 'unite': 'GB'},
            'uptime': {'nom': 'Uptime', 'unite': 'seconds'},
            'processes': {'nom': 'Processes', 'unite': 'count'}
        }
        sensor_type_ids = {}
        for key, info in sensor_types.items():
            sensor_type = TypeCapteur.query.filter_by(nom=info['nom']).first()
            if not sensor_type:
                sensor_type = TypeCapteur(nom=info['nom'], unite=info['unite'])
                db.session.add(sensor_type)
                db.session.flush()
            sensor_type_ids[key] = sensor_type.id

        # Create sensors for each metric
        sensors = {}
        for key, type_id in sensor_type_ids.items():
            sensor = Capteur(
                typecapteurid=type_id,
                etat=key,  # e.g., 'cpu', 'ram'
                microcontrolleurid=microcontroller.id
            )
            db.session.add(sensor)
            db.session.flush()
            sensors[key] = sensor.id

        db.session.commit()

        # Trigger notification
        db.session.execute("NOTIFY new_microcontrolleur, %s", (json.dumps({
            'id': microcontroller.id,
            'nom': microcontroller.nom
        }),))

        return jsonify({
            'message': 'Microcontroller registered',
            'id': microcontroller.id,
            'sensors': sensors
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@microcontrolleur_bp.route('/sensor-data', methods=['GET'])
def get_sensor_data():
    sensor_data = db.session.query(DonneeCapteur, Capteur, TypeCapteur, Microcontrolleur).\
        join(Capteur, DonneeCapteur.capteurid == Capteur.id).\
        join(TypeCapteur, Capteur.typecapteurid == TypeCapteur.id).\
        join(Microcontrolleur, Capteur.microcontrolleurid == Microcontrolleur.id).\
        order_by(DonneeCapteur.timestamp.desc()).all()

    return jsonify({
        'sensors': [{
            'capteurid': data.DonneeCapteur.capteurid,
            'type': data.TypeCapteur.nom,
            'etat': data.Capteur.etat,
            'valeur': data.DonneeCapteur.valeur,
            'unite': data.TypeCapteur.unite,
            'calibrated': True,
            'timestamp': data.DonneeCapteur.timestamp.isoformat() + 'Z',
            'microcontrolleur': data.Microcontrolleur.nom
        } for data in sensor_data]
    })

@microcontrolleur_bp.route('/device-metrics', methods=['POST'])
def add_device_metrics():
    data = request.get_json()
    if not data or 'microcontrolleurid' not in data or 'metrics' not in data:
        return jsonify({'error': 'Missing microcontrolleurid or metrics'}), 400

    try:
        timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        for metric_name, value in data['metrics'].items():
            # Find the sensor for this metric
            sensor = Capteur.query.filter_by(
                microcontrolleurid=data['microcontrolleurid'],
                etat=metric_name
            ).first()
            if not sensor:
                return jsonify({'error': f'No sensor found for metric {metric_name}'}), 400

            # Add metric to donneescapteurs
            donnee = DonneeCapteur(
                capteurid=sensor.id,
                valeur=float(value),
                timestamp=timestamp
            )
            db.session.add(donnee)

        db.session.commit()

        # Trigger notification for each donneescapteur (handled by trigger)
        return jsonify({'message': 'Device metrics added'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@microcontrolleur_bp.route('/alerts', methods=['GET'])
def get_alerts():
    alerts = Alerte.query.order_by(Alerte.dateheure.desc()).all()
    return jsonify({
        'alerts': [{
            'id': alert.id,
            'type': alert.type,
            'dateheure': alert.dateheure.isoformat() + 'Z',
            'statut': alert.statut,
            'etudiantid': alert.etudiantid,
            'capteurid': alert.capteurid,
            'enseignantid': alert.enseignantid,
            'technicienid': alert.technicienid,
            'message': f"{alert.type}: {alert.statut.capitalize()}" + (f" (Sensor ID: {alert.capteurid})" if alert.capteurid else "")
        } for alert in alerts]
    })