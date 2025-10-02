from flask import Flask, jsonify, render_template, request, redirect, url_for, session
import mysql.connector

app = Flask(__name__)
app.secret_key = "clave_super_secreta_123"  

# Conexión a MySQL
def obtener_opciones():
    conexion = mysql.connector.connect(
        host="localhost",       
        user="root",
        password="Admin",
        database="eps_chatbot"
    )
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT id, texto, padre_id, pdf_url FROM opciones")
    resultados = cursor.fetchall()
    conexion.close()
    return resultados

def obtener_faqs():
    conexion = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Admin",
        database="eps_chatbot"
    )
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT pregunta, respuesta FROM faqs")
    resultados = cursor.fetchall()
    conexion.close()
    return resultados


# Validar usuario en DB
def validar_usuario(username, password):
    conexion = mysql.connector.connect(
        host="localhost",       
        user="root",
        password="Admin",
        database="eps_chatbot"
    )
    cursor = conexion.cursor(dictionary=True)
    query = "SELECT * FROM usuarios WHERE username = %s AND password = %s"
    cursor.execute(query, (username, password))
    usuario = cursor.fetchone()
    conexion.close()
    return usuario

# Página de inicio de sesión
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        usuario = validar_usuario(username, password)
        
        if usuario:
            session["usuario"] = usuario["username"]
            return redirect(url_for("index"))
        return render_template("login.html", error="Credenciales inválidas")
    return render_template("login.html")

@app.route("/index")
def index():
    if "usuario" not in session:
        return redirect(url_for("login"))   
    opciones = obtener_opciones()
    usuario = session["usuario"]
    return render_template("index.html", opciones=opciones, usuario=usuario)

@app.route("/logout")
def logout():
    session.pop("usuario", None)
    return redirect(url_for("login"))  
@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "").strip().lower()

    if user_message == "faqs":
        faqs = obtener_faqs()
        return jsonify({"type": "faqs", "data": faqs})

    return jsonify({"type": "text", "data": "Lo siento, no entendí tu mensaje."})


if __name__ == "__main__":
    app.run(debug=True)
