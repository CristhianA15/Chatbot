from flask import Flask, jsonify, render_template, request, redirect, url_for, session
import mysql.connector

app = Flask(__name__)
app.secret_key = "clave_super_secreta_123"  

# --- Funciones CRUD para la Base de Conocimiento ---

def obtener_opciones_con_padre():
    """ Obtiene todas las opciones y el texto de su padre para mostrar en el admin. """
    conexion = mysql.connector.connect(host="localhost", user="root", password="Admin", database="eps_chatbot")
    cursor = conexion.cursor(dictionary=True)
    # Usamos un LEFT JOIN para obtener el nombre del padre, si existe.
    query = """
        SELECT o.id, o.texto, o.padre_id, o.respuesta_final, p.texto AS padre_texto
        FROM opciones o
        LEFT JOIN opciones p ON o.padre_id = p.id
        ORDER BY o.id
    """
    cursor.execute(query)
    opciones = cursor.fetchall()
    conexion.close()
    return opciones

def crear_opcion(texto, padre_id, respuesta_final):
    """ Inserta una nueva opción en la base de datos. """
    conexion = mysql.connector.connect(host="localhost", user="root", password="Admin", database="eps_chatbot")
    cursor = conexion.cursor()
    # Si padre_id es una cadena vacía o 'None', lo convertimos a NULL para la DB.
    if not padre_id or padre_id == 'None':
        padre_id = None
    query = "INSERT INTO opciones (texto, padre_id, respuesta_final) VALUES (%s, %s, %s)"
    cursor.execute(query, (texto, padre_id, respuesta_final))
    conexion.commit()
    conexion.close()

def actualizar_opcion(opcion_id, texto, padre_id, respuesta_final):
    """ Actualiza una opción existente. """
    conexion = mysql.connector.connect(host="localhost", user="root", password="Admin", database="eps_chatbot")
    cursor = conexion.cursor()
    if not padre_id or padre_id == 'None':
        padre_id = None
    query = "UPDATE opciones SET texto = %s, padre_id = %s, respuesta_final = %s WHERE id = %s"
    cursor.execute(query, (texto, padre_id, respuesta_final, opcion_id))
    conexion.commit()
    conexion.close()

def eliminar_opcion(opcion_id):
    """ Elimina una opción. ¡Cuidado con los huérfanos! """
    conexion = mysql.connector.connect(host="localhost", user="root", password="Admin", database="eps_chatbot")
    cursor = conexion.cursor()
    # Primero, desvinculamos los hijos para evitar errores de clave foránea.
    # Una mejor estrategia a largo plazo sería una eliminación en cascada o una advertencia en la UI.
    cursor.execute("UPDATE opciones SET padre_id = NULL WHERE padre_id = %s", (opcion_id,))
    cursor.execute("DELETE FROM opciones WHERE id = %s", (opcion_id,))
    conexion.commit()
    conexion.close()
# Conexión a MySQL
def obtener_opciones():
    conexion = mysql.connector.connect(
        host="localhost",       
        user="root",
        password="Admin",
        database="eps_chatbot"
    )
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT id, texto, padre_id, respuesta_final FROM opciones")
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

def crear_pqrs(usuario_id, asunto, mensaje):
    conexion = mysql.connector.connect(host="localhost", user="root", password="Admin", database="eps_chatbot")
    cursor = conexion.cursor()
    query = "INSERT INTO pqrs (usuario_id, asunto, mensaje) VALUES (%s, %s, %s)"
    cursor.execute(query, (usuario_id, asunto, mensaje))
    conexion.commit()
    conexion.close()

def obtener_pqrs_por_usuario(usuario_id):
    conexion = mysql.connector.connect(host="localhost", user="root", password="Admin", database="eps_chatbot")
    # Usamos dictionary=True para manejar los resultados fácilmente en la plantilla
    cursor = conexion.cursor(dictionary=True)
    query = "SELECT asunto, mensaje, respuesta, estado, fecha_creacion, fecha_respuesta FROM pqrs WHERE usuario_id = %s ORDER BY fecha_creacion DESC"
    cursor.execute(query, (usuario_id,))
    pqrs_list = cursor.fetchall()
    conexion.close()
    return pqrs_list

