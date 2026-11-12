import os
import time
import json
from colorama import Fore, Style, init
from datetime import datetime
import db_nutricional

init(autoreset=True)

# --- FUNCIONES AUXILIARES (testeables) ---

def calcular_tmb(peso, altura, edad, sexo):
    """Calcula la Tasa Metabólica Basal usando fórmula de Mifflin-St Jeor."""
    if sexo == 'M':
        return (10 * peso) + (6.25 * altura) - (5 * edad) + 5
    else:
        return (10 * peso) + (6.25 * altura) - (5 * edad) - 161

def validar_rango(valor, minimo, maximo):
    """Valida que un valor esté dentro de un rango permitido."""
    return minimo <= valor <= maximo

def calcular_macros(peso, calorias, objetivo):
    """
    Calcula macros según el objetivo.
    Retorna: (proteina_g, carbohidratos_g, grasas_g, fibra_g)
    """
    if objetivo == '1':  # Volumen
        proteina = peso * 2.2
        grasas = peso * 1.0
    elif objetivo == '2':  # Recomposición
        proteina = peso * 2.4
        grasas = peso * 0.9
    elif objetivo == '3':  # Definición
        proteina = peso * 2.5
        grasas = peso * 0.8
    else:  # Mantenimiento
        proteina = peso * 2.0
        grasas = peso * 1.0

    kcal_prot_gras = proteina * 4 + grasas * 9
    carbohidratos = (calorias - kcal_prot_gras) / 4
    fibra = (calorias / 1000) * 14

    return proteina, carbohidratos, grasas, fibra

def limpiar_pantalla():
    os.system('clear' if os.name == 'posix' else 'cls')

# --- BASE DE DATOS DE ALIMENTOS EN RD (v5.7 - SQLite + Estadísticas) ---
foods_db = {
    "1": {"nombre": "Pechuga de pollo (Cocinada)", "p": 31.0, "c": 0.0, "g": 3.6, "cal": 165},
    "2": {"nombre": "Muslo de pollo (Sin piel, Cocinado)", "p": 26.0, "c": 0.0, "g": 10.9, "cal": 207},
    "3": {"nombre": "Huevo entero (1 unidad grande ~50g)", "p": 6.3, "c": 0.4, "g": 5.0, "cal": 72},
    "4": {"nombre": "Carne de res molida magra (Cocinada)", "p": 28.0, "c": 0.0, "g": 12.0, "cal": 225},
    "5": {"nombre": "Bacalao (Desalado/Cocinado)", "p": 22.0, "c": 0.0, "g": 2.0, "cal": 105},
    "6": {"nombre": "Filete de Tilapia / Pescado blanco", "p": 23.0, "c": 0.0, "g": 2.5, "cal": 115},
    "7": {"nombre": "Arroz blanco (Cocinado)", "p": 2.7, "c": 28.0, "g": 0.3, "cal": 130},
    "8": {"nombre": "Plátano verde (Hervido)", "p": 1.0, "c": 26.0, "g": 0.2, "cal": 116},
    "9": {"nombre": "Plátano maduro (Hervido)", "p": 1.3, "c": 32.0, "g": 0.4, "cal": 140},
    "10": {"nombre": "Yuca / Yautía (Hervida)", "p": 1.2, "c": 38.0, "g": 0.3, "cal": 160},
    "11": {"nombre": "Avena entera (En crudo)", "p": 13.5, "c": 60.0, "g": 7.0, "cal": 365},
    "12": {"nombre": "Papa blanca (Hervida)", "p": 2.0, "c": 20.0, "g": 0.1, "cal": 87},
    "13": {"nombre": "Aguacate (100g)", "p": 2.0, "c": 8.5, "g": 14.7, "cal": 160},
    "14": {"nombre": "Yogur Griego natural (Sin azúcar)", "p": 10.0, "c": 3.6, "g": 0.4, "cal": 59},
    "15": {"nombre": "Hígado de pollo (Cocinado)", "p": 24.5, "c": 0.8, "g": 6.5, "cal": 167},
    "16": {"nombre": "Atún en agua (Drenado)", "p": 24.0, "c": 0.0, "g": 1.0, "cal": 110},
    "17": {"nombre": "Salmón (Cocinado)", "p": 20.0, "c": 0.0, "g": 13.0, "cal": 206},
    "18": {"nombre": "Whey Protein Isolate (1 scoop ~30g)", "p": 25.0, "c": 3.0, "g": 1.0, "cal": 120},
    "19": {"nombre": "Mangú (Plátano verde hervido y machacado)", "p": 1.5, "c": 32.0, "g": 0.5, "cal": 145},
    "20": {"nombre": "Queso Frito (Queso de freír, 100g)", "p": 22.0, "c": 2.0, "g": 28.0, "cal": 350},
    "21": {"nombre": "Salami Dominicano (Frito, 100g)", "p": 14.0, "c": 2.0, "g": 30.0, "cal": 330},
    "22": {"nombre": "Habichuelas Guisadas (100g)", "p": 7.0, "c": 15.0, "g": 1.0, "cal": 95},
    "23": {"nombre": "Arroz Blanco con Habichuelas (Plato típico, 1 plato)", "p": 8.0, "c": 45.0, "g": 3.0, "cal": 260},
    "24": {"nombre": "Yuca Frita (100g)", "p": 1.5, "c": 38.0, "g": 8.0, "cal": 230},
    "25": {"nombre": "Plátano Maduro Frito (Maduros, 100g)", "p": 1.5, "c": 35.0, "g": 14.0, "cal": 280},
    "26": {"nombre": "Huevo Hervido (1 unidad grande)", "p": 6.3, "c": 0.6, "g": 5.0, "cal": 78}
}

