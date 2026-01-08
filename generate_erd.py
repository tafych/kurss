# generate_erd_simple.py
from app import db
from sqlalchemy import inspect
import json


def generate_erd_description():
    """Генерирует текстовое описание структуры БД"""
    inspector = inspect(db.engine)

    output = []
    output.append("=" * 60)
    output.append("DATABASE SCHEMA DESCRIPTION")
    output.append("=" * 60)

    # Получаем все таблицы
    tables = inspector.get_table_names()

    for table_name in tables:
        output.append(f"\nTABLE: {table_name}")
        output.append("-" * 40)

        # Получаем колонки
        columns = inspector.get_columns(table_name)
        for column in columns:
            col_info = f"  {column['name']}: {column['type']}"
            if column.get('primary_key'):
                col_info += " [PK]"
            if column.get('nullable') is False:
                col_info += " [NOT NULL]"
            if column.get('unique'):
                col_info += " [UNIQUE]"
            output.append(col_info)

        # Получаем внешние ключи
        foreign_keys = inspector.get_foreign_keys(table_name)
        if foreign_keys:
            output.append("\n  FOREIGN KEYS:")
            for fk in foreign_keys:
                ref = f"{fk['referred_table']}.{fk['referred_columns'][0]}"
                output.append(f"    → {ref}")

    # Сохраняем в файл
    with open('database_schema.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))

    print('\n'.join(output))
    print("\n✓ Описание схемы сохранено в 'database_schema.txt'")


def generate_plantuml_code():
    """Генерирует код для PlantUML"""
    inspector = inspect(db.engine)

    plantuml = []
    plantuml.append("@startuml")
    plantuml.append("' ER Diagram for Warehouse Management System")
    plantuml.append("hide circle")
    plantuml.append("skinparam linetype ortho")
    plantuml.append("")

    # Создаем сущности (таблицы)
    tables = inspector.get_table_names()

    for table_name in tables:
        plantuml.append(f"entity \"{table_name}\" {{")

        columns = inspector.get_columns(table_name)
        for column in columns:
            line = f"  {column['name']} : {column['type']}"
            if column.get('primary_key'):
                line += " <<PK>>"
            if column.get('nullable') is False:
                line += " <<NN>>"
            plantuml.append(line)

        plantuml.append("}")
        plantuml.append("")

    # Создаем связи
    for table_name in tables:
        foreign_keys = inspector.get_foreign_keys(table_name)
        for fk in foreign_keys:
            for col in fk['constrained_columns']:
                plantuml.append(f"{table_name} ||--o| {fk['referred_table']} : \"{col}\"")

    plantuml.append("@enduml")

    # Сохраняем
    with open('database_plantuml.puml', 'w', encoding='utf-8') as f:
        f.write('\n'.join(plantuml))

    print("\n✓ PlantUML код сохранен в 'database_plantuml.puml'")
    print("\nВы можете:")
    print("1. Открыть на http://www.plantuml.com/plantuml")
    print("2. Установить PlantUML plugin в VS Code")
    print("3. Использовать локальный PlantUML")


def generate_json_schema():
    """Генерирует JSON схему БД"""
    inspector = inspect(db.engine)

    schema = {
        "database": "warehouse_new.db",
        "tables": {}
    }

    tables = inspector.get_table_names()

    for table_name in tables:
        table_info = {
            "columns": [],
            "primary_keys": [],
            "foreign_keys": []
        }

        # Колонки
        columns = inspector.get_columns(table_name)
        for column in columns:
            col_info = {
                "name": column['name'],
                "type": str(column['type']),
                "nullable": column.get('nullable', True),
                "primary_key": column.get('primary_key', False),
                "unique": column.get('unique', False)
            }
            table_info["columns"].append(col_info)

            if col_info["primary_key"]:
                table_info["primary_keys"].append(column['name'])

        # Внешние ключи
        foreign_keys = inspector.get_foreign_keys(table_name)
        for fk in foreign_keys:
            fk_info = {
                "constrained_columns": fk['constrained_columns'],
                "referred_table": fk['referred_table'],
                "referred_columns": fk['referred_columns']
            }
            table_info["foreign_keys"].append(fk_info)

        schema["tables"][table_name] = table_info

    # Сохраняем
    with open('database_schema.json', 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=2, default=str)

    print("\n✓ JSON схема сохранена в 'database_schema.json'")
    return schema


def create_html_report():
    """Создает HTML отчет о структуре БД"""
    schema = generate_json_schema()

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Database Schema Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            h1 { color: #333; }
            .table { margin-bottom: 30px; border: 1px solid #ddd; padding: 15px; }
            .table-name { background: #f5f5f5; padding: 10px; font-weight: bold; }
            .column { padding: 5px 0; border-bottom: 1px solid #eee; }
            .pk { color: #d32f2f; font-weight: bold; }
            .fk { color: #1976d2; }
        </style>
    </head>
    <body>
        <h1>Database Schema Report</h1>
        <p>Generated: """ + str(datetime.now()) + """</p>
    """

    for table_name, table_info in schema["tables"].items():
        html += f"""
        <div class="table">
            <div class="table-name">{table_name}</div>
            <div class="columns">
        """

        for col in table_info["columns"]:
            classes = []
            if col["primary_key"]:
                classes.append("pk")

            class_str = f" class=\"{' '.join(classes)}\"" if classes else ""
            html += f"""
                <div{class_str}>
                    {col["name"]} : {col["type"]}
                    {"" if col["nullable"] else " [NOT NULL]"}
                    {"" if not col["unique"] else " [UNIQUE]"}
                </div>
            """

        if table_info["foreign_keys"]:
            html += """
                <div style="margin-top: 10px; color: #666;">
                    <strong>Foreign Keys:</strong>
            """
            for fk in table_info["foreign_keys"]:
                html += f"""
                    <div class="fk">
                        {', '.join(fk["constrained_columns"])} → 
                        {fk["referred_table"]}({', '.join(fk["referred_columns"])})
                    </div>
                """
            html += "</div>"

        html += "</div></div>"

    html += """
    </body>
    </html>
    """

    with open('database_report.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("\n✓ HTML отчет сохранен в 'database_report.html'")
    print("Откройте этот файл в браузере для просмотра")


if __name__ == "__main__":
    print("Генерация документации базы данных...")
    print("=" * 60)

    generate_erd_description()
    generate_plantuml_code()
    generate_json_schema()
    create_html_report()

    print("\n" + "=" * 60)
    print("✅ Вся документация успешно сгенерирована!")
    print("Файлы:")
    print("  - database_schema.txt (текстовое описание)")
    print("  - database_plantuml.puml (для PlantUML)")
    print("  - database_schema.json (JSON схема)")
    print("  - database_report.html (HTML отчет)")