# Плагин СУБД SQLite
import os
import sqlite3


def execute_sql_commands(sql_statements: str, db_name: str) -> str:
    """Создает базы данных и выполняет SQL-запросы. Автоматически разворачивает папку Databases."""
    try:
        if not db_name.endswith(".db"):
            db_name += ".db"

        folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "DemonShell", "Databases")
        os.makedirs(folder, exist_ok=True)  # АВТОСОЗДАНИЕ ПАПКИ

        path = os.path.join(folder, db_name)
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        for stmt in sql_statements.split(';'):
            if stmt.strip():
                cursor.execute(stmt)
        conn.commit()
        conn.close()
        return f"База {db_name} обновлена в DemonShell/Databases"
    except Exception as e:
        return f"Ошибка SQL: {str(e)}"