def guardar_plan_en_db(meta_txt, tmb, cal_finales, prot, carb, gras, fibra,
                       peso, altura, edad, sexo, texto_menu):
    """Guarda un plan nutricional en la base de datos SQLite."""
    try:
        plan_data = {
            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "objetivo": meta_txt,
            "tmb": round(tmb, 0),
            "calorias_diarias": round(cal_finales, 0),
            "proteinas_g": round(prot, 1),
            "carbohidratos_g": round(carb, 1),
            "grasas_g": round(gras, 1),
            "fibra_g": round(fibra, 1),
            "peso_kg": round(peso, 1),
            "altura_cm": round(altura, 1),
            "edad": edad,
            "sexo": sexo,
            "menu_texto": texto_menu
        }
        plan_id = db_nutricional.guardar_plan(plan_data)
        print(Fore.GREEN + f"\n[✔] ¡Éxito! Tu plan ha sido guardado en la base de datos (ID: {plan_id})")
        return plan_id
    except Exception as e:
        print(Fore.RED + f"\n[X] Error al guardar en la base de datos: {e}")
        return None

def listar_planes_guardados():
    """Lista planes guardados en la base de datos y retorna el ID seleccionado."""
    limpiar_pantalla()
    print(Fore.CYAN + Style.BRIGHT + "╔" + "═"*46 + "╗")
    print(Fore.CYAN + Style.BRIGHT + "║      📜 HISTORIAL DE PLANES GUARDADOS            ║")
    print(Fore.CYAN + Style.BRIGHT + "╚" + "═"*46 + "╝\n")

    planes = db_nutricional.listar_planes(limit=50)

    if not planes:
        print(Fore.YELLOW + "No hay planes guardados todavía.\n")
        input(Fore.WHITE + "Presiona ENTER para volver...")
        return None

    for i, plan in enumerate(planes, 1):
        print(f"{Fore.YELLOW}{i}. {Fore.WHITE}ID:{plan['id']} | {Fore.CYAN}{plan['fecha']}")
        print(f"   🎯 {plan['objetivo']} | 🔥 {plan['calorias_diarias']:.0f} kcal | "
              f"🥩 {plan['proteinas_g']}g | 🍞 {plan['carbohidratos_g']}g | 🥑 {plan['grasas_g']}g")

    print(Fore.RED + "\n0. Volver al Menú Principal")
    opc = input(Fore.YELLOW + "\n[+] Seleccione un número para ver detalles:~# ")

    if opc == '0':
        return None
    try:
        idx = int(opc) - 1
        if 0 <= idx < len(planes):
            return planes[idx]["id"]
        else:
            print(Fore.RED + "\n[X] Selección inválida.")
            time.sleep(1)
            return None
    except ValueError:
        print(Fore.RED + "\n[X] Opción inválida.")
        time.sleep(1)
        return None

def cargar_plan_desde_db(plan_id):
    """Muestra los detalles de un plan por su ID."""
    try:
        plan = db_nutricional.obtener_plan(plan_id)
        if not plan:
            print(Fore.RED + "\n[X] Plan no encontrado.")
            input(Fore.WHITE + "\nPresiona ENTER para volver...")
            return

        print(Fore.CYAN + Style.BRIGHT + "\n╔" + "═"*46 + "╗")
        print(Fore.CYAN + Style.BRIGHT + f"║  📄 PLAN CARGADO: ID {plan['id']}                ║")
        print(Fore.CYAN + Style.BRIGHT + "╚" + "═"*46 + "╝\n")
        print(Fore.WHITE + f" Fecha           : {plan['fecha']}")
        print(Fore.WHITE + f" Objetivo        : {plan['objetivo']}")
        print(Fore.WHITE + f" TMB             : {plan['tmb']} kcal")
        print(Fore.WHITE + f" Calorías        : {plan['calorias_diarias']} kcal")
        print(Fore.WHITE + f" Proteínas       : {plan['proteinas_g']} g")
        print(Fore.WHITE + f" Carbohidratos   : {plan['carbohidratos_g']} g")
        print(Fore.WHITE + f" Grasas          : {plan['grasas_g']} g")
        print(Fore.WHITE + f" Fibra           : {plan['fibra_g']} g")
        print(Fore.WHITE + f" Peso            : {plan['peso_kg']} kg")
        print(Fore.WHITE + f" Altura          : {plan['altura_cm']} cm")
        print(Fore.WHITE + f" Edad            : {plan['edad']} años")
        print(Fore.WHITE + f" Sexo            : {plan['sexo']}")
        print(Fore.GREEN + "\n" + "═"*48)
        print(Fore.WHITE + plan.get("menu_texto", "Sin menú disponible"))
        print(Fore.GREEN + "═"*48)
    except Exception as e:
        print(Fore.RED + f"\n[X] Error al cargar el plan: {e}")
    input(Fore.WHITE + "\nPresiona ENTER para volver al menú...")

