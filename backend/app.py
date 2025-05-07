# backend/app.py
import logging
from flask import Flask
from flask_socketio import SocketIO
from .config import Config
from .models.db import db
from .routes.microcontrolleur import microcontrolleur_bp
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import threading
import json
from urllib.parse import urlparse
import time
from tenacity import retry, stop_after_attempt, wait_fixed

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

# Initialize Flask-SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

app.register_blueprint(microcontrolleur_bp)

# Function to convert SQLAlchemy URI to psycopg2 DSN
def uri_to_dsn(uri):
    parsed = urlparse(uri)
    dbname = parsed.path.lstrip('/')
    user = parsed.username
    password = parsed.password
    host = parsed.hostname
    port = parsed.port
    return f"dbname={dbname} user={user} password={password} host={host} port={port}"

# Function to listen for PostgreSQL notifications with retry
@retry(stop=stop_after_attempt(5), wait=wait_fixed(10))
def listen_for_notifications():
    try:
        dsn = uri_to_dsn(app.config['SQLALCHEMY_DATABASE_URI'])
        conn = psycopg2.connect(dsn)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        channels = ['new_microcontrolleur', 'new_data', 'new_alert', 'new_presence']
        for channel in channels:
            cursor.execute(f"LISTEN {channel};")
        
        logger.info("Listening for PostgreSQL notifications...")
        while True:
            conn.poll()
            while conn.notifies:
                notify = conn.notifies.pop(0)
                payload = json.loads(notify.payload)
                logger.info(f"Received notification on channel {notify.channel}: {payload}")
                
                if notify.channel == 'new_microcontrolleur':
                    socketio.emit('new_microcontrolleur', {'type': 'new_microcontrolleur', 'data': payload})
                elif notify.channel == 'new_data':
                    cursor.execute("""
                        SELECT d.id, d.capteurid, d.valeur, d.timestamp,
                               c.etat, t.nom AS type, t.unite, m.nom AS microcontrolleur
                        FROM donneescapteurs d
                        JOIN capteurs c ON d.capteurid = c.id
                        JOIN typescapteurs t ON c.typecapteurid = t.id
                        JOIN microcontrolleur m ON c.microcontrolleurid = m.id
                        WHERE d.id = %s
                    """, (payload['id'],))
                    result = cursor.fetchone()
                    if result:
                        sensor_data = {
                            'capteurid': result[1],
                            'type': result[5],
                            'etat': result[4],
                            'valeur': result[2],
                            'unite': result[6],
                            'calibrated': True,
                            'timestamp': result[3].isoformat() + 'Z',
                            'microcontrolleur': result[7]
                        }
                        socketio.emit('new_data', {'type': 'new_data', 'data': sensor_data})
                        logger.info(f"Emitted new_data: {sensor_data}")
                elif notify.channel == 'new_alert':
                    message = f"{payload['type']}: {payload['statut'].capitalize()}"
                    if payload['capteurid']:
                        message += f" (Sensor ID: {payload['capteurid']})"
                    socketio.emit('new_alert', {
                        'type': 'new_alert',
                        'data': {
                            'id': payload['id'],
                            'type': payload['type'],
                            'dateheure': payload['dateheure'],
                            'statut': payload['statut'],
                            'etudiantid': payload['etudiantid'],
                            'capteurid': payload['capteurid'],
                            'enseignantid': payload['enseignantid'],
                            'technicienid': payload['technicienid'],
                            'message': message
                        }
                    })
                    logger.info(f"Emitted new_alert: {payload}")
                elif notify.channel == 'new_presence':
                    socketio.emit('new_presence', {
                        'type': 'new_presence',
                        'data': {
                            'id': payload['id'],
                            'etudiantid': payload['etudiantid'],
                            'statut': payload['statut'],
                            'date_heure': payload['date_heure']
                        }
                    })
                    logger.info(f"Emitted new_presence: {payload}")
    except Exception as e:
        logger.error(f"Error in notification listener: {str(e)}")
        raise

# Start the notification listener in a separate thread
thread = threading.Thread(target=listen_for_notifications, daemon=True)
thread.start()

if __name__ == '__main__':
    with app.app_context():
        logger.info("Starting Flask-SocketIO server...")
        socketio.run(app, host='0.0.0.0', port=8083, debug=True)