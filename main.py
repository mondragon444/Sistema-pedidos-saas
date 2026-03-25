import random
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import re
from datetime import datetime, time

app = FastAPI()

# ========================
# CORS (para el frontend)
# ========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================
# Base de datos
# ========================
pedidos = []
pedidos_temporales = {}

# ========================
# MENÚ COMPLETO (TUYO)
# ========================
menu_taqueria = {
    "info_establecimiento": {
        "nombre": "La Fortuna Taquería",
        "direccion": "Av. Guanajuato Villas del Sol #334, Juventino Rosas, Gto.",
        "telefono": "412 127 5358",
        "eslogan": "Si la vida te da limones, pónselos a los tacos..."
    },
    "especialidades": [
        {"nombre": "La Fortuna", "precio": 135.0, "descripcion": "Costilla asada, queso gratinado, pastor, champiñones y guarnición"},
        {"nombre": "La Lumbre", "precio": 95.0, "descripcion": "Chile poblano, cebolla, tocino, costilla, pastor, bistec, chuleta, aguacate y queso"},
        {"nombre": "La Tablita", "precio": 95.0, "descripcion": "Tocino, cebolla, poblano, chuleta, pastor, aguacate y queso"},
        {"nombre": "Arrachera Asada", "precio": 140.0, "descripcion": "Lechuga, aguacate, jitomate, papa con mantequilla y cebollitas"},
        {"nombre": "Si te Llenas", "precio": 95.0, "descripcion": "Poblano, cebolla, tocino, chorizo, pastor, chuleta, costilla, bistec y queso"}
    ],
    "por_taco": {
        "pastor_o_chorizo": {"sin_queso": 12.0, "con_queso": 15.0},
        "bistec_costilla_chuleta_campechano_champiñon": {"sin_queso": 15.0, "con_queso": 18.0},
        "arrachera": {"sin_queso": 25.0, "con_queso": 28.0}
    },
    "orden_4_tacos": {
        "carnes_estandar": {"sin_queso": 75.0, "con_queso": 80.0},
        "arrachera": {"sin_queso": 85.0, "con_queso": 90.0}
    },
    "papas_asadas": {
        "mantequilla": 30.0,
        "con_queso": 55.0,
        "con_carne_estandar_y_queso": 75.0,
        "con_arrachera": 85.0,
        "combinada": 80.0
    },
    "otros": {
        "quesadillas": {"sola": 22.0, "con_carne": 27.0, "arrachera": 32.0},
        "gringas": {"estandar": 45.0, "arrachera": 60.0},
        "sincronizadas_orden_2": {"estandar": 75.0, "arrachera": 85.0},
        "alambres_con_queso": {"estandar": 90.0, "combinado": 95.0, "arrachera": 100.0, "especial": 95.0},
        "volcanes_orden_3": {"estandar": 55.0, "arrachera": 70.0},
        "tortas": {"estandar": 50.0, "arrachera": 60.0}
    },
    "complementos": {
        "cebollitas": 30.0,
        "orden_piña": 30.0,
        "orden_aguacate": 30.0,
        "tortillas_harina_5pzas": 15.0,
        "chiles_asados_6pzas": 30.0
    },
    "bebidas": {
        "refresco_vidrio": 25.0,
        "refresco_taparrosca_600ml": 27.0,
        "jugos_lata": 25.0,
        "agua_horchata_medio_litro": 22.0,
        "agua_horchata_litro": 40.0,
        "agua_natural_600ml": 22.0,
        "refresco_1_5L": 40.0
    }
}

# ========================
# LISTAS DE APOYO
# ========================
tipos_carne = [
    "pastor", "bistec", "costilla", "chuleta",
    "chorizo", "arrachera", "campechano", "pollo"
]

productos_base = [
    "taco", "tacos", "gringa", "gringas",
    "quesadilla", "quesadillas", "torta", "tortas",
    "volcan", "volcanes", "alambre", "alambres"
]

# ========================
# Modelo
# ========================
class Pedido(BaseModel):
    cliente: str
    producto: str
    estado: str = "pendiente"

# ========================
# Horario
# ========================
HORARIO_APERTURA = time(11, 0)
HORARIO_CIERRE = time(3, 0)

def dentro_horario():
    ahora = datetime.now().time()
    if HORARIO_APERTURA <= HORARIO_CIERRE:
        return HORARIO_APERTURA <= ahora <= HORARIO_CIERRE
    else:
        return ahora >= HORARIO_APERTURA or ahora <= HORARIO_CIERRE

# ========================
# EXTRAER PEDIDOS (CORREGIDO)
# ========================
def extraer_pedidos(texto):
    texto = texto.lower()
    palabras = texto.split()

    resultado = []
    i = 0

    while i < len(palabras):
        if palabras[i].isdigit():
            cantidad = int(palabras[i])
            producto = "taco"
            tipo = None

            if i + 1 < len(palabras) and palabras[i+1] in productos_base:
                producto = palabras[i+1]
                i += 1

            if i + 1 < len(palabras) and palabras[i+1] in tipos_carne:
                tipo = palabras[i+1]
                i += 1

            resultado.append({
                "cantidad": cantidad,
                "producto": producto,
                "tipo": tipo
            })

        i += 1

    return resultado