def editar_plan_manual(proteina, carbohidratos, grasas, calorias_finales):
    limpiar_pantalla()
    print(Fore.CYAN + Style.BRIGHT + "╔" + "═"*46 + "╗")
    print(Fore.CYAN + Style.BRIGHT + "║      ✏️  EDITOR MANUAL DE MACROS                 ║")
    print(Fore.CYAN + Style.BRIGHT + "╚" + "═"*46 + "╝\n")
    print(Fore.WHITE + f" Valores actuales:\n")
    print(Fore.WHITE + f"  🔹 Proteínas : {proteina:.1f} g ({proteina*4:.0f} kcal)")
    print(Fore.WHITE + f"  🔹 Carbohidratos: {carbohidratos:.1f} g ({carbohidratos*4:.0f} kcal)")
    print(Fore.WHITE + f"  🔹 Grasas    : {grasas:.1f} g ({grasas*9:.0f} kcal)")
    print(Fore.WHITE + f"  🔹 Total kcal: {calorias_finales:.0f} kcal\n")

    print(Fore.YELLOW + "Ingrese nuevos valores (deje en blanco para no cambiar):\n")

    try:
        nueva_prot = input(Fore.WHITE + f" Proteínas (g) [{proteina:.1f}]: ").strip()
        proteina = float(nueva_prot) if nueva_prot else proteina

        nueva_carb = input(Fore.WHITE + f" Carbohidratos (g) [{carbohidratos:.1f}]: ").strip()
        carbohidratos = float(nueva_carb) if nueva_carb else carbohidratos

        nueva_gras = input(Fore.WHITE + f" Grasas (g) [{grasas:.1f}]: ").strip()
        grasas = float(nueva_gras) if nueva_gras else grasas

        calorias_calc = proteina * 4 + carbohidratos * 4 + grasas * 9
        print(Fore.GREEN + f"\n[✔] Nuevos macros calculados: {calorias_calc:.0f} kcal totales")
        print(Fore.GREEN + f"     Proteínas: {proteina:.1f} g | Carbohidratos: {carbohidratos:.1f} g | Grasas: {grasas:.1f} g")

        guardar = input(Fore.YELLOW + "\n[?] ¿Guardar este plan editado? (S/N): ").strip().upper()
        if guardar == 'S':
            meta_txt = "Plan Editado Manualmente"
            tmb_est = calorias_calc / 1.55
            fibra = (calorias_calc / 1000) * 14
            menu_impreso = generar_menu_diario(proteina, carbohidratos, grasas)
            # Usar valores por defecto para peso, altura, edad, sexo en edición manual
            guardar_plan_en_db(meta_txt, tmb_est, calorias_calc, proteina, carbohidratos, grasas, fibra,
                               peso=70.0, altura=175.0, edad=30, sexo='M', texto_menu=menu_impreso)
    except ValueError:
        print(Fore.RED + "\n[X] Valores inválidos.")
        time.sleep(1)

    input(Fore.WHITE + "\nPresiona ENTER para volver...")

def buscar_alimento_por_nombre(termino):
    """Busca alimentos por coincidencia de nombre (case-insensitive)."""
    resultados = []
    termino_lower = termino.lower()
    for key, info in foods_db.items():
        if termino_lower in info['nombre'].lower():
            resultados.append((key, info))
    return resultados

def mostrar_info_alimento(key, info):
    """Muestra la información detallada de un alimento."""
    limpiar_pantalla()
    print(Fore.CYAN + Style.BRIGHT + "╔" + "═"*46 + "╗")
    print(Fore.CYAN + Style.BRIGHT + f"║  🎯 INFORMACIÓN NUTRICIONAL: {info['nombre'].upper()} ║")
    print(Fore.CYAN + Style.BRIGHT + "╚" + "═"*46 + "╝\n")
    
    base_medida = "Por 1 Unidad (50g)" if key == "3" else "Por cada 100 gramos"
    print(Fore.WHITE + f" 📋 Base de medida: {Fore.YELLOW}{base_medida}")
    print(Fore.GREEN + "-"*48)
    print(Fore.WHITE + f"  🔹 Calorías     : {Fore.GREEN}{Style.BRIGHT}{info['cal']} kcal")
    print(Fore.WHITE + f"  🔹 Proteínas    : {Fore.MAGENTA}{info['p']} g")
    print(Fore.WHITE + f"  🔹 Carbohidratos: {Fore.MAGENTA}{info['c']} g")
    print(Fore.WHITE + f"  🔹 Grasas       : {Fore.MAGENTA}{info['g']} g")
    print(Fore.GREEN + "═"*48)
    
    print(Fore.YELLOW + "\n[?] ¿Quieres calcular los macros para una cantidad específica?")
    calc_cant = input(Fore.WHITE + "Introduce los gramos (o 'N' para volver a la lista): ").strip().lower()
    
    if calc_cant != 'n':
        try:
            gramos = float(calc_cant)
            factor = gramos / 50.0 if key == "3" else gramos / 100.0
            print(Fore.YELLOW + f"\n📊 RESULTADOS PARA {gramos}g DE {info['nombre'].upper()}:")
            print(Fore.WHITE + f"  -> Calorías     : {Fore.GREEN}{info['cal'] * factor:.1f} kcal")
            print(Fore.WHITE + f"  -> Proteínas    : {Fore.MAGENTA}{info['p'] * factor:.1f} g")
            print(Fore.WHITE + f"  -> Carbohidratos: {Fore.MAGENTA}{info['c'] * factor:.1f} g")
            print(Fore.WHITE + f"  -> Grasas       : {Fore.MAGENTA}{info['g'] * factor:.1f} g")
            print(Fore.GREEN + "-"*48)
            input("\nPresiona ENTER para continuar...")
        except ValueError:
            print(Fore.RED + "\n[X] Cantidad inválida.")
            time.sleep(1)

