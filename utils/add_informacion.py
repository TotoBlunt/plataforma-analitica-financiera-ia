import logging
from datetime import datetime
import uuid
import gspread

logger = logging.getLogger(__name__)

def ingresar_gasto(worksheet, fecha, monto, descripcion, persona, categoria, subcategoria, tipo_gasto, notas):
    """
    Ingresa una nueva fila de gasto en la hoja de cálculo especificada.

    Args:
        worksheet (gspread.Worksheet): Objeto de hoja de cálculo donde se insertarán los datos.
        fecha (datetime.date): Fecha del gasto.
        monto (float): Monto numérico del gasto.
        descripcion (str): Detalle del gasto.
        persona (str): Persona que efectuó el pago.
        categoria (str): Categoría del gasto.
        subcategoria (str): Subcategoría opcional.
        tipo_gasto (str): Fijo, Variable, etc.
        notas (str): Observaciones adicionales.

    Returns:
        tuple: (bool, str) indicando éxito y mensaje descriptivo.
    """
    if worksheet is None:
        return (False, "No hay conexión activa a la hoja de cálculo (Modo Demostración activo o sin conexión).")

    try:
        # Validación de datos
        if not descripcion or str(descripcion).strip() == "":
            return (False, "La descripción no puede estar vacía.")

        if monto is None or float(monto) <= 0:
            return (False, "El monto debe ser un valor positivo mayor a 0.")

        # Generación de ID único y fecha formateada
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
        return (False, "No se pudo guardar el gasto. Verifique los permisos de la hoja o su conexión de red.")

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
        return (True, f"Registro eliminado exitosamente.")

    except Exception as e:
        logger.error(f"Error al eliminar gasto con ID {id_gasto}: {e}")
        return (False, "No se pudo eliminar el gasto. Ocurrió un error de comunicación.")

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
            return (True, f"Gasto actualizado exitosamente.")
        else:
            return (False, "No se suministraron campos válidos para actualizar.")

    except Exception as e:
        logger.error(f"Error al editar gasto con ID {id_gasto}: {e}")
        return (False, "No se pudieron guardar las modificaciones del gasto.")