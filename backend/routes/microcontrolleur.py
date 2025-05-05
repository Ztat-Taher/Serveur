# routes/microcontrolleur.py
from flask import Blueprint, jsonify, request
from datetime import datetime
from ..models.db import db, Microcontrolleur, TypeCapteur, Capteur, DonneeCapteur, DeviceState, DiagnosticResult, Alerte
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

    # Check if microcontroller exists by identifier (e.g., hostname or MAC address)
    existing = Microcontrolleur.query.filter_by(nom=data['identifier']).first()
    if existing:
        return jsonify({'message': 'Microcontroller already registered', 'id': existing.id}), 200

    # Create new microcontroller
    try:
        microcontroller = Microcontrolleur(nom=data['nom'])
        db.session.add(microcontroller)
        db.session.commit()

        # Trigger PostgreSQL notification
        db.session.execute("NOTIFY new_microcontrolleur, %s", (json.dumps({
            'id': microcontroller.id,
            'nom': microcontroller.nom
        }),))

        return jsonify({'message': 'Microcontroller registered', 'id': microcontroller.id}), 201
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

@microcontrolleur_bp.route('/device-states', methods=['GET'])
def get_device_states():
    device_states = DeviceState.query.order_by(DeviceState.timestamp.desc()).all()
    return jsonify({
        'deviceStates': [{
            'id': state.id,
            'microcontrolleurid': state.microcontrolleurid,
            'cpu': state.cpu,
            'ram': state.ram,
            'ramTotal': state.ram_total,
            'temperature': state.temperature,
            'storage': state.storage,
            'storageTotal': state.storage_total,
            'uptime': state.uptime,
            'processes | processes': state.processes,
            'timestamp': state.timestamp.isoformat() + 'Z'
        } for state in device_states]
    })

@microcontrolleur_bp.route('/device-states', methods=['POST'])
def add_device_state():
    data = request.get_json()
    try:
        device_state = DeviceState(
            microcontrolleurid=data['microcontrolleurid'],
            cpu=data.get('cpu'),
            ram=data.get('ram'),
            ram_total=data.get('ram_total'),
            temperature=data.get('temperature'),
            storage=data.get('storage'),
            storage_total=data.get('storage_total'),
            uptime=data.get('uptime'),
            processes=data.get('processes'),
            timestamp=datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        )
        db.session.add(device_state)
        db.session.commit()

        # Trigger PostgreSQL notification
        db.session.execute("NOTIFY device_state_channel, %s", (json.dumps({
            'id': device_state.id,
            'microcontrolleurid': device_state.microcontrolleurid,
            'cpu': device_state.cpu,
            'ram': device_state.ram,
            'ram_total': device_state.ram_total,
            'temperature': device_state.temperature,
            'storage': device_state.storage,
            'storage_total': device_state.storage_total,
            'uptime': device_state.uptime,
            'processes': device_state.processes,
            'timestamp': device_state.timestamp.isoformat() + 'Z'
        }),))

        return jsonify({'message': 'Device state added'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@microcontrolleur_bp.route('/diagnostic-results', methods=['GET'])
def get_diagnostic_results():
    diagnostic_results = DiagnosticResult.query.order_by(DiagnosticResult.timestamp.desc()).all()
    return jsonify({
        'results': [{
            'id': result.id,
            'microcontrolleurid': result.microcontrolleurid,
            'capteurid': result.capteurid,
            'result': result.result,
            'severity': result.severity,
            'timestamp': result.timestamp.isoformat() + 'Z'
        } for result in diagnostic_results]
    })

@microcontrolleur_bp.route('/alerts', methods=['GET'])
def get_alerts():
    alerts = Alerte.query.order_by(Alerte.dateheure.desc()).all()
    return jsonify({
        'alerts': [{
            'id': alert.id,
            'type': alert.type,
            'dateheure': alert.dateheure.isoformat() + 'Z',
            'statut': alert.statut,
            'message': f"{alert.type}: {alert.statut.capitalize()}" + (f" (Sensor ID: {alert.capteurid})" if alert.capteurid else "")
        } for alert in alerts]
    })