def plan_rapido():
    """Genera un plan rápido usando valores por defecto sin solicitar datos personales."""
    limpiar_pantalla()
    print(Fore.CYAN + Style.BRIGHT + "╔" + "═"*46 + "╗")
    print(Fore.CYAN + Style.BRIGHT + f"║      ⚡ PLAN RÁPIDO - VALORES POR DEFECTO        ║")
    print(Fore.CYAN + Style.BRIGHT + "╚" + "═"*46 + "╝\n")
    
    print(Fore.WHITE + "Este plan usa valores promedio de referencia:\n")
    print(Fore.WHITE + f"  👤 Peso        : 70 kg (154 lbs)")
    print(Fore.WHITE + f"  📏 Altura      : 175 cm")
    print(Fore.WHITE + f"  🎂 Edad        : 30 años")
    print(Fore.WHITE + f"  ⚥ Sexo       : Masculino\n")
    
    print(Fore.YELLOW + "Seleccione su objetivo:\n")
    print("1. Aumentar Masa Muscular (Volumen Limpio)")
    print("2. Tonificar / Recomposición")
    print("3. Bajar de Peso / Definición")
    print("4. Mantenimiento General")
    
    objetivo = input(Fore.YELLOW + "\nroot@rapido:~# ").strip()
    
    # Valores por defecto
    peso = 70.0
    altura = 175.0
    edad = 30
    sexo = 'M'
    
    tmb = calcular_tmb(peso, altura, edad, sexo)
    calorias_mantenimiento = tmb * 1.55
    calorias_finales = calorias_mantenimiento
    
    meta_txt = ""
    if objetivo == '1':
        meta_txt = "Aumentar Masa Muscular (Superávit)"
        calorias_finales = calorias_mantenimiento + 400
    elif objetivo == '2':
        meta_txt = "Tonificar / Recomposición"
        calorias_finales = calorias_mantenimiento
    elif objetivo == '3':
        meta_txt = "Bajar de Peso / Definición"
        calorias_finales = calorias_mantenimiento - 500
    else:
        meta_txt = "Mantenimiento General"

    proteina, carbohidratos, grasas, fibra = calcular_macros(peso, calorias_finales, objetivo)
    
    print("\n" + Fore.GREEN + "═"*48)
    print(Fore.GREEN + Style.BRIGHT + "       🎯 PLAN RÁPIDO GENERADO EXITOSAMENTE       ")
    print(Fore.GREEN + "═"*48)
    print(Fore.WHITE + f" Objetivo Seleccionado : {Fore.CYAN}{meta_txt}")
    print(Fore.WHITE + f" TMB (Gasto en Reposo) : {tmb:.0f} kcal")
    print(Fore.WHITE + f" Calorías Diarias Meta : {Fore.GREEN}{Style.BRIGHT}{calorias_finales:.0f} kcal")
    print(Fore.GREEN + "-"*48)
    
    print(Fore.YELLOW + Style.BRIGHT + " DESGLOSE DE MACRONUTRIENTES:")
    print(Fore.WHITE + f"  🔹 Proteínas    : {Fore.MAGENTA}{proteina:.1f} g  {Fore.BLACK}({proteina*4:.0f} kcal)")
    print(Fore.WHITE + f"  🔹 Carbohidratos: {Fore.MAGENTA}{carbohidratos:.1f} g  {Fore.BLACK}({carbohidratos*4:.0f} kcal)")
    print(Fore.WHITE + f"  🔹 Grasas       : {Fore.MAGENTA}{grasas:.1f} g  {Fore.BLACK}({grasas*9:.0f} kcal)")
    print(Fore.WHITE + f"  🔹 Fibra Mínima : {Fore.CYAN}{fibra:.1f} g")
    print(Fore.GREEN + "═"*48)
    
    menu_impreso = generar_menu_diario(proteina, carbohidratos, grasas)
    
    print(Fore.YELLOW + "\n[?] ¿Desea guardar este plan en la base de datos?")
    print("1. Sí, guardar en SQLite")
    print("2. No, solo mostrar")
    exportar = input(Fore.WHITE + "root@export:~# ").strip()

    if exportar == '1':
        guardar_plan_en_db(meta_txt, tmb, calorias_finales, proteina, carbohidratos, grasas, fibra,
                           peso=peso, altura=altura, edad=edad, sexo=sexo, texto_menu=menu_impreso)
    else:
        print(Fore.YELLOW + "\n[!] Plan no guardado.")
    
    input(Fore.WHITE + "\nPresiona ENTER para volver al menú...")

