# 🤖 Chatbot de Trámites para EPS

Este proyecto implementa un chatbot web interactivo orientado a adultos mayores, diseñado para asistir en la realización de trámites frecuentes con una EPS (Entidad Promotora de Salud). El chatbot proporciona respuestas automatizadas en lenguaje natural y funcionalidades de accesibilidad como lectura en voz alta y ajuste de tamaño de fuente.

## 🧠 Funcionalidades

- Chat en lenguaje natural entre el usuario y el asistente.
- Lectura en voz alta de las respuestas del chatbot (opcional).
- Accesibilidad mejorada: aumento y disminución del tamaño de fuente.
- Envío de mensajes mediante el botón o al presionar Enter.
- Mensaje de bienvenida con comandos sugeridos.
- Backend con Python (Flask) para recibir preguntas y procesar respuestas.

## 📁 Estructura del Proyecto
📦 chatbot-eps
├── app.py # Servidor Flask (backend)
├── faqs.db #Base de datos SQLite
├── templates/
│ └── index.html # Interfaz web del chatbot
├── README.md # Este archivo

## 🚀 Cómo ejecutar el proyecto

1. **Clona el repositorio:**

git clone https://github.com/CristhianA15/Chatbot.git
cd Chatbot

2. Instala las dependencias:
pip install Flask
pip install fuzzywuzzy python-Levenshtein

3. Ejecuta la aplicación
python app.py

4. Abre tu navegador

http://localhost:5000

🛠 Tecnologías utilizadas
Frontend: HTML5, CSS3, JavaScript (DOM)

Backend: Python 3, Flask

API de voz: Web Speech API (SpeechSynthesis)
