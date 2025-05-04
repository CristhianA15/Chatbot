from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import sqlite3
import unicodedata
from fuzzywuzzy import fuzz
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Genera una clave secreta para la sesión
DATABASE = 'faqs.db'


# Diccionario de trámites con sus pasos
tramites = {
    "afiliación": [
        "Paso 1: Reunir los documentos necesarios (documento de identidad, etc.)",
        "Paso 2: Ingresar al portal de Compensar y seleccionar 'Afiliación'.",
        "Paso 3: Diligenciar el formulario de afiliación.",
        "Paso 4: Adjuntar los documentos requeridos.",
        "Paso 5: Enviar la solicitud y esperar confirmación."
    ],
    "citas médicas": [
        "Paso 1: Ingresar al portal transaccional de Compensar.",
        "Paso 2: Ir a la sección de salud y seleccionar 'Agendar cita'.",
        "Paso 3: Elegir el tipo de cita (general, odontológica, etc.).",
        "Paso 4: Seleccionar fecha, hora y profesional disponible.",
        "Paso 5: Confirmar la cita."
    ],
    "cancelación de citas": [
        "Paso 1: Ingresar a tu cuenta en el portal de Compensar.",
        "Paso 2: Ir a 'Mis citas' o 'Citas programadas'.",
        "Paso 3: Buscar la cita que deseas cancelar.",
        "Paso 4: Dar clic en 'Cancelar cita'.",
        "Paso 5: Confirmar la cancelación."
    ],
    "actualización de datos": [
        "Paso 1: Accede a tu cuenta en el portal de Compensar.",
        "Paso 2: Dirígete a la sección de 'Perfil' o 'Datos personales'.",
        "Paso 3: Edita la información que deseas actualizar.",
        "Paso 4: Guarda los cambios y verifica que se hayan aplicado correctamente."
    ]
}

faqs_eps_compensar = [
    ("¿Cómo me afilio a Compensar EPS?", "Para afiliarte a Compensar EPS, generalmente debes ingresar a su portal web oficial en la sección de 'Afiliación' y seguir los pasos indicados. También puedes hacerlo a través de los formularios disponibles en sus oficinas de atención al usuario."),
    ("¿Qué documentos necesito para afiliarme a Compensar?", "Los documentos comunes para la afiliación incluyen tu documento de identidad (cédula de ciudadanía, tarjeta de identidad, etc.), el formulario de afiliación diligenciado y, dependiendo de tu situación laboral, certificados de ingresos o afiliación a una caja de compensación."),
    ("¿Cómo agendo una cita médica en Compensar?", "Puedes agendar citas médicas a través del portal transaccional de Compensar, su aplicación móvil o llamando a las líneas de atención telefónica. Dentro de estas plataformas, busca la sección de 'Agendamiento de citas' y sigue los pasos."),
    ("¿Qué tipos de citas puedo agendar en Compensar?", "Generalmente puedes agendar citas de medicina general, odontología, algunas especialidades médicas, y citas para programas de promoción y prevención, según la disponibilidad y tu plan de salud."),
    ("¿Cómo cancelo o reprogramo una cita en Compensar?", "Para cancelar o reprogramar una cita, debes acceder a tu cuenta en el portal transaccional o la app de Compensar, ir a la sección de 'Mis citas' o 'Citas programadas' y buscar la opción para cancelar o reprogramar la cita específica. También puedes comunicarte a las líneas de atención."),
    ("¿Qué hago en caso de una urgencia médica con Compensar?", "En caso de una urgencia médica, debes dirigirte al servicio de urgencias de la red de prestadores de Compensar más cercano. Puedes consultar la red de urgencias en su portal web o app."),
    ("¿Cómo actualizo mis datos de contacto en Compensar?", "Puedes actualizar tus datos de contacto (dirección, teléfono, correo electrónico, etc.) ingresando a tu perfil en el portal transaccional de Compensar o a través de la sección de 'Actualización de datos' en su página web o app."),
    ("¿Cómo obtengo un certificado de afiliación a Compensar?", "El certificado de afiliación generalmente está disponible para descarga en el portal transaccional de Compensar. Busca la sección de 'Certificados' o 'Documentos' dentro de tu cuenta."),
    ("¿Qué cubre mi plan de salud de Compensar?", "La cobertura de tu plan de salud depende del tipo de plan que tengas (Plan de Beneficios en Salud - PBS o planes complementarios). Puedes consultar los detalles de tu cobertura en el portal web de Compensar o comunicándote con sus líneas de atención."),
    ("¿Dónde puedo encontrar las oficinas de atención al usuario de Compensar?", "Puedes encontrar la ubicación y horarios de las oficinas de atención al usuario de Compensar en su página web oficial, en la sección de 'Puntos de atención' o 'Contáctenos'." )
]