def mostrar_estadisticas():
    """Muestra estadísticas agregadas de todos los planes guardados."""
    limpiar_pantalla()
    print(Fore.CYAN + Style.BRIGHT + "╔" + "═"*46 + "╗")
    print(Fore.CYAN + Style.BRIGHT + "║      📊 ESTADÍSTICAS DE PLANES GUARDADOS         ║")
    print(Fore.CYAN + Style.BRIGHT + "╚" + "═"*46 + "╝\n")

    try:
        stats = db_nutricional.obtener_estadisticas()

        print(Fore.WHITE + f" Total de planes guardados : {Fore.GREEN}{stats['total_planes']}")
        print(Fore.WHITE + f" Promedio de calorías      : {Fore.GREEN}{stats['promedio_calorias']} kcal")
        print(Fore.WHITE + f" Promedio de proteínas     : {Fore.GREEN}{stats['promedio_proteinas']} g")
        print(Fore.WHITE + f" Promedio de carbohidratos : {Fore.GREEN}{stats['promedio_carbohidratos']} g")
        print(Fore.WHITE + f" Promedio de grasas        : {Fore.GREEN}{stats['promedio_grasas']} g")
        print(Fore.WHITE + f" Promedio de peso          : {Fore.GREEN}{stats['promedio_peso']} kg")
        print()

        if stats["objetivos_distribucion"]:
            print(Fore.YELLOW + " Distribución por objetivo:")
            for item in stats["objetivos_distribucion"]:
                print(f"   🎯 {item['objetivo']}: {Fore.GREEN}{item['count']} plan(es)")
        else:
            print(Fore.YELLOW + " No hay datos de objetivos todavía.")
    except Exception as e:
        print(Fore.RED + f"\n[X] Error al obtener estadísticas: {e}")

    print(Fore.GREEN + "\n" + "═"*48)
    input(Fore.WHITE + "\nPresiona ENTER para volver al menú...")

def consultar_tabla_alimentos():
    while True:
        limpiar_pantalla()
        print(Fore.GREEN + Style.BRIGHT + "╔" + "═"*46 + "╗")
        print(Fore.GREEN + Style.BRIGHT + "║        🔎 TABLA DE ALIMENTOS INTERACTIVA          ║")
        print(Fore.GREEN + Style.BRIGHT + "╚" + "═"*46 + "╝")
        print(Fore.WHITE + "Opciones:\n")
        print(Fore.YELLOW + "1. " + Fore.WHITE + "Listar todos los alimentos")
        print(Fore.YELLOW + "2. " + Fore.WHITE + "Buscar alimento por nombre")
        print(Fore.RED + "0. " + Fore.WHITE + "Volver al Menú Principal")
        
        opc = input(Fore.YELLOW + "\n[+] Seleccione una opción:~# ").strip()
        
        if opc == '0':
            break
        elif opc == '1':
            limpiar_pantalla()
            print(Fore.GREEN + Style.BRIGHT + "╔" + "═"*46 + "╗")
            print(Fore.GREEN + Style.BRIGHT + "║        📋 LISTA DE ALIMENTOS DISPONIBLES         ║")
            print(Fore.GREEN + Style.BRIGHT + "╚" + "═"*46 + "╝")
            print(Fore.WHITE + "Selecciona un número para ver sus macros:\n")
            
            for key, info in foods_db.items():
                if key == "3":
                    print(f"{Fore.YELLOW}{key}. {Fore.WHITE}{info['nombre']}")
                else:
                    print(f"{Fore.YELLOW}{key}. {Fore.WHITE}{info['nombre']} (100g)")
                    
            print(Fore.RED + "\n0. Volver")
            sub_opc = input(Fore.YELLOW + "\n[+] Ingrese el número del alimento:~# ").strip()
            
            if sub_opc == '0':
                continue
            elif sub_opc in foods_db:
                mostrar_info_alimento(sub_opc, foods_db[sub_opc])
            else:
                print(Fore.RED + "\n[X] Código de alimento no registrado.")
                time.sleep(1)
                
        elif opc == '2':
            limpiar_pantalla()
            print(Fore.GREEN + Style.BRIGHT + "╔" + "═"*46 + "╗")
            print(Fore.GREEN + Style.BRIGHT + "║        🔍 BÚSQUEDA DE ALIMENTOS                  ║")
            print(Fore.GREEN + Style.BRIGHT + "╚" + "═"*46 + "╝")
            termino = input(Fore.WHITE + "\nIngrese nombre o parte del nombre del alimento:~# ").strip()
            
            if not termino:
                print(Fore.RED + "\n[X] Término de búsqueda vacío.")
                time.sleep(1)
                continue
                
            resultados = buscar_alimento_por_nombre(termino)
            
            if not resultados:
                print(Fore.RED + f"\n[X] No se encontraron alimentos que coincidan con '{termino}'.")
                time.sleep(1)
                continue
            
            print(Fore.GREEN + f"\n[✔] Se encontraron {len(resultados)} resultado(s):\n")
            for i, (key, info) in enumerate(resultados, 1):
                medida = "unidad" if key == "3" else "100g"
                print(f"{Fore.YELLOW}{i}. {Fore.WHITE}{info['nombre']} ({medida}) - {Fore.GREEN}{info['cal']} kcal | {Fore.MAGENTA}P:{info['p']}g C:{info['c']}g G:{info['g']}g")
            
            print(Fore.RED + "\n0. Volver")
            sub_opc = input(Fore.YELLOW + "\n[+] Seleccione un número para ver detalles o 0 para volver:~# ").strip()
            
            if sub_opc == '0':
                continue
            try:
                idx = int(sub_opc) - 1
                if 0 <= idx < len(resultados):
                    key, info = resultados[idx]
                    mostrar_info_alimento(key, info)
                else:
                    print(Fore.RED + "\n[X] Selección inválida.")
                    time.sleep(1)
            except ValueError:
                print(Fore.RED + "\n[X] Opción inválida.")
                time.sleep(1)
        else:
            print(Fore.RED + "\n[X] Opción inválida.")
            time.sleep(1)

