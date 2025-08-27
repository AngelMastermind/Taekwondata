import os

# Configuración de la base de datos
SQLALCHEMY_DATABASE_URI = 'mssql+pyodbc://sa:123@HPSALAPRO9\\SQLEXPRESS/TAEKWONDATA?driver=ODBC+Driver+17+for+SQL+Server'
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = os.urandom(24)