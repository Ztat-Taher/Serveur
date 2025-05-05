 # backend/config.py
class Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://imene:imene@10.255.255.126:5432/edge_ia_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'imene'