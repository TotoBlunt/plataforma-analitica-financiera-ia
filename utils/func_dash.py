import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ==============================================================================
# 1. FILTRADO DE DATOS
# ==============================================================================
def aplicar_filtros(df, persona, fechas, categorias):
    """Filtra el DataFrame según las selecciones del usuario en la barra lateral."""
    df_filtrado = df.copy()

    # Filtro de fecha
    if len(fechas) == 2:
        fecha_inicio = pd.to_datetime(fechas[0])
        fecha_fin = pd.to_datetime(fechas[1])
        df_filtrado = df_filtrado[(df_filtrado['Fecha'] >= fecha_inicio) & (df_filtrado['Fecha'] <= fecha_fin)]

    # Filtro de persona
    if persona != "Ambos" and 'Persona' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['Persona'] == persona]

    # Filtro de categoría
    if "Todas" not in categorias and 'Categoria' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['Categoria'].isin(categorias)]

    return df_filtrado

# ==============================================================================
# 2. MÉTRICAS CLAVE Y KPIs FINANCIEROS (MoM, Burn Rate, etc.)
# ==============================================================================
def mostrar_metricas_clave(df_filtrado, df_referencia=None):
    """
    Presenta KPIs financieros ejecutivos incluyendo variación intermensual (MoM),
    gasto diario promedio (Burn Rate) y ticket medio.
    """
    st.subheader("📊 Resumen Ejecutivo del Período")

    if df_filtrado.empty:
        st.info("Sin registros para el filtro seleccionado.")
        return

    total_gastado = df_filtrado['Monto'].sum()
    num_transacciones = len(df_filtrado)
    ticket_promedio = df_filtrado['Monto'].mean() if num_transacciones > 0 else 0

    # Rango en días para calcular burn rate diario
    dias_periodo = (df_filtrado['Fecha'].max() - df_filtrado['Fecha'].min()).days + 1
    dias_periodo = max(dias_periodo, 1)
    gasto_diario_promedio = total_gastado / dias_periodo

    # Cálculo de Variación MoM (Month over Month)
    delta_mom_str = None
    delta_mom_color = "normal"
    df_base = df_referencia if df_referencia is not None and not df_referencia.empty else df_filtrado

    try:
        # Agrupar por Periodo Año-Mes
        df_temp = df_base.copy()
        df_temp['Periodo'] = df_temp['Fecha'].dt.to_period('M')
        gastos_mensuales = df_temp.groupby('Periodo')['Monto'].sum().sort_index()

        if len(gastos_mensuales) >= 2:
            mes_actual = gastos_mensuales.iloc[-1]
            mes_previo = gastos_mensuales.iloc[-2]
            if mes_previo > 0:
                variacion_pct = ((mes_actual - mes_previo) / mes_previo) * 100
                delta_mom_str = f"{variacion_pct:+.1f}% vs mes anterior"
                # En finanzas personales: si el gasto baja (negativo) es favorable (verde)
                delta_mom_color = "inverse"
    except Exception:
        pass

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label="Gasto Total",
            value=f"S/ {total_gastado:,.2f}",
            delta=delta_mom_str,
            delta_color=delta_mom_color
        )
    with col2:
        st.metric(
            label="Gasto Diario (Burn Rate)",
            value=f"S/ {gasto_diario_promedio:,.2f} / día"
        )
    with col3:
        st.metric(
            label="Ticket Promedio",
            value=f"S/ {ticket_promedio:,.2f}"
        )
    with col4:
        st.metric(
            label="Nº Transacciones",
            value=f"{num_transacciones:,}"
        )

