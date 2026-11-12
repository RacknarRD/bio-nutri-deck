"""
Pruebas unitarias para db_nutricional.py (BIO-NUTRI DECK v5.7)

Ejecuta con: python3 test_db.py
"""

import sys
import os
import tempfile
import json

# Agregar directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import db_nutricional


def crear_db_temporal():
    """Crea una base de datos SQLite en un archivo temporal y retorna la ruta."""
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "test_planes.db")
    db_nutricional.DB_PATH = db_path
    db_nutricional.init_db()
    return tmpdir


def test_init_db_crea_tablas():
    """Prueba que init_db cree las tablas correctamente."""
    tmpdir = crear_db_temporal()
    conn = db_nutricional.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='planes'")
    result = cursor.fetchone()
    conn.close()
    assert result is not None, "La tabla 'planes' debería existir"
    print("  ✅ test_init_db_crea_tablas")


def test_guardar_y_obtener_plan():
    """Prueba guardar un plan y obtenerlo por ID."""
    tmpdir = crear_db_temporal()

    plan_data = {
        "fecha": "01/01/2024 12:00:00",
        "objetivo": "Aumentar Masa Muscular (Superávit)",
        "tmb": 1700.0,
        "calorias_diarias": 2100.0,
        "proteinas_g": 154.0,
        "carbohidratos_g": 250.0,
        "grasas_g": 70.0,
        "fibra_g": 29.4,
        "peso_kg": 70.0,
        "altura_cm": 175.0,
        "edad": 30,
        "sexo": "M",
        "menu_texto": "Menú de prueba"
    }

    plan_id = db_nutricional.guardar_plan(plan_data)
    assert plan_id is not None, "Debería retornar un ID"
    assert isinstance(plan_id, int), "El ID debería ser un entero"

    plan = db_nutricional.obtener_plan(plan_id)
    assert plan is not None, "Debería encontrar el plan guardado"
    assert plan["objetivo"] == plan_data["objetivo"]
    assert plan["calorias_diarias"] == 2100.0
    assert plan["proteinas_g"] == 154.0
    print("  ✅ test_guardar_y_obtener_plan")


def test_listar_planes():
    """Prueba listar planos guardados."""
    tmpdir = crear_db_temporal()

    # Insertar 3 planes
    for i in range(3):
        plan_data = {
            "fecha": f"01/01/2024 12:00:{i:02d}",
            "objetivo": "Test",
            "tmb": 1700.0,
            "calorias_diarias": 2000.0 + i * 100,
            "proteinas_g": 150.0,
            "carbohidratos_g": 200.0,
            "grasas_g": 60.0,
            "fibra_g": 25.0,
            "peso_kg": 70.0,
            "altura_cm": 175.0,
            "edad": 30,
            "sexo": "M",
            "menu_texto": f"Menú {i}"
        }
        db_nutricional.guardar_plan(plan_data)

    planes = db_nutricional.listar_planes(limit=10)
    assert len(planes) == 3, f"Debería haber 3 planes, hay {len(planes)}"
    # Deberían venir ordenados por fecha descendente
    assert planes[0]["id"] > planes[1]["id"], "Deberían estar ordenados por ID descendente"
    print("  ✅ test_listar_planes")


def test_eliminar_plan():
    """Prueba eliminar un plan por ID."""
    tmpdir = crear_db_temporal()

    plan_data = {
        "fecha": "01/01/2024 12:00:00",
        "objetivo": "Test Eliminar",
        "tmb": 1700.0,
        "calorias_diarias": 2000.0,
        "proteinas_g": 150.0,
        "carbohidratos_g": 200.0,
        "grasas_g": 60.0,
        "fibra_g": 25.0,
        "peso_kg": 70.0,
        "altura_cm": 175.0,
        "edad": 30,
        "sexo": "M",
        "menu_texto": "Menú a eliminar"
    }

    plan_id = db_nutricional.guardar_plan(plan_data)
    assert db_nutricional.obtener_plan(plan_id) is not None

    resultado = db_nutricional.eliminar_plan(plan_id)
    assert resultado is True, "Debería retornar True al eliminar"

    assert db_nutricional.obtener_plan(plan_id) is None, "El plan no debería existir después de eliminar"

    # Intentar eliminar un ID que no existe
    resultado2 = db_nutricional.eliminar_plan(99999)
    assert resultado2 is False, "Debería retornar False si el ID no existe"
    print("  ✅ test_eliminar_plan")


