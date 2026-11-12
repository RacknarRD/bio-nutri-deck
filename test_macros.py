"""
Pruebas unitarias básicas para app-macros.py (BIO-NUTRI DECK v5.6)

Ejecuta con: python3 -m pytest test_macros.py -v
O simplemente: python3 test_macros.py
"""

import sys
import os
import json
import tempfile
import shutil

# Agregar el directorio actual al path para importar app-macros
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar funciones de app-macros (nombre con guión, usar importlib)
import importlib
app_mod = importlib.import_module("app-macros")

calcular_tmb = app_mod.calcular_tmb
calcular_macros = app_mod.calcular_macros
validar_rango = app_mod.validar_rango
buscar_alimento_por_nombre = app_mod.buscar_alimento_por_nombre
foods_db = app_mod.foods_db

# --- PRUEBAS DE TMB ---
def test_calcular_tmb_masculino():
    """Prueba cálculo de TMB para hombre."""
    peso, altura, edad = 70.0, 175.0, 30
    tmb = calcular_tmb(peso, altura, edad, 'M')
    esperado = (10 * peso) + (6.25 * altura) - (5 * edad) + 5
    assert abs(tmb - esperado) < 0.01, f"TMB masculino incorrecto: {tmb} != {esperado}"
    print("  ✅ test_calcular_tmb_masculino")

def test_calcular_tmb_femenino():
    """Prueba cálculo de TMB para mujer."""
    peso, altura, edad = 60.0, 165.0, 25
    tmb = calcular_tmb(peso, altura, edad, 'F')
    esperado = (10 * peso) + (6.25 * altura) - (5 * edad) - 161
    assert abs(tmb - esperado) < 0.01, f"TMB femenino incorrecto: {tmb} != {esperado}"
    print("  ✅ test_calcular_tmb_femenino")

# --- PRUEBAS DE MACROS ---
def test_calcular_macros_volumen():
    """Prueba cálculo de macros para objetivo de volumen (opción '1')."""
    peso = 70.0
    tmb = 1700.0
    calorias = tmb + 400  # Superávit = 2100
    proteina, carbohidratos, grasas, fibra = calcular_macros(peso, calorias, '1')
    
    # Volumen: proteína 2.2 g/kg, grasa 1.0 g/kg
    assert abs(proteina - peso * 2.2) < 0.01
    assert abs(grasas - peso * 1.0) < 0.01
    # Carbohidratos = resto de calorías / 4
    kcal_prot_gras = proteina * 4 + grasas * 9
    assert abs(carbohidratos - (calorias - kcal_prot_gras) / 4) < 0.01
    print("  ✅ test_calcular_macros_volumen")

def test_calcular_macros_definicion():
    """Prueba cálculo de macros para objetivo de definición (opción '3')."""
    peso = 70.0
    tmb = 1700.0
    calorias = tmb - 500  # Déficit = 1200
    proteina, carbohidratos, grasas, fibra = calcular_macros(peso, calorias, '3')
    
    # Definición: proteína 2.5 g/kg, grasa 0.8 g/kg
    assert abs(proteina - peso * 2.5) < 0.01
    assert abs(grasas - peso * 0.8) < 0.01
    print("  ✅ test_calcular_macros_definicion")

# --- PRUEBAS DE VALIDACIÓN ---
def test_validar_rango_valido():
    """Prueba que valores válidos pasen la validación."""
    assert validar_rango(70, 0.5, 300) == True
    assert validar_rango(175, 60, 275) == True
    assert validar_rango(30, 10, 100) == True
    print("  ✅ test_validar_rango_valido")

def test_validar_rango_invalido():
    """Prueba que valores inválidos fallen la validación."""
    assert validar_rango(-5, 0.5, 300) == False
    assert validar_rango(500, 0.5, 300) == False
    assert validar_rango(5, 60, 275) == False
    assert validar_rango(300, 60, 275) == False
    assert validar_rango(5, 10, 100) == False
    assert validar_rango(150, 10, 100) == False
    print("  ✅ test_validar_rango_invalido")