# ========================
# Función de respuestas predefinidas con flujo completo
# ========================
def responder(texto: str, cliente_id: str):
    texto = texto.lower()

    # ====================
    # FUERA DE HORARIO
    # ====================
    if not dentro_horario():
        return "⏰ Ahorita estamos cerrados, abrimos de 2pm a 3am 😄"

    # ====================
    # SI YA HAY PEDIDO TEMPORAL
    # ====================
    if cliente_id in pedidos_temporales:
        temp_items = pedidos_temporales[cliente_id]

        # -------- CONFIRMAR PEDIDO --------
        if texto in ["si", "sí"]:
            faltantes = [i for i in temp_items if not i.get("tipo")]

            if faltantes:
                productos = ", ".join(set(i["producto"] for i in faltantes))
                return f"❗ Aún necesito que me digas de qué son: {productos}"

            pedidos_confirmados = []
            for item in temp_items:
                nuevo = {
                    "id": len(pedidos) + 1,
                    "cliente": cliente_id,
                    "producto": f'{item["cantidad"]} x {item["producto"]} de {item["tipo"]}',
                    "estado": "pendiente"
                }
                pedidos.append(nuevo)
                pedidos_confirmados.append(nuevo)

            del pedidos_temporales[cliente_id]

            resumen = ", ".join(p["producto"] for p in pedidos_confirmados)
            return f"✅ Pedido confirmado: {resumen}"

        # -------- NO CONFIRMAR --------
        if "no" in texto:
            return "Va 😄 dime qué más quieres agregar"

        # -------- AGREGAR TIPO FALTANTE --------
        for item in temp_items:
            if not item.get("tipo"):
                for tipo in tipos_carne:
                    if tipo in texto:
                        item["tipo"] = tipo

        # verificar otra vez si ya está completo
        faltantes = [i for i in temp_items if not i.get("tipo")]
        if not faltantes:
            resumen = ", ".join(
                f'{i["cantidad"]} x {i["producto"]} de {i["tipo"]}'
                for i in temp_items
            )
            return f"Tu pedido es: {resumen}. ¿Lo confirmas? (sí/no)"

        else:
            productos = ", ".join(set(i["producto"] for i in faltantes))
            return f"Me falta saber de qué son: {productos}"

    # ====================
    # SALUDOS
    # ====================
    if any(p in texto for p in ["hola", "buenas", "que onda", "hey", "holi"]):
        return random.choice([
            "Hola 👋 ¿qué se te antoja hoy?",
            "Buenas 😄 ¿vas por unos tacos o algo más llenador?",
            "Qué tal 👌 ¿te paso el menú o ya sabes qué quieres?",
            "Hola 🔥 aquí estamos, ¿qué te animas a pedir?",
            "¡Qué onda! ¿para cenar algo rico o solo estás viendo?"
        ])

# ====================
# MENÚ
# ====================
if any(p in texto for p in ["menu", "menú", "carta", "lista"]):
    return {
        "tipo": "imagenes",
        "contenido": [
            "https://raw.githubusercontent.com/mondragon444/Sistema-pedidos-saas/main/fortuna1.jpg",
            "https://raw.githubusercontent.com/mondragon444/Sistema-pedidos-saas/main/fortuna2.jpg"
        ]
    }
    # ====================
    # NUEVO PEDIDO
    # ====================
    if any(p in texto for p in productos_base):
        items = extraer_pedidos(texto)

        if not items:
            return "No entendí bien tu pedido 😅 ¿puedes escribirlo así? Ej: 3 tacos pastor"

        pedidos_temporales[cliente_id] = items

        faltantes = [i for i in items if i["tipo"] is None]

        if faltantes:
            productos = ", ".join(set(i["producto"] for i in faltantes))
            return f"He registrado tu pedido 😄 pero me falta saber de qué son: {productos}"

        resumen = ", ".join(
            f'{i["cantidad"]} x {i["producto"]} de {i["tipo"]}'
            for i in items
        )

        return f"Tu pedido es: {resumen}. ¿Lo confirmas? (sí/no)"

    # ====================
    # DEFAULT
    # ====================
    return random.choice([
        "No te entendí 😅 ¿quieres ver el menú o pedir algo?",
        "¿Te paso el menú o quieres ordenar?",
        "Estoy para ayudarte 😄 ¿qué se te antoja?",
        "¿Buscas tacos o algo del menú? 🔥"
    ])


# ========================
# RUTAS DEL SERVIDOR
# ========================

@app.get("/")
def inicio():
    return {"mensaje": "Servidor funcionando 🚀"}


@app.post("/pedido")
def crear_pedido(pedido: Pedido):
    nuevo = {
        "id": len(pedidos) + 1,
        "cliente": pedido.cliente,
        "producto": pedido.producto,
        "estado": pedido.estado
    }
    pedidos.append(nuevo)
    return {"mensaje": "Pedido creado", "pedido": nuevo}


@app.get("/pedidos")
def ver_pedidos():
    return pedidos


@app.put("/pedido/{id}")
def actualizar_estado(id: int, estado: str):
    for pedido in pedidos:
        if pedido["id"] == id:
            pedido["estado"] = estado
            return {"mensaje": "Estado actualizado", "pedido": pedido}
    return {"error": "Pedido no encontrado"}


@app.post("/mensaje")
def recibir_mensaje(cliente_id: str, texto: str):
    respuesta = responder(texto, cliente_id)
    return {"respuesta": respuesta}