def eliminar_acentos(texto):
    texto = texto.lower()
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS faqs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pregunta TEXT UNIQUE,
            respuesta TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pregunta TEXT NOT NULL,
            respuesta TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM faqs")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT OR IGNORE INTO faqs (pregunta, respuesta) VALUES (?, ?)", faqs_eps_compensar)
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        hashed_password = generate_password_hash("%R1RTYwvJJCm1E")  
        cursor.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", ("admin", hashed_password))

    conn.commit()
    conn.close()



def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def query_db(query, args=(), one=False):
    conn = get_db()
    cursor = conn.execute(query, args)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return (results[0] if results else None) if one else results

def execute_db(query, args=()):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(query, args)
    conn.commit()
    cursor.close()
    conn.close()

@app.route('/')
def index():
    init_db()
    if 'username' in session:
        historial = query_db("SELECT pregunta, respuesta FROM chat_history ORDER BY id DESC LIMIT 5")
        return render_template('index.html', historial=historial)
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    init_db()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = query_db('SELECT * FROM users WHERE username = ?', [username], one=True)
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Credenciales inválidas')
    else:
        return render_template('login.html')



@app.route('/chat', methods=['POST'])
def chat():
    init_db()
    mensaje_original = request.json.get("mensaje", "")
    mensaje_procesado = eliminar_acentos(mensaje_original)
    respuesta = ""
    umbral_similitud = 80

    
    faqs = query_db("SELECT pregunta, respuesta FROM faqs")
    mejor_similitud = 0
    mejor_respuesta_faq = None
    #lista de tramites
    if "tramites" in mensaje_procesado:
        lista_tramites = [tramite.title() for tramite in tramites]
        respuesta = "Los trámites disponibles son: " + ", ".join(lista_tramites) + "."
        execute_db("INSERT INTO chat_history (pregunta, respuesta) VALUES (?, ?)", (mensaje_original, respuesta))
        return jsonify({"respuesta": respuesta})
    #lista de faqs
    if "faqs" in mensaje_procesado:
        respuesta = "Preguntas Frecuentes:\n"
        for faq in faqs_eps_compensar:
            respuesta += f"- {faq[0]}\n"  # Agrega cada pregunta a la respuesta
        execute_db("INSERT INTO chat_history (pregunta, respuesta) VALUES (?, ?)", (mensaje_original, respuesta))
        return jsonify({"respuesta": respuesta})

    for faq in faqs:
        pregunta_procesada = eliminar_acentos(faq['pregunta'])
        similitud = fuzz.ratio(mensaje_procesado, pregunta_procesada)
        if similitud > mejor_similitud and similitud >= umbral_similitud:
            mejor_similitud = similitud
            mejor_respuesta_faq = faq['respuesta']
            break # Importante: Salir del bucle si se encuentra una coincidencia
    if mejor_respuesta_faq:
        respuesta = mejor_respuesta_faq
        execute_db("INSERT INTO chat_history (pregunta, respuesta) VALUES (?, ?)", (mensaje_original, respuesta))
        return jsonify({"respuesta": respuesta})


    for tramite, pasos in tramites.items():
        tramite_procesado = eliminar_acentos(tramite)
        similitud = fuzz.ratio(mensaje_procesado, tramite_procesado)
        if similitud >= umbral_similitud:
            respuesta = f"Pasos para el trámite de {tramite.title()}:\n" + "\n".join(pasos)
            execute_db("INSERT INTO chat_history (pregunta, respuesta) VALUES (?, ?)", (mensaje_original, respuesta))
            return jsonify({"respuesta": respuesta})

    respuesta = "Lo siento, no entendí tu solicitud. Por favor intenta con otro trámite disponible o pregunta algo diferente."
    execute_db("INSERT INTO chat_history (pregunta, respuesta) VALUES (?, ?)", (mensaje_original, respuesta))
    return jsonify({"respuesta": respuesta})
    


if __name__ == '__main__':
    app.run(debug=True)
