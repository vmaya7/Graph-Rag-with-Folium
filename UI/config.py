# -*- coding: utf-8 -*-
"""
Archivo de Configuración Centralizado para el Chatbot de Restaurantes.

Aquí se definen todos los parámetros de conexión, APIs, prompts,
y configuraciones visuales para la aplicación.
"""

# --- 1. Configuración del Backend (Servidor) ---
# Define la configuración para tu servidor web (ej. FastAPI, Flask)
BACKEND_SERVER_CONFIG = {
    "host": "0.0.0.0",  # Escucha en todas las interfaces (accesible en la red)
    "port": 8000,       # Puerto estándar para APIs web
}



# --- 2. Configuración de Neo4j ---
# Credenciales y detalles de conexión para tu base de datos Neo4j
NEO4J_CONFIG = {
    "uri": "bolt://localhost:7687",  # Reemplaza con tu URI de Bolt (ej. Aura)
    "username": "neo4j",                             # Usuario de la base de datos
    "password": "test1234",         # Tu contraseña de Neo4j
    "database": "neo4j",                             # Nombre de la base de datos (usualmente 'neo4j' por defecto)
}

# --- 3. Configuración del LLM (Modelo de Lenguaje) ---
# Configuración para el LLM que usará LangChain (ej. OpenAI, Gemini)
LLM_CONFIG = {
    "provider": "openai",  # O "gemini", "huggingface", etc.
    "model_name": "gpt-3.5-turbo", # Modelo específico a utilizar
    "api_key": "",
    "temperature": 0.0,    # 0.0 para respuestas deterministas (bueno para Cypher)
}

# --- 4. Configuración de LangChain (GraphCypherQAChain) ---
# Parámetros para la cadena de QA específica de grafos
LANGCHAIN_QA_CONFIG = {
    "verbose": True,   # Imprime los pasos intermedios (útil para depuración)
    "top_k": 10,       # Número máximo de resultados a devolver por la consulta
    "allow_dangerous_requests": True, # Permite consultas que podrían modificar datos (usar con precaución)
}

# --- 5. Plantilla de Prompt para Cypher (GENERIC_CYPHER_PROMPT) ---
# Esta es la plantilla maestra que instruye al LLM sobre cómo generar Cypher.
# Es crucial para guiar al modelo y manejar casos especiales.
QA_PROMPT_TEMPLATE = """
Eres un asistente foodie de Querétaro. Responde en español con tono cálido y cercano.
Estilo:
- Máx. 2–4 frases + bullets si ayuda.
- 1–2 emojis como máximo.
- Si hay restaurantes, destaca 2–3 con: nombre + zona/por qué ir.
- Ofrece una siguiente acción (“¿Filtrar por barato/cerca/vegano/terraza?”).
- No inventes datos: usa SOLO el CONTEXTO.


PREGUNTA:
{question}

CONTEXTO:
{context}

Responde:
"""


