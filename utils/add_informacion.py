import logging
from datetime import datetime
import uuid
import gspread

logger = logging.getLogger(__name__)

# ==============================================================================
# GESTIÓN DE GASTOS
# ==============================================================================
def ingresar_gasto(worksheet, fecha, monto, descripcion, persona, categoria, subcategoria, tipo_gasto, notas):
    """
    Ingresa una nueva fila de gasto en la hoja de cálculo especificada.
    """
    if worksheet is None:
        return (False, "No hay conexión activa a la hoja de cálculo.")

    try:
        if not descripcion or str(descripcion).strip() == "":
            return (False, "La descripción no puede estar vacía.")

        if monto is None or float(monto) <= 0:
            return (False, "El monto debe ser un valor positivo mayor a 0.")

        id_gasto = f"G-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4]}"
        fecha_str = fecha.strftime("%Y-%m-%d") if hasattr(fecha, "strftime") else str(fecha)

        nueva_fila = [
            id_gasto,
            fecha_str,
            float(monto),
            str(descripcion).strip(),
            str(persona),
            str(categoria),
            str(subcategoria or "").strip(),
            str(tipo_gasto or "Variable Diario"),
            str(notas or "").strip()
        ]

        worksheet.append_row(nueva_fila)
        return (True, "¡Gasto agregado exitosamente!")

    except Exception as e:
        logger.error(f"Error al ingresar gasto en Google Sheets: {e}")
        return (False, "No se pudo guardar el gasto. Verifique permisos o conexión.")

def eliminar_gasto(worksheet, id_gasto):
    """
    Elimina un gasto por su ID_Gasto.
    """
    if worksheet is None:
        return (False, "No hay conexión activa a la hoja de cálculo.")

    try:
        cell = worksheet.find(str(id_gasto), in_column=1)
        if cell is None:
            return (False, f"No se encontró el registro con ID {id_gasto}.")

        worksheet.delete_rows(cell.row)
        return (True, "Registro eliminado exitosamente.")

    except Exception as e:
        logger.error(f"Error al eliminar gasto con ID {id_gasto}: {e}")
        return (False, "No se pudo eliminar el gasto.")

def editar_gasto(worksheet, id_gasto, nuevos_datos):
    """
    Actualiza los valores de un gasto existente según su ID.
    """
    if worksheet is None:
        return (False, "No hay conexión activa a la hoja de cálculo.")

    try:
        cell = worksheet.find(str(id_gasto), in_column=1)
        if cell is None:
            return (False, f"No se encontró el registro con ID {id_gasto}.")

        fila_a_editar = cell.row
        encabezados = worksheet.row_values(1)

        celdas_a_actualizar = []
        for campo, valor in nuevos_datos.items():
            if campo in encabezados:
                columna_a_editar = encabezados.index(campo) + 1
                celda = gspread.Cell(fila_a_editar, columna_a_editar, str(valor))
                celdas_a_actualizar.append(celda)

        if celdas_a_actualizar:
            worksheet.update_cells(celdas_a_actualizar, value_input_option='USER_ENTERED')
            return (True, "Gasto actualizado exitosamente.")
        else:
            return (False, "No se suministraron campos válidos para actualizar.")

    except Exception as e:
        logger.error(f"Error al editar gasto con ID {id_gasto}: {e}")
        return (False, "No se pudieron guardar las modificaciones del gasto.")

# ==============================================================================
# GESTIÓN DE INGRESOS
# ==============================================================================
def ingresar_ingreso(worksheet, fecha, monto, descripcion, persona, categoria):
    """
    Ingresa una nueva fila de ingreso en la hoja de cálculo de Ingresos.
    Columnas: ID_Ingreso, Fecha, Monto, Descripcion, Persona, Categoria
    """
    if worksheet is None:
        return (False, "No hay conexión activa a la hoja de cálculo de Ingresos.")

    try:
        if not descripcion or str(descripcion).strip() == "":
            return (False, "La descripción del ingreso no puede estar vacía.")

        if monto is None or float(monto) <= 0:
            return (False, "El monto del ingreso debe ser mayor a 0.")

        id_ingreso = f"ING-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4]}"
        fecha_str = fecha.strftime("%Y-%m-%d") if hasattr(fecha, "strftime") else str(fecha)

        nueva_fila = [
            id_ingreso,
            fecha_str,
            float(monto),
            str(descripcion).strip(),
            str(persona),
            str(categoria or "Sueldo Fijo")
        ]

        worksheet.append_row(nueva_fila)
        return (True, "¡Ingreso registrado exitosamente!")

    except Exception as e:
        logger.error(f"Error al ingresar entrada de ingreso en Google Sheets: {e}")
        return (False, "No se pudo registrar el ingreso. Verifique la conexión.")

def eliminar_ingreso(worksheet, id_ingreso):
    """
    Elimina un ingreso por su ID_Ingreso.
    """
    if worksheet is None:
        return (False, "No hay conexión activa a la hoja de cálculo de Ingresos.")

    try:
        cell = worksheet.find(str(id_ingreso), in_column=1)
        if cell is None:
            return (False, f"No se encontró el ingreso con ID {id_ingreso}.")

        worksheet.delete_rows(cell.row)
        return (True, "Ingreso eliminado exitosamente.")

    except Exception as e:
        logger.error(f"Error al eliminar ingreso con ID {id_ingreso}: {e}")
        return (False, "No se pudo eliminar el ingreso.")