# ==============================================================================
# 3. ANÁLISIS DE LA REGLA 50 / 30 / 20
# ==============================================================================
def mostrar_kpis_regla_50_30_20(df):
    """
    Clasifica los gastos según el framework financiero 50/30/20:
    - Necesidades Básicas (50%): Hogar, Comida, Transporte, Salud, Deuda fija
    - Deseos / Ocio (30%): Ocio, Ropa, Restaurantes/Delivery, Hobbies, Tecnología
    - Ahorro e Inversión (20%): Ahorro/Inversión, Educación financiera
    """
    if df.empty:
        return

    # Mapeo configurable de categorías a pilares 50/30/20
    mapa_pilares = {
        'Hogar': 'Necesidades (50%)',
        'Comida': 'Necesidades (50%)',
        'Transporte': 'Necesidades (50%)',
        'Salud': 'Necesidades (50%)',
        'Deuda': 'Necesidades (50%)',
        'Ocio': 'Deseos (30%)',
        'Ropa y Calzado': 'Deseos (30%)',
        'Tecnología': 'Deseos (30%)',
        'Regalos': 'Deseos (30%)',
        'Ahorro/Inversión': 'Ahorro / Futuro (20%)',
        'Educación': 'Ahorro / Futuro (20%)',
        'Otro': 'Deseos (30%)'
    }

    df_pilar = df.copy()
    df_pilar['Pilar'] = df_pilar['Categoria'].map(mapa_pilares).fillna('Deseos (30%)')

    resumen_pilares = df_pilar.groupby('Pilar')['Monto'].sum()
    total = resumen_pilares.sum()

    if total == 0:
        return

    pct_necesidades = (resumen_pilares.get('Necesidades (50%)', 0) / total) * 100
    pct_deseos = (resumen_pilares.get('Deseos (30%)', 0) / total) * 100
    pct_ahorro = (resumen_pilares.get('Ahorro / Futuro (20%)', 0) / total) * 100

    with st.expander("⚖️ Diagnóstico de Distribución Financiera (Regla 50 / 30 / 20)", expanded=False):
        st.markdown(
            """
            El modelo **50/30/20** es el estándar de salud financiera personal:
            * **50% Necesidades**: Gastos esenciales para vivir (alojamiento, alimentación básica, salud).
            * **30% Deseos**: Ocio, estilo de vida, salidas y compras personales.
            * **20% Ahorro/Inversión**: Fondo de emergencia, ahorro a largo plazo y amortizaciones.
            """
        )

        c1, c2, c3 = st.columns(3)
        c1.metric(
            "Necesidades (Meta: 50%)",
            f"{pct_necesidades:.1f}%",
            delta=f"{pct_necesidades - 50:+.1f}% vs meta",
            delta_color="inverse"
        )
        c2.metric(
            "Deseos (Meta: 30%)",
            f"{pct_deseos:.1f}%",
            delta=f"{pct_deseos - 30:+.1f}% vs meta",
            delta_color="inverse"
        )
        c3.metric(
            "Ahorro / Futuro (Meta: 20%)",
            f"{pct_ahorro:.1f}%",
            delta=f"{pct_ahorro - 20:+.1f}% vs meta",
            delta_color="normal"
        )

        # Gráfico comparativo de barras apiladas
        fig_pilar = go.Figure()
        fig_pilar.add_trace(go.Bar(
            name='Tu Distribución Real',
            y=['Presupuesto'],
            x=[pct_necesidades],
            text=[f"Necesidades: {pct_necesidades:.1f}%"],
            textposition='inside',
            orientation='h',
            marker_color='#2b5c8f'
        ))
        fig_pilar.add_trace(go.Bar(
            name='Deseos',
            y=['Presupuesto'],
            x=[pct_deseos],
            text=[f"Deseos: {pct_deseos:.1f}%"],
            textposition='inside',
            orientation='h',
            marker_color='#d97706'
        ))
        fig_pilar.add_trace(go.Bar(
            name='Ahorro',
            y=['Presupuesto'],
            x=[pct_ahorro],
            text=[f"Ahorro: {pct_ahorro:.1f}%"],
            textposition='inside',
            orientation='h',
            marker_color='#059669'
        ))

        fig_pilar.update_layout(
            barmode='stack',
            title='Distribución Porcentual Real de tus Gastos',
            height=200,
            margin=dict(l=10, r=10, t=30, b=10),
            xaxis=dict(range=[0, 100], title="Porcentaje (%)"),
            showlegend=True
        )
        st.plotly_chart(fig_pilar, use_container_width=True)

