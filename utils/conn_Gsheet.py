import logging
import gspread
import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

DEFAULT_SPREADSHEET = "FinanzasFamiliares"
DEFAULT_WORKSHEET = "Hoja 1"

def conexion_gsheet_produccion():
    """
    Establece conexión con Google Sheets usando los Secretos de Streamlit
    mediante el cliente moderno de gspread y google-auth.
    """
    try:
        if "gcp_service_account" not in st.secrets:
            logger.warning("Sección [gcp_service_account] no encontrada en st.secrets.")
            return None

        creds_dict = dict(st.secrets["gcp_service_account"])
        # gspread.service_account_from_dict utiliza internamente google-auth (sin oauth2client obsoleto)
        client = gspread.service_account_from_dict(creds_dict)
        return client

    except Exception as e:
        logger.error(f"Error al conectar con Google Sheets: {e}")
        return None

def abrir_hoja(client, sheet_name=None, worksheet_name=None):
    """
    Abre una hoja de cálculo específica y devuelve el objeto Worksheet.
    Permite configuración personalizada desde st.secrets o parámetros.
    """
    if client is None:
        return None

    # Obtener nombres desde configuración opcional o defaults
    cfg = st.secrets.get("app_config", {}) if hasattr(st, "secrets") else {}
    target_sheet = sheet_name or cfg.get("spreadsheet_name", DEFAULT_SPREADSHEET)
    target_worksheet = worksheet_name or cfg.get("worksheet_name", DEFAULT_WORKSHEET)

    try:
        spreadsheet = client.open(target_sheet)
        worksheet = spreadsheet.worksheet(target_worksheet)
        return worksheet
    except Exception as e:
        logger.error(f"Error al abrir la hoja '{target_sheet}' / '{target_worksheet}': {e}")
        return None

def cargar_datos(worksheet):
    """
    Carga los datos de la hoja de cálculo en un DataFrame de Pandas con validación de tipos.
    """
    if worksheet is None:
        return pd.DataFrame()

    try:
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)

        if not df.empty:
            # Asegurar columnas mínimas requeridas
            columnas_esperadas = ['ID_Gasto', 'Fecha', 'Monto', 'Descripcion', 'Persona', 'Categoria']
            for col in columnas_esperadas:
                if col not in df.columns:
                    df[col] = ""

            df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce').fillna(0.0)
            df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
            df.dropna(subset=['Fecha'], inplace=True)
            df.sort_values(by="Fecha", ascending=False, inplace=True)

        return df

    except Exception as e:
        logger.error(f"Error al leer registros de Google Sheets: {e}")
        return pd.DataFrame()