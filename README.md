# Graph-Rag-with-Folium

# Chat de Restaurantes (Neo4j + LangChain + Folium)

Interfaz tipo chat para consultar un grafo de **restaurantes** en Neo4j y visualizar resultados en un **mapa Folium** embebido. Pensado para consultas en español (GraphCypher + QA) y un flujo sencillo: *Frontend HTML → Backend Python → Neo4j → Folium*.



## 🚀 Características
- Chat UI ligero en HTML/Tailwind.
- Backend en Python (FastAPI/Uvicorn sugeridos) con **LangChain** y **Neo4j** (GraphCypherQAChain).
- Render de mapa con **Folium** cuando la respuesta incluye ubicaciones.
- Notebooks para cargar datos y probar mapas.
- Docker Compose para levantar **Neo4j 5** con **APOC** listo para usar.


## 🧭 Estructura de carpetas
```text

├── DB/
│   └── compose.yml              # Docker Compose para Neo4j
├── notebooks/
│   ├── DB.ipynb                 # Carga/transformación de datos al grafo
│   └── folium.ipynb             # Pruebas de mapas
├── UI/
│   ├── config.py                # Configuración (Neo4j, LLM, Folium, CORS, etc.)
│   ├── frontend.html            # Interfaz del chat
│   └── main.py                  # Backend (endpoint /chat)
├── requirements.txt
└── README.md