def generar_menu_diario(proteina_total, carbo_total, grasa_total):
    print(Fore.GREEN + "\n[!] ELIJA EL PRESUPUESTO PARA SU MENÚ DE HOY:")
    print("1. Económico (Huevo, Hígado, Atún, Víveres) - *Bajo Costo y Práctico*")
    print("2. Estándar (Pechuga de pollo, Arroz, Huevos, Avena) - *El clásico del Gym*")
    print("3. Premium (Carne de res, Pescado, Yogur Griego, Batido Whey) - *Mayor variedad*")
    
    presupuesto = input(Fore.YELLOW + "\nroot@budget_select:~# ")
    
    limpiar_pantalla()
    print(Fore.YELLOW + Style.BRIGHT + "╔" + "═"*46 + "╗")
    print(Fore.YELLOW + Style.BRIGHT + "║      🥞 PROPUESTA DE MENÚ ADAPTADO A TU BOLSILLO ║")
    print(Fore.YELLOW + Style.BRIGHT + "╚" + "═"*46 + "╝\n")

    texto_txt_archivo = ""

    if presupuesto == '1':
        print(Fore.GREEN + "🟢 MODO: ECONÓMICO (Guerreando en el colmado)\n")
        avena_g = (carbo_total * 0.25) / 0.60
        higado_g = (proteina_total * 0.35) / 0.245
        arroz_almuerzo = (carbo_total * 0.40) / 0.28
        viveres_merienda = (carbo_total * 0.15) / 0.26
        # Matemática ajustada al valor proteico del atún drenado (24g por cada 100g)
        atun_g = (proteina_total * 0.30) / 0.24
        viveres_cena = (carbo_total * 0.20) / 0.26

        menu_layout = (
            f"🍳 Comida 1: Desayuno\n"
            f"   ├─ 4 Huevos enteros (Proteína completa económica)\n"
            f"   └─ {avena_g:.0f}g de Avena entera en agua\n\n"
            f"🍗 Comida 2: Almuerzo (¡Bomba de Hierro y Zinc!)\n"
            f"   ├─ {higado_g:.0f}g de Hígado de pollo (Peso cocinado, baratísimo y denso en nutrientes)\n"
            f"   └─ {arroz_almuerzo:.0f}g de Arroz blanco\n\n"
            f"🍠 Comida 3: Merienda (Post-Entreno)\n"
            f"   ├─ 3 Huevos duros (Solo las claras para regular grasas)\n"
            f"   └─ {viveres_merienda:.0f}g de Plátano verde o Rulo hervido\n\n"
            f"🐟 Comida 4: Cena (Rápida y Magra)\n"
            f"   ├─ {atun_g:.0f}g de Atún en agua (Drenado, aprox. 1 lata grande o 2 pequeñas)\n"
            f"   └─ {viveres_cena:.0f}g de Yuca o Yautía hervida"
        )
        print(menu_layout)
        texto_txt_archivo = "\n📋 PROPUESTA DE MENÚ: ECONÓMICO\n\n" + menu_layout
        
    elif presupuesto == '3':
        print(Fore.MAGENTA + "👑 MODO: PREMIUM (Quincena cobrada)\n")
        avena_g = (carbo_total * 0.20) / 0.60
        carne_premium = (proteina_total * 0.35) / 0.30
        arroz_premium = (carbo_total * 0.35) / 0.28
        pescado_premium = (proteina_total * 0.30) / 0.24
        papas_cena = (carbo_total * 0.25) / 0.20

        menu_layout = (
            f"🥞 Comida 1: Desayuno\n"
            f"   ├─ 4 Huevos enteros + 2 claras adicionales\n"
            f"   ├─ {avena_g:.0f}g de Avena con leche de almendras\n"
            f"   └─ 1 Puñado de almendras o nueces\n\n"
            f"🥩 Comida 2: Almuerzo (Fuerza Pura)\n"
            f"   ├─ {carne_premium:.0f}g de Carne de res molida magra o Bistec de bola\n"
            f"   ├─ {arroz_premium:.0f}g de Arroz integral o blanco\n"
            f"   └─ 1/2 Aguacate mediano\n\n"
            f"🥛 Comida 3: Post-Entrenamiento\n"
            f"   ├─ 1 Scoop de Whey Protein Isolate\n"
            f"   └─ 2 Guineos maduros grandes\n\n"
            f"🐟 Comida 4: Cena Ligera\n"
            f"   ├─ {pescado_premium:.0f}g de Filete de Salmón o Tilapia a la plancha\n"
            f"   └─ {papas_cena:.0f}g de Papas hervidas o puré\n\n"
            f"🍦 Comida 5: Antes de dormir\n"
            f"   └─ 250g de Yogur Griego natural con miel"
        )
        print(menu_layout)
        texto_txt_archivo = "\n📋 PROPUESTA DE MENÚ: PREMIUM\n\n" + menu_layout

    else:
        print(Fore.CYAN + "🔵 MODO: ESTÁNDAR (El menú clásico de gimnasio)\n")
        avena_g = (carbo_total * 0.20) / 0.60
        pechuga_almuerzo = (proteina_total * 0.35) / 0.31
        arroz_almuerzo = (carbo_total * 0.40) / 0.28
        pechuga_cena = (proteina_total * 0.30) / 0.31
        viveres_cena = (carbo_total * 0.20) / 0.26

        menu_layout = (
            f"🍳 Comida 1: Desayuno\n"
            f"   ├─ 4 Huevos enteros\n"
            f"   └─ {avena_g:.0f}g de Avena entera (peso en crudo)\n\n"
            f"🍗 Comida 2: Almuerzo\n"
            f"   ├─ {pechuga_almuerzo:.0f}g de Pechuga de pollo (peso cocinado)\n"
            f"   └─ {arroz_almuerzo:.0f}g de Arroz blanco (peso cocinado)\n\n"
            f"🍌 Comida 3: Merienda / Post-Entrenamiento\n"
            f"   ├─ 1 Scoop de Proteína en Polvo (Whey)\n"
            f"   └─ 1 Plátano maduro o 2 guineos maduros\n\n"
            f"🍠 Comida 4: Cereal o Cena\n"
            f"   ├─ {pechuga_cena:.0f}g de Pechuga de pollo o Pescado\n"
            f"   └─ {viveres_cena:.0f}g de Plátano verde o Yautía hervida"
        )
        print(menu_layout)
        texto_txt_archivo = "\n📋 PROPUESTA DE MENÚ: ESTÁNDAR\n\n" + menu_layout

    print(Fore.YELLOW + "\n" + "═"*48)
    return texto_txt_archivo

