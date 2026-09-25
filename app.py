# ==============================================================================
# APLICACIÓN: ASISTENTE Y DASHBOARD DE ANALÍTICA FINANCIERA
# ==============================================================================
import os
import streamlit as st
import pandas as pd

from utils.conn_Gsheet import conexion_gsheet_produccion, abrir_hoja, cargar_datos
from utils.add_informacion import ingresar_gasto, eliminar_gasto, editar_gasto
from utils.func_dash import (
    aplicar_filtros,
    mostrar_metricas_clave,
    mostrar_kpis_regla_50_30_20,
    graficar_distribucion_categoria,
    graficar_evolucion_temporal,
    graficar_comparativa_persona,
    graficar_detalle_subcategoria,
    mostrar_tabla_detallada
)
from utils.func_ai import (
    inicializar_cliente_ia,
    sugerir_categoria_ia,
    generar_resumen_ia,
    generar_insights_proactivos,
    responder_pregunta_financiera
)

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y CONSTANTES
# ==============================================================================
st.set_page_config(
    page_title="Analítica Financiera & Asistente Inteligente",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

CATEGORIAS = [
    "Comida", "Hogar", "Transporte", "Ocio", "Salud",
    "Ropa y Calzado", "Tecnología", "Regalos", "Educación", "Deuda", "Ahorro/Inversión", "Otro"
]
TIPOS_GASTO = ["Fijo Mensual", "Variable Diario", "Ocasional", "Ahorro/Inversión", "Deuda"]
RUTA_DEMO = os.path.join(os.path.dirname(__file__), "data", "demo_finanzas.csv")

# ==============================================================================
# 2. INICIALIZACIÓN DE CONEXIONES Y MODO DE DATOS
# ==============================================================================
ia_model = inicializar_cliente_ia()

# Barra lateral: Selector de modo de datos
st.sidebar.title("⚙️ Configuración")
modo_fuente = st.sidebar.radio(
    "Fuente de Datos:",
    ["📊 Modo Demostración (Portafolio)", "🔒 Modo Producción (Google Sheets)"],
    index=0,
    help="El modo Demostración permite evaluar el dashboard y las analíticas de inmediato con un dataset sintético representativo."
)

es_modo_demo = "Demostración" in modo_fuente
worksheet = None
df_original = pd.DataFrame()

if es_modo_demo:
    st.sidebar.success("✅ Datos de Demostración Activos")
    if "df_demo" not in st.session_state:
        if os.path.exists(RUTA_DEMO):
            df_init = pd.read_csv(RUTA_DEMO)
            df_init['Fecha'] = pd.to_datetime(df_init['Fecha'], errors='coerce')
            df_init['Monto'] = pd.to_numeric(df_init['Monto'], errors='coerce').fillna(0.0)
            st.session_state.df_demo = df_init
        else:
            st.error("No se encontró el archivo de demostración en `data/demo_finanzas.csv`.")
            st.stop()
    df_original = st.session_state.df_demo.copy()
else:
    # Modo Producción Google Sheets
    client_gsheet = conexion_gsheet_produccion()
    if client_gsheet is None:
        st.warning(
            "⚠️ No se encontraron credenciales de Google Sheets en `.streamlit/secrets.toml`. "
            "Para explorar el portafolio, utiliza el **Modo Demostración**."
        )
        if st.sidebar.button("👉 Cambiar a Modo Demostración"):
            st.rerun()
        st.stop()
    else:
        worksheet = abrir_hoja(client_gsheet)
        if worksheet is None:
            st.error("No se pudo acceder a la hoja de cálculo. Verifique el nombre y permisos.")
            st.stop()
        df_original = cargar_datos(worksheet)

if df_original.empty:
    st.info("Aún no hay transacciones para analizar. ¡Agrega el primer gasto para iniciar!")
    st.stop()

# Obtener dinámicamente integrantes para evitar PII hardcodeada
personas_en_datos = [p for p in df_original['Persona'].dropna().unique() if str(p).strip()]
PERSONAS = personas_en_datos if personas_en_datos else ["Persona A", "Persona B"]

# ==============================================================================
# 3. CABECERA Y FORMULARIO DE INGRESO
# ==============================================================================
st.title("Plataforma de Analítica Financiera & Asistente Inteligente 📊")
st.markdown(
    "Control de gastos, analítica de presupuesto, diagnóstico con la **Regla 50/30/20** "
    "y asistente conversacional con **Google Gemini**."
)

with st.expander("➕ Registrar o Simular Nuevo Movimiento", expanded=False):
    with st.form("entry_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            fecha_gasto = st.date_input("Fecha")
            descripcion_gasto = st.text_input("Descripción *", placeholder="Ej: Compra mensual de supermercado")
        with col2:
            monto_gasto = st.number_input("Monto *", min_value=0.01, format="%.2f")
            persona_gasto = st.selectbox("Efectuado por", PERSONAS)

        # Asistencia con IA para categorizar
        col_btn_ia, _ = st.columns([1, 2])
        with col_btn_ia:
            if st.form_submit_button("🤖 Sugerir Categoría"):
                if descripcion_gasto and ia_model:
                    with st.spinner("Clasificando con IA..."):
                        sugerencia = sugerir_categoria_ia(descripcion_gasto, CATEGORIAS, ia_model)
                        if sugerencia:
                            st.session_state.sugerencia_categoria = sugerencia
                elif not ia_model:
                    st.info("Sugerencia IA no disponible sin Gemini API Key.")
                else:
                    st.warning("Escribe una descripción primero.")

        indice_sugerido = 0
        sug_guardada = st.session_state.get('sugerencia_categoria')
        if sug_guardada and sug_guardada in CATEGORIAS:
            indice_sugerido = CATEGORIAS.index(sug_guardada)

        col3, col4 = st.columns(2)
        with col3:
            categoria_gasto = st.selectbox("Categoría", CATEGORIAS, index=indice_sugerido)
            subcategoria_gasto = st.text_input("Subcategoría (Opcional)", placeholder="Ej: Alimentos, Gasolina, Netflix")
        with col4:
            tipo_gasto_seleccionado = st.selectbox("Tipo de Gasto", TIPOS_GASTO)
            notas_gasto = st.text_input("Notas (Opcional)", placeholder="Observaciones extras")

        submitted_add = st.form_submit_button("✅ Guardar Movimiento", type="primary")

if submitted_add:
    if es_modo_demo:
        # En modo demo guardamos en memoria de sesión para interactividad
        id_nuevo = f"DEMO-{pd.to_datetime(fecha_gasto).strftime('%Y%m%d')}-{len(st.session_state.df_demo):04d}"
        nuevo_registro = {
            "ID_Gasto": id_nuevo,
            "Fecha": pd.to_datetime(fecha_gasto),
            "Monto": float(monto_gasto),
            "Descripcion": str(descripcion_gasto).strip(),
            "Persona": str(persona_gasto),
            "Categoria": str(categoria_gasto),
            "Subcategoria": str(subcategoria_gasto or "").strip(),
            "Tipo de Gasto": str(tipo_gasto_seleccionado),
            "Notas": str(notas_gasto or "").strip()
        }
        st.session_state.df_demo = pd.concat([pd.DataFrame([nuevo_registro]), st.session_state.df_demo], ignore_index=True)
        st.success("¡Movimiento registrado con éxito en la sesión de demostración!")
        if 'sugerencia_categoria' in st.session_state:
            del st.session_state.sugerencia_categoria
        st.rerun()
    else:
        exito, mensaje = ingresar_gasto(
            worksheet, fecha_gasto, monto_gasto, descripcion_gasto, persona_gasto,
            categoria_gasto, subcategoria_gasto, tipo_gasto_seleccionado, notas_gasto
        )
        if exito:
            st.success(mensaje)
            if 'sugerencia_categoria' in st.session_state:
                del st.session_state.sugerencia_categoria
            st.rerun()
        else:
            st.error(mensaje)

# ==============================================================================
# 4. FILTROS EN BARRA LATERAL
# ==============================================================================
st.sidebar.markdown("---")
st.sidebar.header("🔍 Filtros del Dashboard")
persona_sel = st.sidebar.selectbox("Filtrar por Integrante:", ["Ambos"] + list(df_original['Persona'].unique()))

fecha_min_val = df_original['Fecha'].min().date()
fecha_max_val = df_original['Fecha'].max().date()
fecha_sel = st.sidebar.date_input(
    "Rango de Fechas:",
    value=(fecha_min_val, fecha_max_val),
    min_value=fecha_min_val,
    max_value=fecha_max_val
)

categoria_sel = st.sidebar.multiselect(
    "Filtrar por Categoría:",
    options=["Todas"] + list(df_original['Categoria'].unique()),
    default="Todas"
)

df_filtrado = aplicar_filtros(df_original, persona_sel, fecha_sel, categoria_sel)

if df_filtrado.empty:
    st.warning("No se encontraron registros para los filtros seleccionados.")
    st.stop()

# ==============================================================================
# 5. KPIS EJECUTIVOS Y PATRONES ANALÍTICOS
# ==============================================================================
st.markdown("---")
mostrar_metricas_clave(df_filtrado, df_referencia=df_original)

# Sección de Insights Cuantitativos
st.markdown("#### 💡 Insights y Patrones Detectados")
with st.spinner("Analizando dispersión y hábitos de gasto..."):
    insights = generar_insights_proactivos(df_filtrado, ia_model)

if insights:
    cols_ins = st.columns(len(insights))
    for i, ins in enumerate(insights):
        with cols_ins[i]:
            st.info(ins, icon="📌")

# Diagnóstico de Presupuesto 50/30/20
mostrar_kpis_regla_50_30_20(df_filtrado)

# ==============================================================================
# 6. VISUALIZACIONES PRINCIPALES
# ==============================================================================
st.markdown("---")
c_vis1, c_vis2 = st.columns([1, 1.2])
with c_vis1:
    graficar_distribucion_categoria(df_filtrado)
with c_vis2:
    graficar_evolucion_temporal(df_filtrado)

# ==============================================================================
# 7. MÓDULOS DETALLADOS Y EXPLORATORIOS (TABS)
# ==============================================================================
st.markdown("---")
tabs = st.tabs([
    "👥 Comparativa",
    "🌳 Subcategorías",
    "📄 Datos y Exportación",
    "⚙️ Gestión CRUD",
    "🧠 Diagnóstico Financiero",
    "💬 Chat Analítico"
])

with tabs[0]:
    graficar_comparativa_persona(df_filtrado)

with tabs[1]:
    graficar_detalle_subcategoria(df_filtrado)

with tabs[2]:
    mostrar_tabla_detallada(df_filtrado)

with tabs[3]:
    st.subheader("Gestión de Movimientos Registrados")
    st.caption("Permite auditar, editar o depurar transacciones del período seleccionado.")
    gastos_gestionar = df_filtrado.sort_values(by="Fecha", ascending=False).head(15)

    for _, row in gastos_gestionar.iterrows():
        id_g = str(row['ID_Gasto'])
        desc_val = str(row['Descripcion'])
        monto_val = float(row['Monto'])
        fecha_val = row['Fecha'].strftime('%d/%m/%Y')

        with st.expander(f"📝 {desc_val} | S/ {monto_val:,.2f} | 📅 {fecha_val}"):
            with st.form(key=f"edit_form_{id_g}"):
                st.write(f"**Identificador:** `{id_g}`")
                fc1, fc2 = st.columns(2)
                with fc1:
                    n_fecha = st.date_input("Fecha", value=row['Fecha'].date(), key=f"f_{id_g}")
                    n_monto = st.number_input("Monto", value=monto_val, format="%.2f", key=f"m_{id_g}")
                    cat_idx = CATEGORIAS.index(row['Categoria']) if row['Categoria'] in CATEGORIAS else 0
                    n_cat = st.selectbox("Categoría", CATEGORIAS, index=cat_idx, key=f"c_{id_g}")
                with fc2:
                    n_desc = st.text_input("Descripción", value=desc_val, key=f"d_{id_g}")
                    n_sub = st.text_input("Subcategoría", value=str(row.get('Subcategoria', '')), key=f"s_{id_g}")
                    pers_idx = PERSONAS.index(row['Persona']) if row['Persona'] in PERSONAS else 0
                    n_pers = st.selectbox("Integrante", PERSONAS, index=pers_idx, key=f"p_{id_g}")

                b_edit, b_del = st.columns(2)
                with b_edit:
                    sub_edit = st.form_submit_button("💾 Guardar Cambios")
                with b_del:
                    sub_del = st.form_submit_button("🗑️ Eliminar Movimiento")

            if sub_edit:
                if es_modo_demo:
                    idx = st.session_state.df_demo[st.session_state.df_demo['ID_Gasto'] == id_g].index
                    if not idx.empty:
                        st.session_state.df_demo.loc[idx[0], 'Fecha'] = pd.to_datetime(n_fecha)
                        st.session_state.df_demo.loc[idx[0], 'Monto'] = float(n_monto)
                        st.session_state.df_demo.loc[idx[0], 'Descripcion'] = n_desc
                        st.session_state.df_demo.loc[idx[0], 'Categoria'] = n_cat
                        st.session_state.df_demo.loc[idx[0], 'Subcategoria'] = n_sub
                        st.session_state.df_demo.loc[idx[0], 'Persona'] = n_pers
                        st.success("Gasto actualizado en la sesión de demostración.")
                        st.rerun()
                else:
                    datos_act = {
                        'Fecha': n_fecha.strftime('%Y-%m-%d'), 'Monto': n_monto, 'Descripcion': n_desc,
                        'Categoria': n_cat, 'Subcategoria': n_sub, 'Persona': n_pers
                    }
                    exito, msg = editar_gasto(worksheet, id_g, datos_act)
                    if exito: st.success(msg); st.rerun()
                    else: st.error(msg)

            if sub_del:
                if es_modo_demo:
                    st.session_state.df_demo = st.session_state.df_demo[st.session_state.df_demo['ID_Gasto'] != id_g]
                    st.success("Gasto eliminado de la sesión de demostración.")
                    st.rerun()
                else:
                    exito, msg = eliminar_gasto(worksheet, id_g)
                    if exito: st.success(msg); st.rerun()
                    else: st.error(msg)

with tabs[4]:
    st.subheader("🧠 Diagnóstico Financiero Integral")
    st.caption("Genera una evaluación estratégica de los hábitos de consumo y recomendaciones de ahorro.")
    if st.button("🚀 Generar Diagnóstico Financiero", type="primary"):
        with st.spinner("Procesando análisis multidimensional..."):
            informe = generar_resumen_ia(df_filtrado, ia_model)
            with st.container(border=True):
                st.markdown(informe)

with tabs[5]:
    st.subheader("💬 Asistente Analítico Conversacional")
    st.caption("Formula preguntas sobre tus finanzas en lenguaje natural (ej. '¿Cuál fue el mayor gasto en Comida?').")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Escribe una consulta sobre tus gastos..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analizando datos..."):
                resp = responder_pregunta_financiera(prompt, df_filtrado, ia_model)
                st.markdown(resp)

        st.session_state.messages.append({"role": "assistant", "content": resp})