# ==============================================================================
# 4. VISUALIZACIONES PRINCIPALES (Donut, Evolución, Comparativa, Treemap)
# ==============================================================================
def graficar_distribucion_categoria(df):
    """Muestra un Donut Chart elegante y tabla de concentración por categoría."""
    st.write("#### 🎯 Distribución de Gasto por Categoría")
    gastos_cat = df.groupby('Categoria')['Monto'].sum().sort_values(ascending=False).reset_index()

    if not gastos_cat.empty:
        total = gastos_cat['Monto'].sum()
        gastos_cat['Porcentaje'] = (gastos_cat['Monto'] / total) * 100

        fig = px.pie(
            gastos_cat,
            names='Categoria',
            values='Monto',
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Prism,
            title=f"Volumen Total: S/ {total:,.2f}"
        )
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>Monto: S/ %{value:,.2f}<br>Participación: %{percent:.1%}<extra></extra>'
        )
        fig.update_layout(
            margin=dict(t=40, b=10, l=10, r=10),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos disponibles para mostrar la distribución.")

def graficar_evolucion_temporal(df):
    """
    Muestra la serie temporal diaria junto a la media móvil de 7 días (Rolling 7D)
    para filtrar la volatilidad y destacar la tendencia subyacente.
    """
    st.write("#### 📈 Dinámica Temporal y Tendencia de Gasto")
    if df.empty:
        st.info("Sin registros temporales.")
        return

    gastos_diarios = df.groupby(df['Fecha'].dt.date)['Monto'].sum().reset_index()
    gastos_diarios.columns = ['Fecha', 'Monto_Diario']
    gastos_diarios['Fecha'] = pd.to_datetime(gastos_diarios['Fecha'])
    gastos_diarios.sort_values(by='Fecha', inplace=True)

    # Calcular Media Móvil a 7 días
    gastos_diarios['Media_Movil_7D'] = gastos_diarios['Monto_Diario'].rolling(window=7, min_periods=1).mean()
    gastos_diarios['Gasto_Acumulado'] = gastos_diarios['Monto_Diario'].cumsum()

    fig = go.Figure()

    # Barras de gasto diario
    fig.add_trace(go.Bar(
        x=gastos_diarios['Fecha'],
        y=gastos_diarios['Monto_Diario'],
        name='Gasto Diario',
        opacity=0.45,
        marker_color='#6366f1',
        hovertemplate='Fecha: %{x|%d/%m/%Y}<br>Gasto Diario: S/ %{y:,.2f}<extra></extra>'
    ))

    # Línea de media móvil
    fig.add_trace(go.Scatter(
        x=gastos_diarios['Fecha'],
        y=gastos_diarios['Media_Movil_7D'],
        name='Tendencia (Media Móvil 7d)',
        line=dict(color='#ef4444', width=3),
        mode='lines',
        hovertemplate='Fecha: %{x|%d/%m/%Y}<br>Media Móvil 7d: S/ %{y:,.2f}<extra></extra>'
    ))

    fig.update_layout(
        title="Gasto Diario vs Tendencia Suavizada",
        xaxis_title="Fecha",
        yaxis_title="Monto (S/)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=50, b=10, l=10, r=10),
        height=380
    )
    st.plotly_chart(fig, use_container_width=True)

def graficar_comparativa_persona(df):
    """Presenta el aporte proporcional y absoluto por integrante."""
    st.write("#### 👥 Distribución y Aporte por Integrante")
    if 'Persona' not in df.columns or df.empty:
        st.info("No hay datos de integrantes para comparar.")
        return

    gastos_persona = df.groupby('Persona')['Monto'].agg(['sum', 'count', 'mean']).reset_index()
    gastos_persona.columns = ['Persona', 'Total', 'Transacciones', 'Promedio']
    total_gral = gastos_persona['Total'].sum()
    gastos_persona['Pct'] = (gastos_persona['Total'] / total_gral) * 100 if total_gral > 0 else 0
    gastos_persona.sort_values(by='Total', ascending=False, inplace=True)

    fig = px.bar(
        gastos_persona,
        x='Persona',
        y='Total',
        color='Persona',
        text=gastos_persona.apply(lambda r: f"S/ {r['Total']:,.2f}<br>({r['Pct']:.1f}%)", axis=1),
        title="Gasto Acumulado por Integrante",
        labels={'Total': 'Total Desembolsado (S/)', 'Persona': 'Integrante'},
        color_discrete_sequence=['#3b82f6', '#10b981', '#f59e0b']
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide', margin=dict(t=50, b=20, l=20, r=20))
    st.plotly_chart(fig, use_container_width=True)

def graficar_detalle_subcategoria(df):
    """Treemap interactivo de descomposición Categoria -> Subcategoria."""
    st.write("#### 🌳 Descomposición Jerárquica de Subcategorías")
    df_subcat = df[df['Subcategoria'].notna() & (df['Subcategoria'].astype(str).str.strip() != '')].copy()

    if not df_subcat.empty:
        gastos_sub = df_subcat.groupby(['Categoria', 'Subcategoria'])['Monto'].sum().reset_index()
        fig = px.treemap(
            gastos_sub,
            path=[px.Constant("Presupuesto Total"), 'Categoria', 'Subcategoria'],
            values='Monto',
            color='Monto',
            color_continuous_scale='Blues',
            title='Estructura de Gasto Jerárquica'
        )
        fig.update_traces(hovertemplate='<b>%{label}</b><br>Monto: S/ %{value:,.2f}<extra></extra>')
        fig.update_layout(margin=dict(t=40, b=10, l=10, r=10), height=450)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay subcategorías registradas para el filtro seleccionado.")

# ==============================================================================
# 5. TABLA DE DATOS ANALÍTICA CON DESCARGA
# ==============================================================================
def mostrar_tabla_detallada(df):
    """Muestra la tabla analítica con ordenamiento, formato y opción de exportación CSV."""
    st.write("#### 📄 Registros Analíticos del Período")
    if df.empty:
        st.info("Sin registros.")
        return

    cols_disponibles = [c for c in ['Fecha', 'Descripcion', 'Categoria', 'Subcategoria', 'Tipo de Gasto', 'Persona', 'Monto', 'Notas'] if c in df.columns]
    df_display = df[cols_disponibles].copy()
    df_display.sort_values(by="Fecha", ascending=False, inplace=True)

    c_btn, _ = st.columns([1, 3])
    with c_btn:
        csv_data = df_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Exportar datos a CSV",
            data=csv_data,
            file_name="gastos_filtrados.csv",
            mime="text/csv"
        )

    # Formato visual para mostrar
    df_mostrar = df_display.copy()
    df_mostrar['Fecha'] = df_mostrar['Fecha'].dt.strftime('%d/%m/%Y')
    df_mostrar['Monto'] = df_mostrar['Monto'].map(lambda x: f"S/ {x:,.2f}")

    st.dataframe(df_mostrar, use_container_width=True, height=400)