CYPHER_PROMPT_TEMPLATE = """
Eres experto en Cypher para Neo4j 5.
Devuelve **solo** un bloque:
```cypher
<CONSULTA CYPHER>
```
Reglas:

    • IMPORTANTE: Siempre que devuelvas nodos :Restaurant (ej. r:Restaurant), debes incluir las siguientes propiedades en el RETURN, si están disponibles:
        - `r.title AS name` (o `n.title AS name`, etc.)
        - `r.address AS address`
        - `r.location.latitude AS latitude`
        - `r.location.longitude AS longitude`
        - `r.rating AS rating`
        - `r.reviews AS total_ratings`
        - `r.user_review AS review`
    •   Para “caminando / a pie / cerca / distancia”, usar arista no dirigida :IS_WALKING.
    •   Para las reseñas, asegurate que el review del usuario esté en español. Sino es el caso, traducelo al español. 
    •   Si el usuario pide los restaurantes que están caminando de un restaurante, usa la siguietne query como base: 
         MATCH (v:Restaurant) WHERE toLower(v.title)=toLower($TITLE)
        MATCH (v)-[e:IS_WALKING]-(n:Restaurant)
-        RETURN n.title AS name, round(e.meters) AS meters, round(e.time_min,1) AS minutes, n.address AS address, n.location.latitude AS latitude, n.location.longitude AS longitude, n.user_review AS review, n.rating AS rating, n.reviews AS total_ratings, n.price_level AS price_level
+        RETURN n.title AS name, round(e.meters) AS meters, round(e.time_min,1) AS minutes, n.address AS address, n.location.latitude AS latitude, n.location.longitude AS longitude, n.user_review AS review, n.rating AS rating, n.reviews AS total_ratings, n.price_level AS price_level
        ORDER BY meters ASC
    •   Ancla por título de restaurante:
        MATCH (v:Restaurant) WHERE toLower(v.title) = toLower($TITLE)
    •   Si mencionan “Querétaro/Qro/Queretarock”, hace referencia a "Santiago de Querétaro".
    •   Ordena y limita resultados razonablemente.
    •   Usa toLower() para comparaciones de strings insensibles a mayúsculas/minúsculas.

    • Reglas de Títulos: Para comparar títulos de restaurantes, SIEMPRE usa toLower() en ambos lados de la comparación.

        MAL: WHERE r.title = 'VegCo'

        MAL: WHERE toLower(r.title) = 'VegCo'

        BIEN: WHERE toLower(r.title) = 'vegco'

        BIEN: WHERE toLower(r.title) = toLower('VegCo')


    •   Regla de Existencia**: Para comprobar si una propiedad existe, **NUNCA** uses `exists(propiedad)`. Usa `propiedad IS NOT NULL`.
           MAL: `WHERE exists(r.review_text)`
           BIEN: `WHERE r.review_text IS NOT NULL`

        
Esquema:
{schema}

Pregunta:
{question}
"""

# --- 6. Configuración Visual del Frontend (Chatbot UI) ---
# Parámetros que definen el aspecto y los mensajes iniciales del chat
FRONTEND_CONFIG = {
    "page_title": "Restaurante-Bot Qro",
    "window_title": "Chat de Restaurantes 🍽️",
    "chatbot_title": "Tu Asistente de Restaurantes en Querétaro",
    "welcome_message": "¡Hola! Soy tu asistente para encontrar los mejores restaurantes en Querétaro. ¿Qué te apetece hoy?",
    "user_avatar": "👤", # Puede ser un emoji o una URL a una imagen
    "bot_avatar": "🤖",  # Puede ser un emoji o una URL a una imagen
    "theme_primary_color": "#FF4B4B", # Color principal (ej. para botones y acentos)
    "theme_background_color": "#F0F2F6", # Color de fondo de la app
    "theme_font": "Inter, sans-serif", # Fuente principal
    "cors_origin": "*", 
}

# --- 7. Configuración de Folium (Mapas) ---
# Parámetros por defecto para generar los mapas de Folium
FOLIUM_CONFIG = {
    "default_location": [20.5888, -100.3899], # Coordenadas de Santiago de Querétaro
    "default_zoom": 13,                        # Nivel de zoom inicial
    "map_tiles": "CartoDB positron",           # Estilo del mapa (otros: 'OpenStreetMap', 'Stamen Terrain')
    "marker_color_restaurant": "blue",         # Color para marcadores de restaurantes
    "marker_icon_restaurant": "cutlery",       # Icono de FontAwesome para restaurantes
    "marker_color_user_location": "red",       # Color para la ubicación del usuario (si se implementa)
    "marker_icon_user_location": "user",       # Icono para el usuario
        # El zoom inicial del mapa (14 es un buen nivel para una zona)
    "zoom_start": 14,
    
    # El estilo del mapa (ej. 'CartoDB positron', 'OpenStreetMap')
    "tiles": "CartoDB positron",           
    
    # Color del marcador para restaurantes
    "marker_color_restaurant": "blue",         
    
    # Icono (de FontAwesome) para el marcador
    "marker_icon_restaurant": "cutlery",      
    "map_height_px": 400,
}

