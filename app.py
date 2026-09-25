# ==============================================================================
# APLICACIÓN: ASISTENTE Y DASHBOARD DE ANALÍTICA FINANCIERA
# ==============================================================================
import os
import streamlit as st
import pandas as pd

from utils.conn_Gsheet import conexion_gsheet_produccion, abrir_hoja, cargar_datos, cargar_ingresos
from utils.add_informacion import ingresar_gasto, eliminar_gasto, editar_gasto, ingresar_ingreso, eliminar_ingreso
from utils.func_dash import (
    aplicar_filtros,
    mostrar_balance_financiero,
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

CATEGORIAS_GASTO = [
    "Comida", "Hogar", "Transporte", "Ocio", "Salud",
    "Ropa y Calzado", "Tecnología", "Regalos", "Educación", "Deuda", "Ahorro/Inversión", "Otro"
]
TIPOS_GASTO = ["Fijo Mensual", "Variable Diario", "Ocasional", "Ahorro/Inversión", "Deuda"]

CATEGORIAS_INGRESO = [
    "Sueldo Fijo", "Quincena", "Bono / Gratificación", "Freelance / Independiente", "Inversión", "Otro"
]

RUTA_DEMO_GASTOS = os.path.join(os.path.dirname(__file__), "data", "demo_finanzas.csv")
RUTA_DEMO_INGRESOS = os.path.join(os.path.dirname(__file__), "data", "demo_ingresos.csv")

# ==============================================================================
# 2. INICIALIZACIÓN DE CONEXIONES Y GESTIÓN DE SEGURIDAD / MODO DE DATOS
# ==============================================================================
ia_model = inicializar_cliente_ia()

st.sidebar.title("⚙️ Configuración")
modo_fuente = st.sidebar.radio(
    "Fuente de Datos:",
    ["📊 Modo Demostración (Portafolio)", "🔒 Modo Producción (Google Sheets)"],
    index=0,
    help="El modo Demostración contiene 1,480 transacciones sintéticas para evaluar el sistema. El modo Producción conecta a tu Google Sheets privado bajo clave de acceso."
)

es_modo_demo = "Demostración" in modo_fuente
worksheet_gastos = None
worksheet_ingresos = None
df_original_gastos = pd.DataFrame()
df_original_ingresos = pd.DataFrame()

if es_modo_demo:
    st.sidebar.success("✅ Modo Demostración Activo")
    # Cargar datos sintéticos de gastos
    if "df_demo_gastos" not in st.session_state:
        if os.path.exists(RUTA_DEMO_GASTOS):
            df_g = pd.read_csv(RUTA_DEMO_GASTOS)
            df_g['Fecha'] = pd.to_datetime(df_g['Fecha'], errors='coerce')
            df_g['Monto'] = pd.to_numeric(df_g['Monto'], errors='coerce').fillna(0.0)
            st.session_state.df_demo_gastos = df_g
        else:
            st.error("No se encontró `data/demo_finanzas.csv`.")
            st.stop()
    df_original_gastos = st.session_state.df_demo_gastos.copy()

    # Cargar datos sintéticos de ingresos
    if "df_demo_ingresos" not in st.session_state:
        if os.path.exists(RUTA_DEMO_INGRESOS):
            df_i = pd.read_csv(RUTA_DEMO_INGRESOS)
            df_i['Fecha'] = pd.to_datetime(df_i['Fecha'], errors='coerce')
            df_i['Monto'] = pd.to_numeric(df_i['Monto'], errors='coerce').fillna(0.0)
            st.session_state.df_demo_ingresos = df_i
        else:
            st.session_state.df_demo_ingresos = pd.DataFrame(columns=['ID_Ingreso', 'Fecha', 'Monto', 'Descripcion', 'Persona', 'Categoria'])
    df_original_ingresos = st.session_state.df_demo_ingresos.copy()

else:
    # --------------------------------------------------------------------------
    # BARRERA DE SEGURIDAD / PIN PARA MODO PRODUCCIÓN
    # --------------------------------------------------------------------------
    if "auth_produccion" not in st.session_state:
        st.session_state.auth_produccion = False

    if not st.session_state.auth_produccion:
        st.title("🔒 Acceso Restringido: Modo Producción")
        st.markdown(
            """
            Este entorno conecta directamente a la base de datos real en **Google Sheets**.
            Por motivos de seguridad y privacidad financiera, el acceso está protegido por clave.
            """
        )

        col_pin, _ = st.columns([1.2, 1])
        with col_pin:
            with st.form("pin_auth_form"):
                st.subheader("🔑 Autenticación de Propietario")
                pin_input = st.text_input("Ingrese su PIN o Clave de Seguridad:", type="password", placeholder="Ingresa tu clave...")
                submit_pin = st.form_submit_button("Desbloquear Modo Producción", type="primary")

            if submit_pin:
                pin_correcto = None
                if hasattr(st, "secrets") and "app_config" in st.secrets:
                    pin_correcto = str(st.secrets["app_config"].get("admin_password", ""))
                if not pin_correcto:
                    pin_correcto = os.environ.get("ADMIN_PASSWORD", "")

                if pin_correcto and pin_input.strip() == pin_correcto.strip():
                    st.session_state.auth_produccion = True
                    st.success("¡Acceso concedido exitosamente!")
                    st.rerun()
                elif not pin_correcto:
                    st.warning("⚠️ No se ha definido 'admin_password' en `.streamlit/secrets.toml` bajo la sección `[app_config]`.")
                else:
                    st.error("❌ Clave o PIN incorrecto. Si eres visitante o reclutador, utiliza el **Modo Demostración**.")

            st.markdown("---")
            if st.button("👈 Volver al Modo Demostración"):
                st.rerun()

        st.stop()

    # Si ya está autenticado en producción:
    st.sidebar.success("🔓 Sesión de Producción Activa")
    if st.sidebar.button("🔒 Cerrar Sesión Privada"):
        st.session_state.auth_produccion = False
        st.rerun()

    client_gsheet = conexion_gsheet_produccion()
    if client_gsheet is None:
        st.warning(
            "⚠️ No se encontraron credenciales válidas en `.streamlit/secrets.toml` para conectar a Google Sheets."
        )
        st.stop()

    worksheet_gastos = abrir_hoja(client_gsheet, worksheet_name="Hoja 1")
    worksheet_ingresos = abrir_hoja(client_gsheet, worksheet_name="Ingresos")

    if worksheet_gastos is None:
        st.error("No se pudo acceder a la hoja de gastos ('Hoja 1'). Verifique permisos.")
        st.stop()

    df_original_gastos = cargar_datos(worksheet_gastos)
    df_original_ingresos = cargar_ingresos(worksheet_ingresos) if worksheet_ingresos is not None else pd.DataFrame(columns=['ID_Ingreso', 'Fecha', 'Monto', 'Descripcion', 'Persona', 'Categoria'])

if df_original_gastos.empty and df_original_ingresos.empty:
    st.info("Aún no hay transacciones para analizar. ¡Agrega el primer movimiento para iniciar!")
    st.stop()

# Detección dinámica de integrantes
personas_detectadas = set()
if 'Persona' in df_original_gastos.columns:
    personas_detectadas.update(df_original_gastos['Persona'].dropna().unique())
if 'Persona' in df_original_ingresos.columns:
    personas_detectadas.update(df_original_ingresos['Persona'].dropna().unique())

PERSONAS = list(personas_detectadas) if personas_detectadas else ["Persona A", "Persona B"]

# ==============================================================================
# 3. CABECERA Y REGISTRO DE MOVIMIENTOS (GASTOS E INGRESOS)
# ==============================================================================
st.title("Plataforma de Analítica Financiera & Flujo de Caja 📊")
st.markdown(
    "Control integral de **Ingresos vs. Gastos**, diagnóstico de salud financiera (**Regla 50/30/20**), "
    "análisis de tendencias y asistente conversacional con **Google Gemini AI**."
)

with st.expander("➕ Registrar o Simular Movimiento (Gasto / Ingreso)", expanded=False):
    tipo_movimiento = st.radio("Tipo de Movimiento a Registrar:", ["💸 Registrar Gasto", "💰 Registrar Ingreso"], horizontal=True)

    if tipo_movimiento == "💸 Registrar Gasto":
        with st.form("form_gasto", clear_on_submit=False):
            col1, col2 = st.columns(2)
            with col1:
                fecha_gasto = st.date_input("Fecha del Gasto")
                descripcion_gasto = st.text_input("Descripción *", placeholder="Ej: Compra semanal de supermercado")
            with col2:
                monto_gasto = st.number_input("Monto * (S/)", min_value=0.01, format="%.2f")
                persona_gasto = st.selectbox("Efectuado por", PERSONAS)

            col_btn_ia, _ = st.columns([1, 2])
            with col_btn_ia:
                if st.form_submit_button("🤖 Sugerir Categoría"):
                    if descripcion_gasto and ia_model:
                        with st.spinner("Clasificando con IA..."):
                            sugerencia = sugerir_categoria_ia(descripcion_gasto, CATEGORIAS_GASTO, ia_model)
                            if sugerencia:
                                st.session_state.sugerencia_categoria = sugerencia
                    elif not ia_model:
                        st.info("Sugerencia IA no disponible sin Gemini API Key.")
                    else:
                        st.warning("Escribe una descripción primero.")

            indice_sugerido = 0
            sug_guardada = st.session_state.get('sugerencia_categoria')
            if sug_guardada and sug_guardada in CATEGORIAS_GASTO:
                indice_sugerido = CATEGORIAS_GASTO.index(sug_guardada)

            col3, col4 = st.columns(2)
            with col3:
                categoria_gasto = st.selectbox("Categoría", CATEGORIAS_GASTO, index=indice_sugerido)
                subcategoria_gasto = st.text_input("Subcategoría (Opcional)", placeholder="Ej: Alimentos, Combustible, Netflix")
            with col4:
                tipo_gasto_seleccionado = st.selectbox("Tipo de Gasto", TIPOS_GASTO)
                notas_gasto = st.text_input("Notas (Opcional)", placeholder="Observaciones extras")

            submitted_gasto = st.form_submit_button("✅ Guardar Gasto", type="primary")

        if submitted_gasto:
            if es_modo_demo:
                id_nuevo = f"DEMO-G-{pd.to_datetime(fecha_gasto).strftime('%Y%m%d')}-{len(st.session_state.df_demo_gastos):04d}"
                nuevo_reg = {
                    "ID_Gasto": id_nuevo, "Fecha": pd.to_datetime(fecha_gasto), "Monto": float(monto_gasto),
                    "Descripcion": str(descripcion_gasto).strip(), "Persona": str(persona_gasto),
                    "Categoria": str(categoria_gasto), "Subcategoria": str(subcategoria_gasto or "").strip(),
                    "Tipo de Gasto": str(tipo_gasto_seleccionado), "Notas": str(notas_gasto or "").strip()
                }
                st.session_state.df_demo_gastos = pd.concat([pd.DataFrame([nuevo_reg]), st.session_state.df_demo_gastos], ignore_index=True)
                st.success("¡Gasto registrado en la sesión de demostración!")
                if 'sugerencia_categoria' in st.session_state: del st.session_state.sugerencia_categoria
                st.rerun()
            else:
                exito, msg = ingresar_gasto(worksheet_gastos, fecha_gasto, monto_gasto, descripcion_gasto, persona_gasto,
                                            categoria_gasto, subcategoria_gasto, tipo_gasto_seleccionado, notas_gasto)
                if exito:
                    st.success(msg)
                    if 'sugerencia_categoria' in st.session_state: del st.session_state.sugerencia_categoria
                    st.rerun()
                else:
                    st.error(msg)

    else:
        # Formulario de Registro de Ingreso
        with st.form("form_ingreso", clear_on_submit=False):
            col1, col2 = st.columns(2)
            with col1:
                fecha_ingreso = st.date_input("Fecha del Ingreso")
                descripcion_ingreso = st.text_input("Descripción *", placeholder="Ej: Sueldo mensual, Adelanto quincena, Bono")
            with col2:
                monto_ingreso = st.number_input("Monto * (S/)", min_value=0.01, format="%.2f")
                persona_ingreso = st.selectbox("Percibido por", PERSONAS)

            col3, col4 = st.columns(2)
            with col3:
                categoria_ingreso = st.selectbox("Categoría de Ingreso", CATEGORIAS_INGRESO)
            with col4:
                st.caption("Los ingresos alimentan el cálculo del Flujo de Caja y la Tasa de Ahorro.")

            submitted_ingreso = st.form_submit_button("✅ Guardar Ingreso", type="primary")

        if submitted_ingreso:
            if es_modo_demo:
                id_nuevo_ing = f"DEMO-I-{pd.to_datetime(fecha_ingreso).strftime('%Y%m%d')}-{len(st.session_state.df_demo_ingresos):04d}"
                nuevo_reg_ing = {
                    "ID_Ingreso": id_nuevo_ing, "Fecha": pd.to_datetime(fecha_ingreso), "Monto": float(monto_ingreso),
                    "Descripcion": str(descripcion_ingreso).strip(), "Persona": str(persona_ingreso),
                    "Categoria": str(categoria_ingreso)
                }
                st.session_state.df_demo_ingresos = pd.concat([pd.DataFrame([nuevo_reg_ing]), st.session_state.df_demo_ingresos], ignore_index=True)
                st.success("¡Ingreso registrado en la sesión de demostración!")
                st.rerun()
            else:
                if worksheet_ingresos is None:
                    st.error("No se encontró la pestaña 'Ingresos' en tu Google Sheets. Asegúrate de haberla creado con las columnas indicadas.")
                else:
                    exito, msg = ingresar_ingreso(worksheet_ingresos, fecha_ingreso, monto_ingreso, descripcion_ingreso, persona_ingreso, categoria_ingreso)
                    if exito:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

# ==============================================================================
# 4. FILTROS EN BARRA LATERAL
# ==============================================================================
st.sidebar.markdown("---")
st.sidebar.header("🔍 Filtros del Dashboard")
persona_sel = st.sidebar.selectbox("Filtrar por Integrante:", ["Ambos"] + PERSONAS)

# Determinar rango temporal
fechas_disponibles = []
if not df_original_gastos.empty and 'Fecha' in df_original_gastos.columns:
    fechas_disponibles.extend([df_original_gastos['Fecha'].min(), df_original_gastos['Fecha'].max()])
if not df_original_ingresos.empty and 'Fecha' in df_original_ingresos.columns:
    fechas_disponibles.extend([df_original_ingresos['Fecha'].min(), df_original_ingresos['Fecha'].max()])

if fechas_disponibles:
    f_min = min(fechas_disponibles).date()
    f_max = max(fechas_disponibles).date()
else:
    f_min = pd.to_datetime("2025-01-01").date()
    f_max = pd.to_datetime("2026-12-31").date()

fecha_sel = st.sidebar.date_input("Rango de Fechas:", value=(f_min, f_max), min_value=f_min, max_value=f_max)

cat_opciones = ["Todas"] + list(df_original_gastos['Categoria'].dropna().unique()) if not df_original_gastos.empty else ["Todas"]
categoria_sel = st.sidebar.multiselect("Filtrar por Categoría de Gasto:", options=cat_opciones, default="Todas")

# Aplicar filtros
df_gastos_filtrado = aplicar_filtros(df_original_gastos, persona_sel, fecha_sel, categoria_sel)
df_ingresos_filtrado = aplicar_filtros(df_original_ingresos, persona_sel, fecha_sel, ["Todas"])

# ==============================================================================
# 5. BALANCE GENERAL & KPIS (SEMÁFORO FINANCIERO ROJO / VERDE)
# ==============================================================================
st.markdown("---")
mostrar_balance_financiero(df_gastos_filtrado, df_ingresos_filtrado)

st.markdown("---")
mostrar_metricas_clave(df_gastos_filtrado, df_referencia=df_original_gastos)

# Sección de Insights
st.markdown("#### 💡 Insights y Patrones Detectados")
with st.spinner("Analizando hábitos de consumo y dispersión..."):
    insights = generar_insights_proactivos(df_gastos_filtrado, ia_model)

if insights:
    cols_ins = st.columns(len(insights))
    for i, ins in enumerate(insights):
        with cols_ins[i]:
            st.info(ins, icon="📌")

# Regla 50/30/20
mostrar_kpis_regla_50_30_20(df_gastos_filtrado)

# ==============================================================================
# 6. VISUALIZACIONES PRINCIPALES
# ==============================================================================
st.markdown("---")
c_vis1, c_vis2 = st.columns([1, 1.2])
with c_vis1:
    graficar_distribucion_categoria(df_gastos_filtrado)
with c_vis2:
    graficar_evolucion_temporal(df_gastos_filtrado)

# ==============================================================================
# 7. MÓDULOS DETALLADOS (TABS)
# ==============================================================================
st.markdown("---")
tabs = st.tabs([
    "👥 Comparativa",
    "🌳 Subcategorías",
    "📄 Registros y Descarga",
    "⚙️ Gestión CRUD",
    "🧠 Diagnóstico Financiero",
    "💬 Chat Analítico"
])

with tabs[0]:
    graficar_comparativa_persona(df_gastos_filtrado)

with tabs[1]:
    graficar_detalle_subcategoria(df_gastos_filtrado)

with tabs[2]:
    st.subheader("Registros Detallados")
    tab_sub1, tab_sub2 = st.tabs(["💸 Gastos Registrados", "💰 Ingresos Registrados"])
    with tab_sub1:
        mostrar_tabla_detallada(df_gastos_filtrado, nombre_archivo="gastos_filtrados.csv")
    with tab_sub2:
        mostrar_tabla_detallada(df_ingresos_filtrado, nombre_archivo="ingresos_filtrados.csv")

with tabs[3]:
    st.subheader("Gestión de Movimientos Registrados")
    st.caption("Permite auditar, editar o depurar transacciones del período seleccionado.")
    gastos_gestionar = df_gastos_filtrado.sort_values(by="Fecha", ascending=False).head(15) if not df_gastos_filtrado.empty else pd.DataFrame()

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
                    cat_idx = CATEGORIAS_GASTO.index(row['Categoria']) if row['Categoria'] in CATEGORIAS_GASTO else 0
                    n_cat = st.selectbox("Categoría", CATEGORIAS_GASTO, index=cat_idx, key=f"c_{id_g}")
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
                    idx = st.session_state.df_demo_gastos[st.session_state.df_demo_gastos['ID_Gasto'] == id_g].index
                    if not idx.empty:
                        st.session_state.df_demo_gastos.loc[idx[0], 'Fecha'] = pd.to_datetime(n_fecha)
                        st.session_state.df_demo_gastos.loc[idx[0], 'Monto'] = float(n_monto)
                        st.session_state.df_demo_gastos.loc[idx[0], 'Descripcion'] = n_desc
                        st.session_state.df_demo_gastos.loc[idx[0], 'Categoria'] = n_cat
                        st.session_state.df_demo_gastos.loc[idx[0], 'Subcategoria'] = n_sub
                        st.session_state.df_demo_gastos.loc[idx[0], 'Persona'] = n_pers
                        st.success("Gasto actualizado en la sesión de demostración.")
                        st.rerun()
                else:
                    datos_act = {
                        'Fecha': n_fecha.strftime('%Y-%m-%d'), 'Monto': n_monto, 'Descripcion': n_desc,
                        'Categoria': n_cat, 'Subcategoria': n_sub, 'Persona': n_pers
                    }
                    exito, msg = editar_gasto(worksheet_gastos, id_g, datos_act)
                    if exito: st.success(msg); st.rerun()
                    else: st.error(msg)

            if sub_del:
                if es_modo_demo:
                    st.session_state.df_demo_gastos = st.session_state.df_demo_gastos[st.session_state.df_demo_gastos['ID_Gasto'] != id_g]
                    st.success("Gasto eliminado de la sesión de demostración.")
                    st.rerun()
                else:
                    exito, msg = eliminar_gasto(worksheet_gastos, id_g)
                    if exito: st.success(msg); st.rerun()
                    else: st.error(msg)

with tabs[4]:
    st.subheader("🧠 Diagnóstico Financiero Integral")
    st.caption("Genera una evaluación estratégica de los hábitos de consumo y recomendaciones de ahorro.")
    if st.button("🚀 Generar Diagnóstico Financiero", type="primary"):
        with st.spinner("Procesando análisis multidimensional..."):
            informe = generar_resumen_ia(df_gastos_filtrado, ia_model)
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
                resp = responder_pregunta_financiera(prompt, df_gastos_filtrado, ia_model)
                st.markdown(resp)

        st.session_state.messages.append({"role": "assistant", "content": resp})