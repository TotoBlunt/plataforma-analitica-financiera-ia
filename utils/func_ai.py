import os
import ast
import logging
import streamlit as st
import google.generativeai as genai
import pandas as pd

logger = logging.getLogger(__name__)

# ==============================================================================
# 1. INICIALIZACIÓN DEL CLIENTE
# ==============================================================================
def inicializar_cliente_ia():
    """
    Inicializa el cliente de Google Gemini si la clave existe en st.secrets o en variables de entorno.
    """
    api_key = None
    try:
        if hasattr(st, "secrets") and "google_ai" in st.secrets:
            api_key = st.secrets["google_ai"].get("api_key")
    except Exception:
        pass

    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        logger.info("API Key de Google Gemini no configurada.")
        return None

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        return model
    except Exception as e:
        logger.error(f"Error al configurar la API de Google Gemini: {e}")
        return None

# ==============================================================================
# 2. FUNCIONALIDADES DE ASISTENCIA Y CATEGORIZACIÓN
# ==============================================================================
def sugerir_categoria_ia(descripcion, categorias_posibles, model):
    """
    Usa Gemini para sugerir una categoría basada en la descripción del gasto.
    """
    if not model or not descripcion:
        return None

    prompt = f"""Dada la descripción de un gasto: "{descripcion}", ¿cuál de estas categorías es la más apropiada? 
Categorías disponibles: {', '.join(categorias_posibles)}. 
Responde únicamente con el nombre exacto de la categoría. Si ninguna encaja, responde 'Otro'."""
    try:
        response = model.generate_content(prompt)
        sugerencia = response.text.strip().replace("'", "").replace('"', '')
        return sugerencia if sugerencia in categorias_posibles else "Otro"
    except Exception as e:
        logger.error(f"Error al sugerir categoría con Gemini: {e}")
        return None