def test_obtener_estadisticas():
    """Prueba el cálculo de estadísticas agregadas."""
    tmpdir = crear_db_temporal()

    # Insertar 2 planes con diferentes objetivos y valores
    planes_data = [
        {
            "fecha": "01/01/2024 10:00:00",
            "objetivo": "Volumen",
            "tmb": 1700.0,
            "calorias_diarias": 2100.0,
            "proteinas_g": 154.0,
            "carbohidratos_g": 250.0,
            "grasas_g": 70.0,
            "fibra_g": 29.4,
            "peso_kg": 70.0,
            "altura_cm": 175.0,
            "edad": 30,
            "sexo": "M",
            "menu_texto": "Menú 1"
        },
        {
            "fecha": "02/01/2024 10:00:00",
            "objetivo": "Definición",
            "tmb": 1600.0,
            "calorias_diarias": 1100.0,
            "proteinas_g": 175.0,
            "carbohidratos_g": 100.0,
            "grasas_g": 56.0,
            "fibra_g": 15.4,
            "peso_kg": 70.0,
            "altura_cm": 175.0,
            "edad": 30,
            "sexo": "M",
            "menu_texto": "Menú 2"
        }
    ]

    for pd in planes_data:
        db_nutricional.guardar_plan(pd)

    stats = db_nutricional.obtener_estadisticas()

    assert stats["total_planes"] == 2
    assert stats["promedio_calorias"] == (2100.0 + 1100.0) / 2  # 1600.0
    assert stats["promedio_proteinas"] == (154.0 + 175.0) / 2  # 164.5
    assert len(stats["objetivos_distribucion"]) == 2
    print("  ✅ test_obtener_estadisticas")


def test_obtener_estadisticas_vacio():
    """Prueba estadísticas con base de datos vacía."""
    tmpdir = crear_db_temporal()

    stats = db_nutricional.obtener_estadisticas()
    assert stats["total_planes"] == 0
    assert stats["promedio_calorias"] == 0
    assert stats["promedio_proteinas"] == 0
    assert stats["objetivos_distribucion"] == []
    print("  ✅ test_obtener_estadisticas_vacio")


def test_exportar_planes_a_json():
    """Prueba exportar planes a JSON."""
    tmpdir = crear_db_temporal()

    plan_data = {
        "fecha": "01/01/2024 12:00:00",
        "objetivo": "Test Export",
        "tmb": 1700.0,
        "calorias_diarias": 2000.0,
        "proteinas_g": 150.0,
        "carbohidratos_g": 200.0,
        "grasas_g": 60.0,
        "fibra_g": 25.0,
        "peso_kg": 70.0,
        "altura_cm": 175.0,
        "edad": 30,
        "sexo": "M",
        "menu_texto": "Menú de exportación"
    }
    db_nutricional.guardar_plan(plan_data)

    # Usar un archivo temporal para la exportación
    export_dir = tempfile.mkdtemp()
    ruta = os.path.join(export_dir, "test_export.json")
    resultado = db_nutricional.exportar_planes_a_json(ruta)
    assert resultado == ruta
    assert os.path.exists(ruta), "El archivo JSON debería existir"

    with open(ruta, "r", encoding="utf-8") as f:
        datos = json.load(f)
    assert len(datos) == 1
    assert datos[0]["objetivo"] == "Test Export"
    print("  ✅ test_exportar_planes_a_json")


# --- EJECUTAR TODAS LAS PRUEBAS ---
if __name__ == "__main__":
    print("\n" + "="*50)
    print("  PRUEBAS UNITARIAS - db_nutricional.py (v5.7)")
    print("="*50 + "\n")

    pruebas = [
        test_init_db_crea_tablas,
        test_guardar_y_obtener_plan,
        test_listar_planes,
        test_eliminar_plan,
        test_obtener_estadisticas,
        test_obtener_estadisticas_vacio,
        test_exportar_planes_a_json,
    ]

    fallos = 0
    for prueba in pruebas:
        try:
            prueba()
        except Exception as e:
            print(f"  ❌ {prueba.__name__}: {e}")
            fallos += 1

    print("\n" + "="*50)
    if fallos == 0:
        print(f"  ✅ TODAS LAS {len(pruebas)} PRUEBAS PASARON")
    else:
        print(f"  ⚠️  {fallos} de {len(pruebas)} pruebas fallaron")
    print("="*50 + "\n")
    sys.exit(0 if fallos == 0 else 1)
