from flask import Flask, request, jsonify
import requests
import sqlite3
from datetime import datetime

app = Flask(__name__)

AGENTS = [
    {"name": "PC-001", "ip": "192.168.1.101"},
    {"name": "PC-002", "ip": "192.168.1.102"}
]

AGENT_PORT = 8080
API_KEY = "SECRET123"
DB_FILE = "logs.db"

headers = {
    "X-Api-Key": API_KEY,
    "Content-Type": "application/json"
}

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_ip TEXT,
            action TEXT,
            timestamp TEXT,
            result TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route("/agents", methods=["GET"])
def list_agents():
    return jsonify(AGENTS)

@app.route("/inventory/<ip>", methods=["GET"])
def get_inventory(ip):
    try:
        url = f"http://{ip}:{AGENT_PORT}/inventory"
        resp = requests.get(url, headers=headers, timeout=5)
        save_log(ip, "inventory", resp.text)
        return jsonify(resp.json())
    except Exception as e:
        save_log(ip, "inventory", f"error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/deploy/<ip>", methods=["POST"])
def deploy_to_agent(ip):
    data = request.get_json()
    try:
        url = f"http://{ip}:{AGENT_PORT}/deploy"
        resp = requests.post(url, headers=headers, json=data, timeout=10)
        save_log(ip, f"deploy: {data.get('install_command')}", resp.text)
        return jsonify(resp.json())
    except Exception as e:
        save_log(ip, "deploy", f"error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/logs", methods=["GET"])
def get_logs():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 100")
    rows = cursor.fetchall()
    conn.close()
    logs = [
        {"id": row[0], "ip": row[1], "action": row[2], "time": row[3], "result": row[4]}
        for row in rows
    ]
    return jsonify(logs)

def save_log(ip, action, result):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    timestamp = datetime.utcnow().isoformat()
    cursor.execute("INSERT INTO logs (agent_ip, action, timestamp, result) VALUES (?, ?, ?, ?)",
                   (ip, action, timestamp, result))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
