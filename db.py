"""
=============================================================================
SISTEMA DE GESTIÓN: EL BUEN MORDISCO
Archivo: db.py
Descripción: Conexión y ejecución de consultas SQL usando la librería nativa sqlite3.
Permite ejecutar código SQL puro (SELECT, INSERT, UPDATE, DELETE) desde Python.
=============================================================================
"""

import sqlite3
import os

DATABASE = 'el_buen_mordisco.db'

def get_db_connection():
    """
    Abre una conexión con la base de datos SQLite.
    'row_factory = sqlite3.Row' nos permite acceder a las columnas por su nombre,
    por ejemplo: producto['nombre'], en lugar de números de índice.
    """
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    # Habilitar el control de claves foráneas en SQLite
    conn.execute('PRAGMA foreign_keys = ON;')
    return conn

def init_db():
    """
    Lee el archivo 'schema.sql' y ejecuta todas las sentencias CREATE TABLE
    e INSERT INTO para crear la base de datos desde cero con código SQL puro.
    """
    print(">> Inicializando base de datos desde 'schema.sql'...")
    ruta_schema = os.path.join(os.path.dirname(__file__), 'schema.sql')
    
    with open(ruta_schema, 'r', encoding='utf-8') as f:
        script_sql = f.read()
    
    conn = get_db_connection()
    conn.executescript(script_sql)
    conn.commit()
    conn.close()
    print(">> Base de datos inicializada exitosamente con código SQL puro.")

if __name__ == '__main__':
    init_db()