def ejecutar_calculo():
    limpiar_pantalla()
    print(Fore.CYAN + Style.BRIGHT + "╔" + "═"*46 + "╗")
    print(Fore.CYAN + Style.BRIGHT + "║      📊 BIO-CALCULADOR DE MACRONUTRIENTES v5.7   ║")
    print(Fore.CYAN + Style.BRIGHT + "╚" + "═"*46 + "╝")

    try:
        sexo = input(Fore.YELLOW + "[?] Sexo (M para Masculino / F para Femenino): ").strip().upper()
        if sexo not in ['M', 'F']:
            sexo = 'M'
            
        print(Fore.GREEN + "\n[!] SELECCIONE UNIDAD DE PESO:")
        print("1. Libras (lbs)")
        print("2. Kilogramos (kg)")
        unidad_peso = input(Fore.YELLOW + "root@weight_select:~# ")
        
        if unidad_peso == '1':
            peso_lbs = float(input(Fore.YELLOW + "\n[?] Introduzca su peso en Libras (ejemplo: 208): "))
            if not validar_rango(peso_lbs, 0.5, 1000):
                raise ValueError("Peso fuera de rango válido (0.5 - 1000 lbs)")
            peso = peso_lbs / 2.20462
        else:
            peso = float(input(Fore.YELLOW + "\n[?] Introduzca su peso en Kilogramos: "))
            if not validar_rango(peso, 0.5, 300):
                raise ValueError("Peso fuera de rango válido (0.5 - 300 kg)")
            
        print(Fore.GREEN + "\n[!] SELECCIONE UNIDAD DE ALTURA:")
        print("1. Pies y Pulgadas (ejemplo: 6'2\")")
        print("2. Centímetros (cm)")
        unidad_altura = input(Fore.YELLOW + "root@height_select:~# ")
        
        if unidad_altura == '1':
            print(Fore.YELLOW + "\n[?] Introduzca la altura:")
            pies = int(input("    Pies: "))
            pulgadas = int(input("    Pulgadas: "))
            altura = (pies * 30.48) + (pulgadas * 2.54)
            if not validar_rango(altura, 60, 275):
                raise ValueError("Altura fuera de rango válido (60 - 275 cm)")
        else:
            altura = float(input(Fore.YELLOW + "\n[?] Altura en centímetros (ejemplo: 188): "))
            if not validar_rango(altura, 60, 275):
                raise ValueError("Altura fuera de rango válido (60 - 275 cm)")
            
        edad = int(input(Fore.YELLOW + "\n[?] Edad en años: "))
        if not validar_rango(edad, 10, 100):
            raise ValueError("Edad fuera de rango válido (10 - 100 años)")
    except ValueError as e:
        print(Fore.RED + f"\n[X] Error: {e}")
        input("\nPresiona ENTER para reiniciar...")
        return

    print(Fore.GREEN + "\n[!] SELECCIONE SU OBJETIVO ACTUAL:")
    print("1. Aumentar Masa Muscular (Volumen Limpio)")
    print("2. Tonificar / Recomposición (Mantener peso, perder grasa)")
    print("3. Bajar de Peso / Definición (Déficit calórico)")
    
    objetivo = input(Fore.YELLOW + "\nroot@nutri_deck:~# ")

    tmb = calcular_tmb(peso, altura, edad, sexo)
    calorias_mantenimiento = tmb * 1.55
    calorias_finales = calorias_mantenimiento

    meta_txt = ""
    if objetivo == '1':
        meta_txt = "Aumentar Masa Muscular (Superávit)"
        calorias_finales = calorias_mantenimiento + 400
    elif objetivo == '2':
        meta_txt = "Tonificar / Recomposición"
        calorias_finales = calorias_mantenimiento
    elif objetivo == '3':
        meta_txt = "Bajar de Peso / Definición"
        calorias_finales = calorias_mantenimiento - 500
    else:
        meta_txt = "Mantenimiento General"

    proteina, carbohidratos, grasas, fibra = calcular_macros(peso, calorias_finales, objetivo)

    print("\n" + Fore.GREEN + "═"*48)
    print(Fore.GREEN + Style.BRIGHT + "       🎯 PLAN NUTRICIONAL GENERADO EXITOSAMENTE       ")
    print(Fore.GREEN + "═"*48)
    print(Fore.WHITE + f" Objetivo Seleccionado : {Fore.CYAN}{meta_txt}")
    print(Fore.WHITE + f" TMB (Gasto en Reposo) : {tmb:.0f} kcal")
    print(Fore.WHITE + f" Calorías Diarias Meta : {Fore.GREEN}{Style.BRIGHT}{calorias_finales:.0f} kcal")
    print(Fore.GREEN + "-"*48)
    
    print(Fore.YELLOW + Style.BRIGHT + " DESGLOSE DE MACRONUTRIENTES:")
    print(Fore.WHITE + f"  🔹 Proteínas    : {Fore.MAGENTA}{proteina:.1f} g  {Fore.BLACK}({proteina*4:.0f} kcal)")
    print(Fore.WHITE + f"  🔹 Carbohidratos: {Fore.MAGENTA}{carbohidratos:.1f} g  {Fore.BLACK}({carbohidratos*4:.0f} kcal)")
    print(Fore.WHITE + f"  🔹 Grasas       : {Fore.MAGENTA}{grasas:.1f} g  {Fore.BLACK}({grasas*9:.0f} kcal)")
    print(Fore.WHITE + f"  🔹 Fibra Mínima : {Fore.CYAN}{fibra:.1f} g")
    print(Fore.GREEN + "═"*48)
    
    menu_impreso = generar_menu_diario(proteina, carbohidratos, grasas)
    
    print(Fore.YELLOW + "\n[?] ¿Desea guardar este plan en la base de datos?")
    print("1. Sí, guardar en SQLite")
    print("2. No, solo mostrar")
    exportar = input(Fore.WHITE + "root@export:~# ").strip()

    if exportar == '1':
        guardar_plan_en_db(meta_txt, tmb, calorias_finales, proteina, carbohidratos, grasas, fibra,
                           peso=peso, altura=altura, edad=edad, sexo=sexo, texto_menu=menu_impreso)
    else:
        print(Fore.YELLOW + "\n[!] Plan no guardado.")