def obtener_todas_las_pqrs():
    conexion = mysql.connector.connect(host="localhost", user="root", password="Admin", database="eps_chatbot")
    cursor = conexion.cursor(dictionary=True)
    # Obtenemos también el nombre de usuario para mostrarlo al empleado
    query = """
        SELECT p.id, u.username, p.asunto, p.mensaje, p.estado, p.fecha_creacion
        FROM pqrs p
        JOIN usuarios u ON p.usuario_id = u.id
        ORDER BY p.fecha_creacion DESC
    """
    cursor.execute(query)
    pqrs_list = cursor.fetchall()
    conexion.close()
    return pqrs_list

def responder_pqrs(pqrs_id, respuesta):
    conexion = mysql.connector.connect(host="localhost", user="root", password="Admin", database="eps_chatbot")
    cursor = conexion.cursor()
    query = "UPDATE pqrs SET respuesta = %s, estado = 'Resuelta', fecha_respuesta = NOW() WHERE id = %s"
    cursor.execute(query, (respuesta, pqrs_id))
    conexion.commit()
    conexion.close()

# Página de inicio de sesión

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        usuario = validar_usuario(username, password)
        
        if usuario:
            # Guardamos los datos clave en la sesión
            session["usuario"] = usuario["username"]
            session["id"] = usuario["id"]
            session["rol"] = usuario["rol"]
            
          
            if usuario["rol"] == "empleado":
                # Si el rol es 'empleado', va a la página de gestión de PQRS
                return redirect(url_for("pqrs"))
            elif usuario["rol"] == "empleado-admin":
                # Si es admin de conocimiento, va a su panel
                return redirect(url_for("conocimiento"))
            else:
                # Si es un usuario normal, va al chat
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
@app.route("/pqrs", methods=["GET", "POST"])
def pqrs():
    if "usuario" not in session:
        return redirect(url_for("login"))

   
    usuario_rol = session.get("rol", "usuario")
    usuario_id = session.get("id")

    if usuario_rol == "empleado":
        # Lógica para el empleado
        if request.method == "POST":
            pqrs_id = request.form["pqrs_id"]
            respuesta = request.form["respuesta"]
            responder_pqrs(pqrs_id, respuesta)
            return redirect(url_for("pqrs"))

        todas_las_pqrs = obtener_todas_las_pqrs()
        return render_template("pqrs_empleado.html", pqrs_list=todas_las_pqrs)
    else:
        # Lógica para el usuario estándar
        if request.method == "POST":
            asunto = request.form["asunto"]
            mensaje = request.form["mensaje"]
            crear_pqrs(usuario_id, asunto, mensaje)
            return redirect(url_for("pqrs"))

        mis_pqrs = obtener_pqrs_por_usuario(usuario_id)
        return render_template("pqrs_usuario.html", mis_pqrs=mis_pqrs, usuario=session["usuario"])
@app.route("/conocimiento", methods=["GET", "POST"])
def conocimiento():
    # --- Seguridad: Solo los empleados pueden acceder ---
    if session.get("rol") != "empleado-admin":
        return redirect(url_for("login"))

    # --- Lógica para manejar el envío de formularios (Crear, Actualizar, Eliminar) ---
    if request.method == "POST":
        action = request.form.get("action")

        if action == "crear":
            texto = request.form["texto"]
            padre_id = request.form["padre_id"]
            respuesta_final = request.form["respuesta_final"]
            crear_opcion(texto, padre_id, respuesta_final)
        
        elif action == "actualizar":
            opcion_id = request.form["opcion_id"]
            texto = request.form["texto"]
            padre_id = request.form["padre_id"]
            respuesta_final = request.form["respuesta_final"]
            actualizar_opcion(opcion_id, texto, padre_id, respuesta_final)

        elif action == "eliminar":
            opcion_id = request.form["opcion_id"]
            eliminar_opcion(opcion_id)
        
        # Usamos el patrón Post/Redirect/Get para evitar reenvíos de formulario
        return redirect(url_for("conocimiento"))

    # --- Lógica para mostrar la página (GET) ---
    opciones = obtener_opciones_con_padre()
    return render_template("conocimiento_admin.html", opciones=opciones)


if __name__ == "__main__":
    app.run(debug=True)
