# Плагин генерации продвинутых отчетов Excel
import os
import json
import openpyxl
import pandas as pd
from openpyxl.utils.dataframe import dataframe_to_rows


def create_excel_report(json_data: str, filename: str) -> str:
    """Генерирует таблицы Excel из JSON. Автоматически разворачивает папку Reports/Excel."""
    try:
        if not filename.endswith(".xlsx"):
            filename += ".xlsx"

        folder_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "DemonShell", "Reports", "Excel")
        os.makedirs(folder_path, exist_ok=True)  # АВТОСОЗДАНИЕ ПАПКИ

        path = os.path.join(folder_path, filename)
        payload = json.loads(json_data)
        wb = openpyxl.Workbook()
        ws = wb.active
        df = pd.DataFrame(payload.get("sheets", {}).get("Report", payload))
        for r in dataframe_to_rows(df, index=False, header=True):
            ws.append(r)
        wb.save(path)
        return f"Excel сохранен в DemonShell/Reports/Excel/{filename}"
    except Exception as e:
        return f"Ошибка Excel: {str(e)}"
