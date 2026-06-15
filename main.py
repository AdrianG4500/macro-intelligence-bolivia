import streamlit as st
import polars as pl
from openai import OpenAI
import os
import json
from dotenv import load_dotenv

# Cargar configuración y API Key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID", "vs_6a2f5cca5f808191ae9bf9ab632c0e9e")

# Leer parámetros para modo embebido/chat-only
chat_only = st.query_params.get("chat_only") == "true"

# 1. Configuración de página
st.set_page_config(
    page_title="Agente Macroeconomía Abierta",
    page_icon="🌍",
    layout="wide"
)

# 2. Inyección de Diseño Premium (CSS)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    font-family: 'Outfit', sans-serif;
}

/* Tarjeta Métrica Estilo Premium */
.metric-card {
    background: linear-gradient(135deg, #1e293b, #0f172a);
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 22px;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -4px rgba(0, 0, 0, 0.3);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.metric-card:hover {
    transform: translateY(-4px);
    border-color: #3b82f6;
    box-shadow: 0 20px 25px -5px rgba(59, 130, 246, 0.2), 0 8px 10px -6px rgba(59, 130, 246, 0.2);
}

/* Tarjeta de Noticias Estilo Premium */
.news-card {
    background: linear-gradient(135deg, #111827, #1f2937);
    border: 1px solid #374151;
    border-radius: 14px;
    padding: 18px;
    margin-bottom: 15px;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: all 0.25s ease;
}

.news-card:hover {
    border-color: #10b981;
    transform: scale(1.01);
}
</style>
""", unsafe_allow_html=True)

if not chat_only:
    # Encabezado Principal
    st.title("🌍 Agente de Macroeconomía Abierta")
    st.markdown("### Análisis Inteligente y Monitoreo de la Economía Boliviana")
    st.divider()

    # --- SECCIÓN DE NOTICIAS ---
    st.subheader("🗞️ Radar de Noticias Económicas")

    try:
        with open("data/processed/latest_news.json", "r", encoding="utf-8") as f:
            news_data = json.load(f)
        
        if news_data:
            cols = st.columns(3)
            for i, item in enumerate(news_data[:6]):  # Mostrar hasta 6 noticias
                with cols[i % 3]:
                    st.markdown(f"""
                    <div class="news-card">
                        <div>
                            <span style="font-size: 11px; background-color: #065f46; color: #34d399; padding: 3px 8px; border-radius: 9999px; font-weight: 600; text-transform: uppercase;">Radar</span>
                            <h4 style="color: #f3f4f6; margin-top: 10px; margin-bottom: 8px; font-weight: 600; line-height: 1.3;">{item['titulo']}</h4>
                            <p style="color: #9ca3af; font-size: 13px; margin-bottom: 12px; line-height: 1.4;">{item['resumen']}</p>
                        </div>
                        <a href="{item['link']}" target="_blank" style="color: #34d399; text-decoration: none; font-size: 12px; font-weight: 500; display: inline-flex; align-items: center; gap: 4px;">
                            Leer fuente original →
                        </a>
                    </div>
                    """, unsafe_allow_html=True)
                    st.write("") # Margen vertical
        else:
            st.info("No hay noticias recientes cargadas en el sistema.")
    except FileNotFoundError:
        st.warning("Aún no se ha generado el briefing de noticias de hoy.")

    st.divider()

    # --- SECCIÓN DE VARIABLES ---
    st.subheader("📊 Indicadores Macroeconómicos Clave")

    @st.cache_data
    def load_macro_data():
        return pl.read_csv("data/processed/top_25_macro_bolivia.csv")

    try:
        df_macro = load_macro_data()
        
        # Organizar variables en pestañas por categoría
        categorias = ["Core Doméstico", "Externas Críticas", "Financieras y Riesgo"]
        tabs = st.tabs([f"🔹 {cat}" for cat in categorias] + ["📋 Ver Tabla Completa"])
        
        for cat, tab in zip(categorias, tabs[:3]):
            with tab:
                df_cat = df_macro.filter(pl.col("Categoria") == cat)
                cols = st.columns(3)
                
                for idx, row in enumerate(df_cat.iter_rows(named=True)):
                    with cols[idx % 3]:
                        val = row['Valor_Actual']
                        val_str = f"{val:,.2f}" if val is not None else "N/A"
                        st.markdown(f"""
                        <div class="metric-card" style="margin-bottom: 20px;">
                            <div style="font-size: 11px; color: #94a3b8; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px;">
                                {row['Variable']}
                            </div>
                            <div style="font-size: 28px; font-weight: 700; color: #f8fafc; margin-bottom: 8px;">
                                {val_str} <span style="font-size: 14px; color: #64748b; font-weight: 400;">{row['Unidad']}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; font-size: 11px; color: #64748b; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 8px; margin-top: 8px;">
                                <span>🏛️ {row['Fuente']}</span>
                                <span>📅 {row['Ultima_Actualizacion']}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.write("") # Margen
                        
        with tabs[3]:
            st.dataframe(df_macro.to_pandas(), use_container_width='stretch', hide_index=True)

    except Exception as e:
        st.error(f"Error cargando indicadores macroeconómicos: {e}")

    st.divider()
    # --- SECCIÓN 3: CHATBOT DE INTELIGENCIA ARTIFICIAL ---
    st.subheader("🤖 Consultor IA de Macroeconomía")
else:
    st.markdown("<h3 style='text-align: center; color: #f8fafc; margin-top: 0; padding-top: 10px;'>🤖 Asistente Macroeconómico</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 13px; margin-bottom: 20px;'>Consultas oficiales sobre la economía boliviana</p>", unsafe_allow_html=True)


if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar historial
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Entrada del usuario
if user_input := st.chat_input("Pregunta sobre la economía boliviana o los reportes oficiales..."):
    # Añadir mensaje del usuario al historial
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Respuesta de OpenAI
    with st.chat_message("assistant"):
        status_container = st.status("🔍 Analizando reportes y series de tiempo...", expanded=True)
        
        try:
            response = client.responses.create(
                model="gpt-5-mini",
                input=[
                    {
                        "role": "system",
                        "content": (
                            "# Role: Senior Macroeconomist & Data Analyst (Bolivia Specialist)\n\n"
                            "## Perfil\n"
                            "Eres un economista macroeconómico senior con más de 15 años de experiencia en el análisis de la economía boliviana. Tu especialidad es la Macroeconomía Abierta, con un enfoque profundo en la sostenibilidad externa, la gestión de reservas internacionales y la política fiscal y cambiaria.\n\n"
                            "## Instrucciones de Operación\n"
                            "1. **Rigor Estadístico:** Analiza datos estructurados (series de tiempo, variaciones porcentuales, saldos) con precisión. Identifica tendencias, picos, caídas, estacionalidad y quiebres estructurales.\n"
                            "2. **Uso de Herramientas:**\n"
                            "   - **`file_search`:** Es tu fuente primaria. Debes basar tus respuestas estrictamente en los reportes del BCB y el INE adjuntos en el Vector Store.\n"
                            "   - **`web_search`:** Utilízalo exclusivamente para reforzar información, buscar precios de commodities en tiempo real (Gas, Petróleo, Zinc, Oro) o encontrar comunicados de prensa recientes que no estén en los PDFs.\n"
                            "3. **Marco Teórico:** Vincula los datos con teorías de Macroeconomía Abierta (ej: Condición de Marshall-Lerner, Enfermedad Holandesa, Identidad de Absorción, Sostenibilidad de la Deuda).\n"
                            "4. **Notación Matemática:** Utiliza SIEMPRE LaTeX para fórmulas. Ejemplo: Para explicar la cuenta corriente usa $$CC = S - I + (T - G)$$ o variaciones porcentuales $$\\Delta \\% = \\frac{V_f - V_i}{V_i} \\times 100$$.\n"
                            "5. **Integridad de Datos:** No inventes cifras. Si un dato no está en los archivos ni en la web, indícalo claramente.\n\n"
                            "## Estructura del Informe\n"
                            "Cada respuesta debe seguir este formato profesional:\n"
                            "- **Título:** Técnico y descriptivo.\n"
                            "- **Resumen Ejecutivo:** (Máximo 3 líneas) El hallazgo principal (Bottom Line Up Front).\n"
                            "- **Análisis Detallado:** Desglose del impacto de las variables. Debes conectar al menos dos variables del \"Top 25\" en tu explicación (ej: cómo el precio del Gas afecta las Reservas y el Déficit Fiscal).\n"
                            "- **Contexto de Datos:** Cita explícitamente si el dato proviene de los documentos de la base de conocimientos ({datos_contexto}).\n"
                            "- **Conclusiones e Implicaciones:** Qué significa esto para la estabilidad cambiaria o la solvencia del país.\n\n"
                            "## Estilo y Tono\n"
                            "- Idioma: Español técnico y formal.\n"
                            "- Preciso, analítico y libre de sesgos políticos.\n"
                            "- Formato: Usa negritas para resaltar indicadores clave y listas para mejorar la legibilidad."
                        )
                    },
                    {
                        "role": "user",
                        "content": user_input
                    }
                ],
                tools=[
                    {
                        "type": "file_search",
                        "vector_store_ids": [VECTOR_STORE_ID]
                    },
                    {
                        "type": "web_search",
                        "filters": {
                            "allowed_domains": [
                                "www.bcb.gob.bo",
                                "www.ine.gob.bo",
                                "tradingeconomics.com",
                                "finance.yahoo.com",
                                "www.bbc.com",
                                "eldeber.com.bo",
                                "www.economist.com",
                                "economist.com",
                                "bloomberg.com",
                                "www.bloomberg.com",
                                "reuters.com",
                                "www.reuters.com",
                                "ft.com",
                                "www.ft.com"
                            ]
                        }
                    }
                ]
            )
            
            status_container.update(label="✅ Análisis completado", state="complete", expanded=False)
            answer = response.output_text
            
            # Renderizar la respuesta
            st.markdown(answer)
            
            # Mostrar las fuentes bibliográficas si la IA usó file_search o web_search
            if hasattr(response, 'citations') and response.citations:
                with st.expander("Ver fuentes consultadas"):
                    for cite in response.citations:
                        st.caption(f"📍 {cite}")

            st.session_state.messages.append({"role": "assistant", "content": answer})
                
        except Exception as e:
            status_container.update(label="❌ Error en la consulta", state="error", expanded=False)
            st.error(f"Error técnico: {e}")

# Pie de página pulcro
st.markdown("---")
st.markdown("<p style='text-align: center; color: grey;'>Desarrollado para la materia de Macroeconomía Abierta | 2026</p>", unsafe_allow_html=True)