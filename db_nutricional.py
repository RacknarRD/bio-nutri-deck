"""
Módulo de base de datos para BIO-NUTRI DECK v5.7
Almacena planes nutricionales en SQLite para consultas y estadísticas.
"""

import sqlite3
import json
import os
from datetime import datetime

DB_PATH = "planes_nutricionales.db"


def get_connection():
    """Retorna una conexión a la base de datos SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Crea las tablas si no existen."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS planes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            objetivo TEXT NOT NULL,
            tmb REAL NOT NULL,
            calorias_diarias REAL NOT NULL,
            proteinas_g REAL NOT NULL,
            carbohidratos_g REAL NOT NULL,
            grasas_g REAL NOT NULL,
            fibra_g REAL NOT NULL,
            peso_kg REAL NOT NULL,
            altura_cm REAL NOT NULL,
            edad INTEGER NOT NULL,
            sexo TEXT NOT NULL,
            menu_texto TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def guardar_plan(plan_data):
    """
    Guarda un plan nutricional en la base de datos.
    
    plan_data: dict con claves:
        fecha, objetivo, tmb, calorias_diarias, proteinas_g,
        carbohidratos_g, grasas_g, fibra_g, peso_kg, altura_cm,
        edad, sexo, menu_texto
    Retorna el ID del plan insertado.
    """
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO planes (
            fecha, objetivo, tmb, calorias_diarias,
            proteinas_g, carbohidratos_g, grasas_g, fibra_g,
            peso_kg, altura_cm, edad, sexo, menu_texto
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        plan_data.get("fecha", datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
        plan_data.get("objetivo", ""),
        plan_data.get("tmb", 0),
        plan_data.get("calorias_diarias", 0),
        plan_data.get("proteinas_g", 0),
        plan_data.get("carbohidratos_g", 0),
        plan_data.get("grasas_g", 0),
        plan_data.get("fibra_g", 0),
        plan_data.get("peso_kg", 0),
        plan_data.get("altura_cm", 0),
        plan_data.get("edad", 0),
        plan_data.get("sexo", ""),
        plan_data.get("menu_texto", "")
    ))
    plan_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return plan_id


def listar_planes(limit=50, objetivo_filtro=None):
    """
    Retorna lista de planes guardados ordenados por fecha descendente.
    
    Args:
        limit: máximo número de registros a retornar
        objetivo_filtro: filtrar por tipo de objetivo (opcional)
    Retorna: lista de dicts
    """
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    if objetivo_filtro:
        cursor.execute("""
            SELECT * FROM planes 
            WHERE objetivo = ? 
            ORDER BY created_at DESC, id DESC 
            LIMIT ?
        """, (objetivo_filtro, limit))
    else:
        cursor.execute("""
            SELECT * FROM planes 
            ORDER BY created_at DESC, id DESC 
            LIMIT ?
        """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def obtener_plan(plan_id):
    """Retorna un plan por su ID."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM planes WHERE id = ?", (plan_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def eliminar_plan(plan_id):
    """Elimina un plan por su ID. Retorna True si se eliminó."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM planes WHERE id = ?", (plan_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def obtener_estadisticas():
    """
    Retorna estadísticas agregadas de todos los planes.
    Retorna dict con: total_planes, promedio_calorias, promedio_proteinas,
    promedio_carbohidratos, promedio_grasas, objetivos_distribucion
    """
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    # Totales y promedios
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            AVG(calorias_diarias) as avg_calorias,
            AVG(proteinas_g) as avg_proteinas,
            AVG(carbohidratos_g) as avg_carbohidratos,
            AVG(grasas_g) as avg_grasas,
            AVG(peso_kg) as avg_peso
        FROM planes
    """)
    row = cursor.fetchone()
    
    # Distribución de objetivos
    cursor.execute("""
        SELECT objetivo, COUNT(*) as count 
        FROM planes 
        GROUP BY objetivo
    """)
    objetivos = cursor.fetchall()
    
    conn.close()
    
    return {
        "total_planes": row["total"] if row["total"] else 0,
        "promedio_calorias": round(row["avg_calorias"], 1) if row["avg_calorias"] else 0,
        "promedio_proteinas": round(row["avg_proteinas"], 1) if row["avg_proteinas"] else 0,
        "promedio_carbohidratos": round(row["avg_carbohidratos"], 1) if row["avg_carbohidratos"] else 0,
        "promedio_grasas": round(row["avg_grasas"], 1) if row["avg_grasas"] else 0,
        "promedio_peso": round(row["avg_peso"], 1) if row["avg_peso"] else 0,
        "objetivos_distribucion": [{"objetivo": o["objetivo"], "count": o["count"]} for o in objetivos]
    }


def exportar_planes_a_json(ruta_archivo="planes_exportados.json"):
    """Exporta todos los planes a un archivo JSON."""
    planes = listar_planes(limit=1000)
    with open(ruta_archivo, "w", encoding="utf-8") as f:
        json.dump(planes, f, indent=2, ensure_ascii=False)
    return ruta_archivo
