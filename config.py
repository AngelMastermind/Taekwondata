# MultipleFiles/config.py
import os
# Configuración de la base de datos
SQLALCHEMY_DATABASE_URI = 'postgresql://postgres.temvdmmkuuhyuipejpbo:1025655077@aws-1-us-east-1.pooler.supabase.com:6543/postgres'
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = os.urandom(24)