# --- PRUEBAS DE BASE DE DATOS ---
def test_foods_db_no_vacia():
    """Prueba que la base de datos de alimentos no esté vacía."""
    assert len(foods_db) >= 26, f"Se esperaban al menos 26 alimentos, hay {len(foods_db)}"
    print("  ✅ test_foods_db_no_vacia")

def test_buscar_alimento_por_nombre():
    """Prueba búsqueda de alimentos por nombre."""
    # Búsqueda exacta
    resultados = buscar_alimento_por_nombre("pechuga de pollo")
    assert len(resultados) >= 1, "Debería encontrar 'Pechuga de pollo'"
    
    # Búsqueda parcial
    resultados = buscar_alimento_por_nombre("pollo")
    assert len(resultados) >= 2, "Debería encontrar al menos 2 alimentos con 'pollo'"
    
    # Búsqueda sin resultados
    resultados = buscar_alimento_por_nombre("xyz123")
    assert len(resultados) == 0, "No debería encontrar nada con 'xyz123'"
    
    print("  ✅ test_buscar_alimento_por_nombre")

def test_alimentos_nuevos_rd():
    """Prueba que los alimentos típicos de RD estén en la base de datos."""
    nombres = [info['nombre'].lower() for info in foods_db.values()]
    assert any('mangú' in n for n in nombres), "Falta: Mangú"
    assert any('queso frito' in n for n in nombres), "Falta: Queso Frito"
    assert any('salami' in n for n in nombres), "Falta: Salami Dominicano"
    assert any('habichuela' in n for n in nombres), "Falta: Habichuelas"
    assert any('salmón' in n for n in nombres), "Falta: Salmón"
    assert any('whey' in n for n in nombres), "Falta: Whey Protein"
    print("  ✅ test_alimentos_nuevos_rd")

# --- PRUEBA DE EXPORTACIÓN JSON ---
def test_exportar_json():
    """Prueba exportación a JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ruta_original = os.getcwd()
        os.chdir(tmpdir)
        try:
            # Simular datos de exportación
            datos = {
                "fecha": "01/01/2024 12:00:00",
                "objetivo": "Test",
                "tmb": 1700,
                "calorias_diarias": 2100,
                "proteinas_g": 154.0,
                "carbohidratos_g": 250.0,
                "grasas_g": 70.0,
                "fibra_g": 29.4,
                "menu": "Menú de prueba"
            }
            nombre_archivo = "test_plan.json"
            with open(nombre_archivo, "w", encoding="utf-8") as f:
                json.dump(datos, f, indent=2, ensure_ascii=False)
            
            # Verificar que se creó y se puede leer
            assert os.path.exists(nombre_archivo), "El archivo JSON no se creó"
            with open(nombre_archivo, "r", encoding="utf-8") as f:
                datos_leidos = json.load(f)
            assert datos_leidos["objetivo"] == "Test"
            assert datos_leidos["proteinas_g"] == 154.0
            print("  ✅ test_exportar_json")
        finally:
            os.chdir(ruta_original)

# --- EJECUTAR TODAS LAS PRUEBAS ---
if __name__ == "__main__":
    print("\n" + "="*50)
    print("  EJECUTANDO PRUEBAS UNITARIAS - BIO-NUTRI DECK v5.6")
    print("="*50 + "\n")
    
    pruebas = [
        test_calcular_tmb_masculino,
        test_calcular_tmb_femenino,
        test_calcular_macros_volumen,
        test_calcular_macros_definicion,
        test_validar_rango_valido,
        test_validar_rango_invalido,
        test_foods_db_no_vacia,
        test_buscar_alimento_por_nombre,
        test_alimentos_nuevos_rd,
        test_exportar_json,
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
