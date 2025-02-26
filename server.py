from flask import Flask
import sqlite3

app = Flask(__name__)

def get_users():
    conn = sqlite3.connect("phone_numbers.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, full_name, phone, career_result FROM phone_numbers")
    users = cursor.fetchall()
    conn.close()

    table_rows = "".join(
        f"<tr><td>{u[0]}</td><td>{u[1]}</td><td>{u[2]}</td><td>{u[3]}</td><td>{u[4]}</td></tr>" for u in users
    )

    html_content = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Список пользователей</title>
        <style>
            table {{ width: 100%%; border-collapse: collapse; }}
            th, td {{ border: 1px solid black; padding: 8px; text-align: left; }}
            th {{ background-color:rgba(139, 139, 139, 0.57); }}
        </style>
    </head>
    <body>
        <h2>Список пользователей</h2>
        <table>
            <tr>
                <th>ID</th>
                <th>Имя в телеграмм</th>
                <th>Имя фамилия</th>
                <th>Телефон</th>
                <th>Специальность</th>
            </tr>
            {table_rows}
        </table>
    </body>
    </html>
    """
    return html_content

@app.route('/', methods=['GET'])
def users():
    return get_users(), 200, {'Content-Type': 'text/html; charset=utf-8'}

