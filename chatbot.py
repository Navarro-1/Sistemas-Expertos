from flask import Flask, request, jsonify
import sqlite3

# Crear la aplicación Flask
app = Flask(__name__)

# Inicializar la base de datos
def init_db():
    with sqlite3.connect("chatbot.db") as conn:
        cursor = conn.cursor()
        # Tabla de conocimientos: pregunta y respuesta
        cursor.execute('''CREATE TABLE IF NOT EXISTS knowledge (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            question TEXT UNIQUE,
                            answer TEXT)''')
        # Tabla de registro de conversaciones
        cursor.execute('''CREATE TABLE IF NOT EXISTS conversation_log (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_message TEXT,
                            bot_response TEXT)''')
        conn.commit()

# Ruta para la raíz
@app.route('/')
def home():
    return "Bienvenido al Chatbot. Usa /chat para interactuar."

# Obtener respuesta desde la base de datos
def get_answer(question):
    try:
        with sqlite3.connect("chatbot.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT answer FROM knowledge WHERE question = ?", (question,))
            result = cursor.fetchone()
            # Si existe respuesta y no es 'Pendiente de respuesta', la devuelve
            return result[0] if result and result[0] != "Pendiente de respuesta" else None
    except sqlite3.Error as e:
        print(f"Error al acceder a la base de datos: {e}")
        return None

# Guardar o actualizar el conocimiento
def store_knowledge(question, answer):
    try:
        with sqlite3.connect("chatbot.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT answer FROM knowledge WHERE question = ?", (question,))
            existing = cursor.fetchone()
            if existing:
                # Actualiza la respuesta si ya existe
                cursor.execute("UPDATE knowledge SET answer = ? WHERE question = ?", (answer, question))
            else:
                # Inserta el nuevo conocimiento
                cursor.execute("INSERT INTO knowledge (question, answer) VALUES (?, ?)", (question, answer))
            conn.commit()
    except sqlite3.Error as e:
        print(f"Error al almacenar conocimiento: {e}")

# Registrar la conversación en la base de datos
def log_conversation(user_message, bot_response):
    try:
        with sqlite3.connect("chatbot.db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO conversation_log (user_message, bot_response) VALUES (?, ?)", (user_message, bot_response))
            conn.commit()
    except sqlite3.Error as e:
        print(f"Error al registrar la conversación: {e}")

# Ruta para manejar el chat
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "").strip()

    # Busca una respuesta ya aprendida
    answer = get_answer(user_message)
    if answer:
        response = answer
    else:
        response = "No sé qué responder. ¿Me enseñas?"
        # Guarda la pregunta con estado pendiente si no existe aún
        store_knowledge(user_message, "Pendiente de respuesta")
    
    # Registra la conversación
    log_conversation(user_message, response)

    return jsonify({"response": response})

# Ruta para aprender nuevas respuestas
@app.route("/learn", methods=["POST"])
def learn():
    data = request.json
    question = data.get("question", "").strip()
    answer = data.get("answer", "").strip()

    if question and answer:
        store_knowledge(question, answer)
        return jsonify({"response": "Gracias, he aprendido algo nuevo."})
    return jsonify({"response": "No puedo aprender sin una pregunta y respuesta válidas."})

# Ejecutar la aplicación Flask
if __name__ == "__main__":
    init_db()
    app.run(debug=True)