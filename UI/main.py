import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager 
#from langchain.memory import ConversationBufferWindowMemory, ConversationSummaryBufferMemory

# from neo4j import GraphDatabase 
import folium
from langchain_community.graphs import Neo4jGraph
from langchain_openai import ChatOpenAI
from langchain.chains import GraphCypherQAChain
from langchain.prompts import PromptTemplate
# --- Importación de Configuración ---
try:
    from config import (
        NEO4J_CONFIG,
        LLM_CONFIG,
        FRONTEND_CONFIG,
        FOLIUM_CONFIG,
        CYPHER_PROMPT_TEMPLATE,
        QA_PROMPT_TEMPLATE
    )
except ImportError:
    print("ERROR: No se pudo encontrar el archivo config.py.")
    print("Asegúrate de que config.py esté en el mismo directorio.")
    exit()

# --- Modelos de Datos (Pydantic) ---

class ChatRequest(BaseModel):
    """Define la estructura de la petición de chat entrante."""
    query: str

class ChatResponse(BaseModel):
    """Define la estructura de la respuesta del chat saliente."""
    answer: str
    cypher_query: str
    map_html: Optional[str] = None

# --- Variables Globales (se inicializan en 'lifespan') ---

graph: Optional[Neo4jGraph] = None
qa_chain: Optional[GraphCypherQAChain] = None


