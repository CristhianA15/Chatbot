from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import sqlite3
import unicodedata
import re
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from werkzeug.security import generate_password_hash, check_password_hash
from fuzzywuzzy import fuzz

app = Flask(__name__)
app.secret_key = os.urandom(24)
DATABASE = 'faqs.db'
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def query_db(query, args=(), one=False):
    conn = get_db()
    cursor = conn.execute(query, args)
    results = cursor.fetchall()
    conn.close()
    return (results[0] if results else None) if one else results

def execute_db(query, args=()):
    conn = sqlite3.connect(DATABASE)
    conn.execute(query, args)
    conn.commit()
    conn.close()


def load_intents_from_db():
   
    print("Cargando intenciones desde la base de datos...")
    intents_dict = {}
    training_data = query_db("SELECT intent, phrase FROM intents_training")
    
    for row in training_data:
        intent = row['intent']
        phrase = row['phrase']
        if intent not in intents_dict:
            intents_dict[intent] = []
        intents_dict[intent].append(phrase)
    
    print(f"Carga completa. {len(intents_dict)} intenciones encontradas.")
    return intents_dict

intents = load_intents_from_db()




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


X_train = []
y_train = []

def clean_text(text):
    text = text.lower()
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    text = re.sub(r'[^\w\s]', '', text)
    return text

for intent, phrases in intents.items():
    for phrase in phrases:
        X_train.append(clean_text(phrase))
        y_train.append(intent)

vectorizer = TfidfVectorizer()
X_train_vec = vectorizer.fit_transform(X_train)

clf = MultinomialNB()
clf.fit(X_train_vec, y_train)

def classify_intent(message):
 
    processed_message = clean_text(message)

   
    for intent, phrases in intents.items():
        for phrase in phrases:
            if processed_message == clean_text(phrase):
                print(f"Coincidencia exacta encontrada para la intención: {intent}") 
                return intent

 
    message_vec = vectorizer.transform([processed_message])
    
    probas = clf.predict_proba(message_vec)[0]
    confidence = max(probas)
    intent = clf.classes_[probas.argmax()]

    print(f"Intención detectada por el modelo: '{intent}' con confianza de {confidence:.2f}")

    if confidence >= 0.4:
        return intent
    

    return None




@app.route('/')
def index():
    if 'username' in session:
        historial = query_db("SELECT pregunta, respuesta FROM chat_history ORDER BY id DESC LIMIT 5")
        return render_template('index.html', historial=historial)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = query_db('SELECT * FROM users WHERE username = ?', [username], one=True)
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return redirect(url_for('index'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get("mensaje", "")
    response = ""


    intent = classify_intent(user_message)
    if intent and intent in tramites:
 
        response = "\n".join(tramites[intent])
    else:

        faqs = query_db("SELECT pregunta, respuesta FROM faqs")
        best_match_score = 0
        best_faq_response = None
        similarity_threshold = 80
        
        processed_user_message = clean_text(user_message)

        for faq in faqs:
            processed_question = clean_text(faq['pregunta'])
            similarity = fuzz.ratio(processed_user_message, processed_question)
            if similarity > best_match_score and similarity >= similarity_threshold:
                best_match_score = similarity
                best_faq_response = faq['respuesta']
        
        if best_faq_response:
            response = best_faq_response
        else:
     
            response = "Lo siento, no entendí tu solicitud. ¿Podrías reformularla o consultar otra opción?"


    execute_db("INSERT INTO chat_history (pregunta, respuesta) VALUES (?, ?)", (user_message, response))
    return jsonify({"respuesta": response})

if __name__ == '__main__':
    # You should have a setup script to create the DB and tables
    # For example:
    # with get_db() as conn:
    #     conn.execute('''
    #         CREATE TABLE IF NOT EXISTS users (
    #             id INTEGER PRIMARY KEY AUTOINCREMENT,
    #             username TEXT UNIQUE NOT NULL,
    #             password TEXT NOT NULL
    #         );
    #     ''')
    #     conn.execute('''
    #         CREATE TABLE IF NOT EXISTS faqs (
    #             id INTEGER PRIMARY KEY AUTOINCREMENT,
    #             pregunta TEXT NOT NULL,
    #             respuesta TEXT NOT NULL
    #         );
    #     ''')
    #     conn.execute('''
    #         CREATE TABLE IF NOT EXISTS chat_history (
    #             id INTEGER PRIMARY KEY AUTOINCREMENT,
    #             pregunta TEXT NOT NULL,
    #             respuesta TEXT NOT NULL,
    #             timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    #         );
    #     ''')
    app.run(debug=True)