def main_app():
    while True:
        limpiar_pantalla()
        print(Fore.CYAN + Style.BRIGHT + "╔" + "═"*46 + "╗")
        print(Fore.CYAN + Style.BRIGHT + "║          📌 BIO-NUTRI DECK - MENÚ PRINCIPAL       ║")
        print(Fore.CYAN + Style.BRIGHT + "╚" + "═"*46 + "╝")
        print(Fore.WHITE + "1. Calcular Nuevo Plan de Macros y Menú Adaptado")
        print(Fore.WHITE + "2. Plan Rápido (valores por defecto)")
        print(Fore.WHITE + "3. Consultar Tabla de Alimentos")
        print(Fore.WHITE + "4. Ver Historial de Planes Guardados")
        print(Fore.WHITE + "5. Editar Plan Manualmente")
        print(Fore.WHITE + "6. Ver Estadísticas Guardadas")
        print(Fore.RED + "7. Salir de la aplicación")
        
        opcion = input(Fore.YELLOW + "\n[+] Seleccione una opción:~# ")
        
        if opcion == '1':
            ejecutar_calculo()
            print(Fore.GREEN + "\n[?] ¿QUÉ DESEA HACER AHORA?")
            print("1. Volver al Menú Principal")
            print("2. Salir de la aplicación")
            sig_paso = input(Fore.YELLOW + "\nroot@navigation:~# ")
            if sig_paso == '2':
                print(Fore.RED + "\n[*] Cerrando sesión de nutrición... ¡A entrenar duro!")
                break
        elif opcion == '2':
            plan_rapido()
        elif opcion == '3':
            consultar_tabla_alimentos()
        elif opcion == '4':
            plan_id = listar_planes_guardados()
            if plan_id is not None:
                cargar_plan_desde_db(plan_id)
        elif opcion == '5':
            # Valores por defecto para el editor manual
            editar_plan_manual(proteina=100.0, carbohidratos=300.0, grasas=60.0, calorias_finales=2200.0)
        elif opcion == '6':
            mostrar_estadisticas()
        elif opcion == '7':
            print(Fore.RED + "\n[*] Cerrando sesión de nutrición... ¡A entrenar duro!")
            break
        else:
            print(Fore.RED + "\n[X] Opción inválida.")
            time.sleep(1)

if __name__ == "__main__":
    main_app()

