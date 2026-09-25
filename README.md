# 📊 Plataforma de Analítica Financiera & Asistente Inteligente

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://finanzasfamiliares.streamlit.app/)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Security: AST Validated](https://img.shields.io/badge/Security-AST%20Sandbox-success)](utils/func_ai.py)
[![Data: Demo Ready](https://img.shields.io/badge/Data-Demo%20Ready%20(1.4k+)-brightgreen)](data/demo_finanzas.csv)

Una plataforma end-to-end de **Inteligencia de Negocio y Finanzas Personales** desarrollada en Python y Streamlit. Diseñada para transformar el registro diario de transacciones en **decisiones financieras estratégicas**, combinando analítica descriptiva avanzada, KPIs de salud financiera (**Regla 50/30/20**, **MoM %**, **Burn Rate**), análisis exploratorio estadístico (EDA) y asistencia conversacional segura mediante **Google Gemini AI**.

---

## 🎯 Caso de Negocio & Objetivos Analíticos

La gestión financiera suele fallar por falta de visibilidad y análisis oportuno. Este proyecto aborda y resuelve las siguientes preguntas de negocio:

1. **¿Cómo se distribuyen los egresos frente a las mejores prácticas financieras?**  
   Implementación del diagnóstico automatizado de la **Regla 50/30/20** (*Necesidades 50% / Deseos 30% / Ahorro 20%*).
2. **¿Existe aceleración o desaceleración en el ritmo de gasto?**  
   Cálculo del **Month-over-Month (MoM %)** y del **Burn Rate diario** para proyectar el flujo de caja al cierre de mes.
3. **¿Cuáles son las transacciones atípicas que distorsionan el presupuesto?**  
   Detección de anomalías cuantitativas mediante **Rango Intercuartílico (IQR)** en el flujo analítico y en el Notebook exploratorio.
4. **¿Cómo facilitar el acceso a la información a usuarios no técnicos?**  
   Interfaz conversacional en lenguaje natural con validación de seguridad AST (*Text-to-Insights*).

---

## 🏗️ Arquitectura del Proyecto & Funcionalidades por Módulo

El sistema cuenta con una arquitectura desacoplada, modular y orientada a la seguridad:

```
Analisis_finanzas_personales/
├── app.py                            # Orquestador UI en Streamlit y flujo principal
├── requirements.txt                  # Dependencias optimizadas y modernas
├── .gitignore                        # Blindaje de secretos y archivos temporales
├── .streamlit/
│   └── secrets.toml.example          # Plantilla segura de configuración de credenciales
├── data/
│   └── demo_finanzas.csv             # Dataset sintético de 1,480 transacciones (Modo Demo)
├── notebooks/
│   └── 01_eda_analisis_financiero.ipynb # Análisis estadístico riguroso (Pareto, Outliers, 50/30/20)
└── utils/
    ├── conn_Gsheet.py                # Conexión moderna a Google Sheets con google-auth
    ├── add_informacion.py            # Operaciones transaccionales CRUD con validación estricta
    ├── func_dash.py                  # Motor de KPIs analíticos y visualizaciones Plotly
    └── func_ai.py                    # Integración Gemini AI con sandbox AST y fallback offline
```

### Detalle de Módulos

#### 1. `app.py` (Orquestador Central)
* **Selector de Fuente de Datos:** Permite alternar en tiempo real entre el **Modo Demostración** (ideal para reclutadores, con 1,480 transacciones listas para explorar) y el **Modo Producción** (Google Sheets en la nube).
* **Anonimización Dinámica:** Elimina datos personales (PII) hardcodeados, detectando automáticamente los integrantes a partir del dataset.
* **Flujo Transaccional:** Registro, categorización asistida y edición/depuración en vivo (incluso en memoria de sesión en Modo Demo).

#### 2. `utils/func_dash.py` (Capa de Inteligencia y Métricas)
* `mostrar_metricas_clave()`: Cálculo de gasto total con **delta MoM %**, gasto diario promedio (*Burn Rate*), ticket medio y volumen de operaciones.
* `mostrar_kpis_regla_50_30_20()`: Agrupación analítica de categorías en *Necesidades*, *Deseos* y *Ahorro*, comparando la distribución real vs. las metas estándar con gráficos de barras apiladas.
* `graficar_evolucion_temporal()`: Visualización dual que combina el gasto diario con una **Media Móvil a 7 días (Rolling 7D)** para filtrar la volatilidad y destacar la tendencia real.
* `graficar_distribucion_categoria()`: Donut Chart interactivo de alta legibilidad con porcentajes y montos acumulados.
* `graficar_comparativa_persona()` y `graficar_detalle_subcategoria()`: Desglose comparativo por integrante y Treemap jerárquico.
* `mostrar_tabla_detallada()`: Tabla de auditoría con botón de **exportación directa a CSV**.

#### 3. `utils/func_ai.py` (Inteligencia Artificial y Seguridad)
* **Sandbox AST (`_validar_seguridad_ast`)**: Mitiga riesgos de Ejecución Remota de Código (RCE). Inspecciona el Árbol de Sintaxis Abstracta antes de cualquier cálculo en Pandas, bloqueando imports, llamadas al sistema (`os`, `sys`, `eval`, `exec`) o acceso a atributos privados (`__`).
* `generar_insights_proactivos()`: Detecta concentración de gastos, día pico de desembolso y transacciones atípicas (outliers IQR). Funciona de forma autónoma tanto con Gemini como en modo analítico offline.
* `generar_resumen_ia()`: Diagnóstico financiero estratégico cualitativo/cuantitativo con recomendaciones accionables.
* `sugerir_categoria_ia()`: Asistente de autocompletado en el formulario de ingreso.

#### 4. `utils/conn_Gsheet.py` & `utils/add_informacion.py` (Capa de Datos y CRUD)
* **Migración a `google-auth`:** Reemplaza la biblioteca obsoleta `oauth2client` por `gspread.service_account_from_dict()`.
* **Saneamiento de Excepciones:** Los errores técnicos se gestionan mediante el módulo estándar `logging`, evitando filtrar rutas internas o secretos en la pantalla del usuario (*Information Disclosure*).
* **Generación de Claves Robustas:** Generación de identificadores únicos basados en timestamp y UUID.

#### 5. `notebooks/01_eda_analisis_financiero.ipynb` (Evidencia para Portafolio)
* Análisis de estadísticas descriptivas completas (Mediana, IQR, Skewness).
* **Curva de Pareto (80/20)** para identificar las categorías críticas de gasto.
* **Detección de Outliers** mediante Boxplots y umbrales IQR formales.
* Análisis de estacionalidad por día de la semana y día del mes (patrón quincenal/inicio de mes).
* Conclusiones estructuradas para toma de decisiones financieras.

---

## 🔒 Mejoras de Seguridad Implementadas

| Vulnerabilidad / Hallazgo Previo | Solución Aplicada | Estado |
| :--- | :--- | :---: |
| **Ausencia de `.gitignore`** | Se creó un `.gitignore` integral que previene la fuga accidental de credenciales (`*.json`, `.streamlit/secrets.toml`, `.env`). | ✅ Resuelto |
| **RCE vía `exec()` arbitrario en chat** | Validación estricta mediante **AST (Abstract Syntax Tree)** y entorno restringido `__builtins__` seguro. | ✅ Resuelto |
| **Fuga de información (`st.write(e)`)** | Se reemplazó la impresión de trazas crudas por registro en `logging` y mensajes de usuario amigables. | ✅ Resuelto |
| **PII (Datos personales hardcodeados)** | Extracción dinámica de integrantes según el dataset, con datos de demostración anonimizados. | ✅ Resuelto |
| **Dependencias obsoletas y huérfanas** | Eliminación de `openai` y migración de `oauth2client` a `google-auth`. | ✅ Resuelto |

---

## 🚀 Puesta en Marcha Rápida (Local)

### 1. Clonar el repositorio e ingresar a la carpeta
```bash
git clone https://github.com/TotoBlunt/Analisis_finanzas_personales.git
cd Analisis_finanzas_personales
```

### 2. Crear entorno virtual e instalar dependencias
```bash
python -m venv .venv
# En Windows:
.venv\Scripts\activate
# En Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Iniciar la aplicación en Modo Demostración (Sin necesidad de API Keys)
```bash
streamlit run app.py
```
> La aplicación se iniciará por defecto en **Modo Demostración**, cargando el dataset analítico de 1,480 transacciones en `data/demo_finanzas.csv`.

---

## ☁️ Configuración para Producción (Google Sheets & Gemini)

Para conectar tu propia hoja de cálculo en la nube y habilitar Gemini AI:

1. Copia la plantilla de secretos:
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```
2. Completa tu clave de servicio de Google Cloud (`[gcp_service_account]`) y tu API Key de Gemini (`[google_ai]`).
3. En la barra lateral de la aplicación, cambia el selector a **"Modo Producción (Google Sheets)"**.

---

## 🛠️ Tecnologías Utilizadas

* **Lenguaje:** Python 3.10+
* **Framework Web:** Streamlit
* **Procesamiento de Datos:** Pandas, NumPy
* **Visualización Interactiva:** Plotly (Express & Graph Objects), Seaborn, Matplotlib
* **Capa Cloud / Backend:** Google Sheets API, Google Cloud Service Accounts (`gspread`, `google-auth`)
* **Inteligencia Artificial:** Google Gemini 1.5 Flash (`google-generativeai`)
* **Seguridad de Código:** Python AST (Abstract Syntax Tree)

---

## 📜 Licencia

Distribuido bajo la Licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más información.