# --- 3. Evento de Inicio (Lifespan) ---
# Esta es la forma moderna de manejar el 'startup' y 'shutdown'

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Se ejecuta al iniciar el servidor.
    Inicializa la conexión a Neo4j, el LLM y la cadena QA.
    """
    global graph, qa_chain
    print("Iniciando el servidor...")

    try:
        # 1. Inicializar Conexión a Neo4j (Forma moderna)
        print(f"Conectando a Neo4j en: {NEO4J_CONFIG['uri']}...")
        graph = Neo4jGraph(
            url=NEO4J_CONFIG["uri"],
            username=NEO4J_CONFIG["username"],
            password=NEO4J_CONFIG["password"]
        )
        print("Conexión a Neo4j exitosa.")

        # 2. Inicializar LLM
        print(f"Inicializando LLM (Modelo: {LLM_CONFIG['model_name']})...")
        llm = ChatOpenAI(
            model=LLM_CONFIG["model_name"],
            temperature=LLM_CONFIG["temperature"],
            api_key=LLM_CONFIG["api_key"]
        )

        llm_default = ChatOpenAI(
            model=LLM_CONFIG["model_name"],
            temperature=LLM_CONFIG["temperature"],
            api_key=LLM_CONFIG["api_key"]
        )
        print("LLM inicializado.")

        # 3. Inicializar Cadena QA
        print("Creando la cadena GraphCypherQAChain...")

        
        # --- CORRECCIÓN 2: Convertir el string en un objeto PromptTemplate ---
        # La cadena espera las variables 'schema' y 'question'
        cypher_prompt_object = PromptTemplate(
            template=CYPHER_PROMPT_TEMPLATE,
            input_variables=["schema", "question"]
        )

        # Crea y exporta el objeto listo para usarse
        QA_PROMPT_OBJECT = PromptTemplate(
            template=QA_PROMPT_TEMPLATE,
            input_variables=[ "context", "question"],
        )


        # --- FIN DE LA CORRECCIÓN ---

        qa_chain = GraphCypherQAChain.from_llm(
            llm=llm,
            graph=graph,
            verbose=True,
            return_intermediate_steps=True,
            top_k=20,
            allow_dangerous_requests=True,
            cypher_prompt=cypher_prompt_object,
            qa_prompt=QA_PROMPT_OBJECT,
            )
        print("Cadena QA creada y lista.")
        print("\n--- Servidor listo para recibir peticiones ---")
    except Exception as e:
        print(f"ERROR FATAL DURANTE LA INICIALIZACIÓN: {e}")
        import traceback
        traceback.print_exc() # Imprime el traceback completo del error
        print("La aplicación no pudo iniciarse correctamente.")
    
    # --- Aquí es donde la aplicación se ejecuta ---
    yield
    
    # --- Código de apagado (opcional) ---
    print("Cerrando el servidor...")
    if graph and hasattr(graph, 'driver') and graph.driver:
        graph.driver.close()
        print("Conexión a Neo4j cerrada.")


# --- Inicialización de FastAPI ---

app = FastAPI(
    title="Chatbot de Restaurantes API",
    description="API para interactuar con un LLM y una base de datos Neo4j de restaurantes.",
    lifespan=lifespan  
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_CONFIG["cors_origin"]],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Funciones de Ayuda ---

def create_folium_map(location_data: List[Dict[str, Any]]) -> Optional[str]:
    """
    Crea un mapa de Folium con los datos de ubicación proporcionados
    y devuelve el HTML del mapa.
    'location_data' es la lista de resultados de la BD.
    """
    # Importar folium aquí para que no sea una dependencia dura al iniciar
    try:
        import folium
    except ImportError:
        print("ERROR: Folium no está instalado. No se pueden generar mapas.")
        return None

    if not location_data:
        print("create_folium_map recibió datos vacíos.")
        return None

    # Filtrar datos sin coordenadas válidas
    valid_locations = [
        loc for loc in location_data
        if loc.get("latitude") is not None and loc.get("longitude") is not None
    ]

    if not valid_locations:
        print("No se encontraron coordenadas válidas en los resultados.")
        return None

    # Calcular el punto central del mapa
    avg_lat = sum(loc["latitude"] for loc in valid_locations) / len(valid_locations)
    avg_lon = sum(loc["longitude"] for loc in valid_locations) / len(valid_locations)

    # Crear mapa
    m = folium.Map(
        location=[avg_lat, avg_lon],
        zoom_start=FOLIUM_CONFIG["zoom_start"],
        tiles=FOLIUM_CONFIG["tiles"],
        width="100%",
        height=FOLIUM_CONFIG.get("map_height_px", 400) 
        
    )

    # --- LÓGICA DE POPUP MEJORADA ---
    for loc in valid_locations:
        popup_title = loc.get('name', loc.get('title', 'Restaurante'))
        
        # Construir el HTML del popup
        html = f"<div style='font-family: sans-serif; min-width: 150px; max-width: 250px;'>"
        html += f"<strong>{popup_title}</strong>"
        
        # --- Lógica de Calificación (Estrellas) ---
        rating = loc.get('rating')
        if rating:
            try:
                # Convertir rating (ej. 4.3) en estrellas
                rating_val = float(rating)
                stars = "★" * int(rating_val) + "☆" * (5 - int(rating_val))
                
                total_str = ""
                total_ratings = loc.get('total_ratings')
                if total_ratings:
                    total_str = f" ({total_ratings} calif.)"
                
                html += f"<br>{stars} {rating_val} {total_str}"
            except (ValueError, TypeError):
                pass # Ignorar si el rating no es un número

        # --- Lógica de Reseña ---
        review = loc.get('review')
        if review:
            html += f"<hr style='margin: 5px 0; border-top: 1px solid #eee;'>"
            html += f"<i style='color: #555;'>&quot;{review}&quot;</i>"        
        html += "</div>"
        
        # Crear objeto Popup de Folium
        popup = folium.Popup(html)

        # Añadir marcador
        folium.Marker(
            [loc["latitude"], loc["longitude"]],
            popup=popup, # Usar el objeto popup
            tooltip=popup_title,
            icon=folium.Icon(
                color=FOLIUM_CONFIG["marker_color_restaurant"],
                icon=FOLIUM_CONFIG["marker_icon_restaurant"]
            )
        ).add_to(m)

    # Devolver el HTML del mapa
    return m._repr_html_()


# --- Endpoint Principal de Chat ---

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    """
    Endpoint principal para recibir preguntas y devolver respuestas.
    """
    if not qa_chain:
        raise HTTPException(status_code=503, detail="El servidor no se inicializó correctamente (qa_chain es Nulo). Revisa los logs.")

    print(f"\nRecibida nueva petición: '{request.query}'")

    try:
        # 1. Ejecutar la cadena QA
        result =  qa_chain.invoke({"query": request.query})

        # 2. Inicializar y extraer resultados
        answer = result.get("result", "Lo siento, no pude encontrar una respuesta.")

        intermediate_steps = result.get("intermediate_steps", [])
        
        cypher_query = "No se generó query."
        db_results = []
        map_html = None

        if intermediate_steps:
            print(f"Intermediate Steps: {intermediate_steps}")  
            # Capturamos la query y el contexto (resultados de la BD)
            cypher_query = intermediate_steps[0].get("query", "No se capturó la query.")
            db_results = intermediate_steps[1].get("context", [])

        print(f"Respuesta generada: {answer}")
        print(f"Query Cypher: {cypher_query}")
        print(f"Resultados BD: {db_results}") 

        # 3. Generar mapa de Folium
        if db_results:
            location_data = [item for item in db_results if isinstance(item, dict)]
            
            if location_data:
                map_html = create_folium_map(location_data)
                if map_html:
                    print("Mapa de Folium generado.")
                else:
                    print("Se encontraron resultados de BD, pero no tenían coordenadas válidas.")
            else:
                 print("Los resultados de la BD no eran diccionarios válidos.")

        # 4. Devolver la respuesta completa
        return ChatResponse(
            answer=answer,
            cypher_query=cypher_query,
            map_html=map_html
        )

    except Exception as e:
        print(f"Error durante la ejecución del chat: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ocurrió un error interno: {e}")

# --- Ejecución del Servidor ---

if __name__ == "__main__":
    print("Iniciando servidor Uvicorn en http://localhost:8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)