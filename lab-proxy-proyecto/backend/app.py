import os
import socket
import time

from flask import Flask, jsonify, request, render_template_string
from prometheus_flask_exporter import PrometheusMetrics
#---------------------CONFIGURACION SERVER VISUAL----------------------#
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ server_name }}</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: system-ui, -apple-system, sans-serif;
            background: #0f172a;
            color: #f8fafc;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        .topbar {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            background: #1e293b;
            border-bottom: 1px solid #334155;
            padding: 0.75rem 1rem;
            text-align: center;
            font-size: 1rem;
            color: #94a3b8;
            letter-spacing: 0.02em;
        }
        .topbar strong {
            color: #f8fafc;
            font-weight: 600;
            font-size: 1.15rem;
        }
        .card {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 1.75rem;
            width: 90%;
            max-width: 360px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.35);
        }
        .status {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(34, 197, 94, 0.15);
            color: #4ade80;
            font-size: 0.75rem;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 999px;
            margin-bottom: 1rem;
        }
        .dot {
            width: 8px;
            height: 8px;
            background: #4ade80;
            border-radius: 50%;
        }
        h1 {
            font-size: 1.35rem;
            margin-bottom: 1.25rem;
            color: #f1f5f9;
        }
        .info-box {
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 0.85rem 1rem;
            margin-bottom: 1.25rem;
        }
        .label {
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #94a3b8;
            margin-bottom: 4px;
        }
        .value {
            font-family: monospace;
            font-size: 1rem;
            color: #38bdf8;
        }
        button {
            width: 100%;
            padding: 0.65rem;
            background: #2563eb;
            color: #fff;
            border: none;
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: 500;
            cursor: pointer;
        }
        button:hover { background: #1d4ed8; }
    </style>
</head>
<body>
    <header class="topbar">
        Autores: <strong>Samuel Perdomo Camargo - Juan Miguel Fajardo Valencia</strong>
    </header>

    <div class="card">
        <div class="status"><span class="dot"></span> Activo</div>
        <h1>Hello from {{ server_name }}</h1>
        <div class="info-box">
            <div class="label">Contenedor</div>
            <div class="value">{{ hostname }}</div>
        </div>
        <button onclick="location.reload()">Recargar petición</button>
    </div>
</body>
</html>
"""
#-----------------------------------------------------------------#
app = Flask(__name__)

SERVER_NAME = os.getenv("SERVER_NAME", "sin-nombre")

# --- Monitoreo: expone /metrics en formato Prometheus ---------------------
# group_by="endpoint": agrupa por ruta de Flask (evita una serie por cada URL distinta)
# default_labels: etiqueta "backend" en todas las métricas, útil para las gráficas
# excluded_paths: no cuenta el healthcheck de Docker, que llega cada 5 s
metrics = PrometheusMetrics(
    app,
    group_by="endpoint",
    default_labels={"backend": SERVER_NAME},
    excluded_paths=["/health"],
)
metrics.info("app_info", "Información del backend", server=SERVER_NAME)


@app.route("/")
def index():
    return render_template_string(
        HTML_TEMPLATE,
        server_name=SERVER_NAME,
        hostname=socket.gethostname()
    )


@app.route("/health")
def health():
    return jsonify(status="ok", server=SERVER_NAME)


@app.route("/headers")
def headers():
    # Muestra qué cabeceras recibe realmente el backend (útil para ver X-Forwarded-For)
    return jsonify(
        server=SERVER_NAME,
        ip_que_ve_flask=request.remote_addr,
        cabeceras=dict(request.headers),
    )


@app.route("/slow")
def slow():
    # Simula trabajo pesado: /slow?ms=500 tarda 500 ms en responder
    ms = min(int(request.args.get("ms", 1000)), 30000)
    time.sleep(ms / 1000)
    return jsonify(server=SERVER_NAME, esperó_ms=ms)


@app.after_request
def marcar_backend(resp):
    resp.headers["X-Backend"] = SERVER_NAME
    return resp