# ==============================================================================
# 3. RESÚMENES FINANCIEROS INTELIGENTES
# ==============================================================================
def generar_resumen_ia(df_filtrado, model):
    """
    Genera un informe analítico financiero. Si el modelo IA no está disponible,
    genera un análisis estadístico-descriptivo con Pandas para modo Demo.
    """
    if df_filtrado.empty:
        return "No hay transacciones registradas en el período seleccionado."

    gasto_total = df_filtrado['Monto'].sum()
    gastos_por_cat = df_filtrado.groupby('Categoria')['Monto'].sum().sort_values(ascending=False)
    cat_top = gastos_por_cat.index[0]
    monto_top = gastos_por_cat.iloc[0]
    pct_top = (monto_top / gasto_total) * 100 if gasto_total > 0 else 0
    promedio_transaccion = df_filtrado['Monto'].mean()

    # Si no hay modelo de IA disponible, generamos reporte analítico determinista
    if not model:
        return f"""
### 📊 Diagnóstico Financiero Analítico (Modo Offline / Demo)

* **Volumen Total:** Se registraron **S/{gasto_total:,.2f}** distribuidos en **{len(df_filtrado)}** movimientos con un ticket promedio de **S/{promedio_transaccion:,.2f}**.
* **Mayor Concentración:** La categoría **{cat_top}** absorbe el **{pct_top:.1f}%** del presupuesto del período (S/{monto_top:,.2f}).
* **Oportunidad de Eficiencia:** Diversificar o auditar las subcategorías de `{cat_top}` para verificar si corresponden a gastos fijos no negociables o gastos discrecionales.

*(💡 Para resúmenes generados con lenguaje natural conversacional, activa tu Google Gemini API Key).*
"""

    prompt = f"""
    Actúa como un asesor y analista financiero personal senior para una pareja/hogar. 
    Analiza con rigor y empatía estos datos consolidados:
    - Gasto Total: S/{gasto_total:,.2f}
    - Ticket promedio por transacción: S/{promedio_transaccion:,.2f}
    - Categoría con mayor peso: '{cat_top}' (S/{monto_top:,.2f}, {pct_top:.1f}% del total).
    - Desglose por categoría:
    {gastos_por_cat.to_string()}

    Escribe un informe conciso estructurado con:
    1. **Logros y Salud General**: Comportamiento destacable del período.
    2. **Focos de Atención**: Categorías con mayor dispersión o sobregasto.
    3. **Plan de Acción / Recomendación**: 2 pasos concretos para optimizar el ahorro en el próximo mes.
    Dirígete al equipo familiar en tono constructivo y profesional.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error al generar resumen con Gemini: {e}")
        return "Ocurrió un error al procesar el resumen con IA. Por favor, intente nuevamente."

# ==============================================================================
# 4. INSIGHTS ANALÍTICOS Y DETECCIÓN DE ANOMALÍAS
# ==============================================================================
def generar_insights_proactivos(df, ia_model):
    """
    Analiza el DataFrame para encontrar patrones cuantitativos, concentración y outliers.
    """
    if df.empty or len(df) < 5:
        return ["💡 Continúa registrando más transacciones para descubrir patrones analíticos."]

    insights_calculados = []
    gasto_total = df['Monto'].sum()

    # 1. Análisis de día de la semana
    df_temp = df.copy()
    dias_es = {
        'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
        'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
    }
    df_temp['Dia_Semana'] = df_temp['Fecha'].dt.day_name().map(dias_es).fillna(df_temp['Fecha'].dt.day_name())
    gasto_dia = df_temp.groupby('Dia_Semana')['Monto'].sum().sort_values(ascending=False)

    if not gasto_dia.empty:
        dia_max = gasto_dia.index[0]
        monto_dia_max = gasto_dia.iloc[0]
        pct_dia = (monto_dia_max / gasto_total) * 100 if gasto_total > 0 else 0
        insights_calculados.append(f"📅 El día de mayor desembolso suele ser el **{dia_max}** acumulando S/{monto_dia_max:,.2f} ({pct_dia:.1f}% del total).")

    # 2. Concentración por categoría
    gastos_cat = df.groupby('Categoria')['Monto'].sum().sort_values(ascending=False)
    if not gastos_cat.empty:
        cat_max = gastos_cat.index[0]
        pct_cat = (gastos_cat.iloc[0] / gasto_total) * 100 if gasto_total > 0 else 0
        insights_calculados.append(f"🎯 **{cat_max}** es la categoría dominante, absorbiendo el **{pct_cat:.1f}%** de los egresos.")

    # 3. Detección estadística de Outliers (Valores atípicos usando IQR)
    q75, q25 = df['Monto'].quantile(0.75), df['Monto'].quantile(0.25)
    iqr = q75 - q25
    umbral_outlier = q75 + (1.5 * iqr)
    outliers = df[df['Monto'] > umbral_outlier]

    if not outliers.empty:
        top_outlier = outliers.sort_values(by='Monto', ascending=False).iloc[0]
        insights_calculados.append(
            f"⚠️ Transacción atípica detectada: **{top_outlier['Descripcion']}** (S/{top_outlier['Monto']:,.2f}) en {top_outlier['Categoria']} supera el umbral IQR."
        )
    else:
        # Alternativa: proporción fija vs variable
        if 'Tipo de Gasto' in df.columns:
            fijo_vs_var = df.groupby('Tipo de Gasto')['Monto'].sum()
            if 'Fijo Mensual' in fijo_vs_var:
                pct_fijo = (fijo_vs_var['Fijo Mensual'] / gasto_total) * 100
                insights_calculados.append(f"📊 Los compromisos fijos representan el **{pct_fijo:.1f}%** de los egresos del período.")

    # Si no hay IA activa, devolver los insights analíticos directamente
    if not ia_model:
        return insights_calculados[:3]

    # Si hay IA activa, permitir enriquecer el tono y síntesis
    prompt = f"""
    Actúa como un analista financiero. Toma estos 3 hallazgos analíticos cuantificados y reescríbelos 
    en un formato visual, empático y directo para una pareja (máximo 1 línea por hallazgo, iniciando con un emoji):
    - {' '.join(insights_calculados)}
    No añadas introducciones ni despedidas, solo las viñetas separadas por salto de línea.
    """
    try:
        response = ia_model.generate_content(prompt)
        lineas = [l.strip() for l in response.text.strip().split('\n') if l.strip()]
        return lineas if len(lineas) >= 2 else insights_calculados[:3]
    except Exception as e:
        logger.error(f"Error al enriquecer insights con Gemini: {e}")
        return insights_calculados[:3]

# ==============================================================================
# 5. CONSULTA EN LENGUAJE NATURAL CON EJECUCIÓN SEGURA (SANDBOX AST)
# ==============================================================================
def _validar_seguridad_ast(codigo_str):
    """
    Valida mediante AST que el código no contenga imports, acceso a dunders/privados,
    ni invocaciones a funciones reservadas del sistema.
    """
    try:
        tree = ast.parse(codigo_str)
    except SyntaxError as e:
        return False, f"Sintaxis inválida en el código generado: {e}"

    nombres_prohibidos = {
        'eval', 'exec', 'open', 'compile', '__import__', 'globals', 'locals',
        'getattr', 'setattr', 'delattr', 'input', 'breakpoint', 'exit', 'quit',
        'subprocess', 'os', 'sys', 'shutil', 'socket', 'requests', 'urllib'
    }

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            return False, "Operación bloqueada: importación de librerías no permitida."
        if isinstance(node, ast.Attribute) and node.attr.startswith('_'):
            return False, "Operación bloqueada: acceso a propiedades internas o privadas no permitido."
        if isinstance(node, ast.Name) and node.id in nombres_prohibidos:
            return False, f"Operación bloqueada: uso de identificador reservado '{node.id}'."

    return True, ""

def responder_pregunta_financiera(pregunta_usuario, df, ia_model):
    """
    Procesa consultas analíticas en lenguaje natural.
    Implementa un pipeline: Gemini -> Generación de Consulta Pandas -> Validación AST -> Ejecución Sandbox -> Explicación.
    """
    if df.empty:
        return "No hay transacciones registradas para responder a tu consulta."

    if not ia_model:
        return "⚠️ La funcionalidad de consulta conversacional requiere configurar tu clave de Gemini en los secretos."

    # Prompt con especificación estricta de variables y esquema
    prompt_generar = f"""
    Actúa como un experto en Pandas y analítica financiera.
    El DataFrame se llama `df` con las siguientes columnas y tipos:
    {df.dtypes.to_string()}
    
    Pregunta del usuario: "{pregunta_usuario}"
    
    Genera ÚNICAMENTE código Python que asigne el resultado del cálculo a una variable llamada `resultado`.
    Reglas estrictas:
    - No uses `import`.
    - No redefinas `df`.
    - Asigna el resultado a `resultado`.
    - Devuelve SOLO el código sin comillas de markdown ```python ni explicaciones.
    """

    try:
        res_codigo = ia_model.generate_content(prompt_generar)
        codigo_raw = res_codigo.text.strip()
    except Exception as e:
        logger.error(f"Error al generar consulta con Gemini: {e}")
        return "Hubo un inconveniente al procesar tu consulta con la IA. Intenta reformularla."

    # Limpieza de código generado
    lineas = []
    for l in codigo_raw.split('\n'):
        l_str = l.strip()
        if not l_str.startswith('import ') and not l_str.startswith('from ') and not l_str.startswith('```'):
            lineas.append(l)
    codigo_limpio = "\n".join(lineas).strip()

    # Validación de seguridad AST
    es_seguro, razon_bloqueo = _validar_seguridad_ast(codigo_limpio)
    if not es_seguro:
        logger.warning(f"Consulta rechazada por seguridad AST: {razon_bloqueo} | Código: {codigo_limpio}")
        return f"Por motivos de seguridad, la consulta no pudo ser ejecutada ({razon_bloqueo})."

    # Ejecución en sandbox restringido
    safe_builtins = {
        'len': len, 'min': min, 'max': max, 'sum': sum, 'abs': abs,
        'round': round, 'str': str, 'int': int, 'float': float,
        'list': list, 'dict': dict, 'set': set, 'range': range
    }
    local_scope = {'df': df.copy(), 'pd': pd}
    global_scope = {'__builtins__': safe_builtins}

    try:
        exec(codigo_limpio, global_scope, local_scope)
        resultado_calc = local_scope.get('resultado', 'Cálculo ejecutado sin variable de retorno.')
    except Exception as e:
        logger.error(f"Error al ejecutar código Pandas en sandbox: {e}")
        return "No fue posible calcular la respuesta para esa pregunta específica. Intenta preguntar sobre montos, categorías o fechas puntuales."

    # Paso de síntesis y respuesta en lenguaje natural
    prompt_interpretar = f"""
    Eres un analista financiero. Un usuario preguntó: "{pregunta_usuario}".
    Se ejecutó un cálculo con el siguiente resultado cuantitativo:
    {str(resultado_calc)}
    
    Explica el resultado de forma clara, directa y en lenguaje natural (máximo 2 oraciones). Si es un valor monetario, exprésalo adecuadamente.
    """
    try:
        res_final = ia_model.generate_content(prompt_interpretar)
        return res_final.text.strip()
    except Exception as e:
        logger.error(f"Error al interpretar resultado con Gemini: {e}")
        return f"El resultado calculado fue: {str(resultado_calc)}"