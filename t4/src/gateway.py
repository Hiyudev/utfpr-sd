from threading import Thread
import uuid
import pika
import requests
from flask import Flask, request, jsonify, session
from flask_sse import sse

from common.serial import deserialize_dict

app = Flask(__name__)
app.config["REDIS_URL"] = "redis://localhost"
app.register_blueprint(sse, url_prefix="/events")

global_ms_leilao_url = "http://127.0.0.1:8000/leilao"
global_ms_lance_url = "http://127.0.0.1:8100/lance"
global_interests: dict[str, list[str]] = {}
EXCHANGE_NAME = "exchange"


@app.route("/", methods=["GET"])
def index():
    if "client_id" not in session:
        session["client_id"] = str(uuid.uuid4())  # Generate a new unique ID
    return session["client_id"], 200


@app.route("/leilao", methods=["GET", "POST"])
def route_leilao():
    # Requisito 3.1.2
    if request.method == "GET":
        try:
            response = requests.get(global_ms_leilao_url)
            response.raise_for_status()

            return jsonify(response.json()), 200
        except requests.exceptions.RequestException as e:
            return f"Erro na consulta dos leilões", 500
    # Requisito 3.1.1
    elif request.method == "POST":
        try:
            body = request.get_json()

            assert "name" in body
            assert "description" in body
            assert "value" in body
            assert "start" in body
            assert "end" in body

            response = requests.post(global_ms_leilao_url, json=body)
            response.raise_for_status()

            return "Leilao criado com sucesso", 200
        except requests.exceptions.RequestException as e:
            return f"Erro na criação do leilao: {e}", 500
    else:
        return "Method Not Allowed", 405


@app.route("/lance", methods=["POST"])
def route_lance():
    if request.method == "POST":
        try:
            body = request.get_json()

            assert "leilao_id" in body
            assert "user_id" in body
            assert "value" in body

            response = requests.post(global_ms_lance_url, json=body)
            response.raise_for_status()

            return "Lance realizado", 200
        except requests.exceptions.RequestException as e:
            return f"Erro no lance: {e}", 500
    else:
        return "Method Not Allowed", 405


@app.route("/notificacoes/<uuid:leilao_id>", methods=["POST", "DELETE"])
def route_notificacoes(leilao_id: str):
    if request.method == "POST":
        if "client_id" not in session:
            return "Bad Request", 400

        client_id = session["client_id"]

        if client_id not in global_interests:
            global_interests[client_id] = []

        global_interests[client_id].append(leilao_id)
    elif request.method == "DELETE":
        if "client_id" not in session:
            return "Bad Request", 400

        client_id = session["client_id"]

        if client_id not in global_interests:
            return "Bad Request", 400

        global_interests[client_id].remove(leilao_id)
    else:
        return "Method Not Allowed", 405


def main_rabbitmq():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="direct")

    # Cria uma fila com nome aleatória
    result = channel.queue_declare(queue="", exclusive=True)
    queue_name = result.method.queue

    routing_keys = [
        "lance_validado",
        "lance_invalidado",
        "leilao_vencedor",
        "link_pagamento",
        "status_pagamento",
    ]
    for routing_key in routing_keys:
        channel.queue_bind(
            exchange=EXCHANGE_NAME, queue=queue_name, routing_key=routing_key
        )

    def on_message(ch, method, properties, body):
        data = deserialize_dict(body)
        
        client_id = ""
        
        if method.routing_key == "lance_validado" or method.routing_key == "lance_invalidado":
            client_id = data["user_id"]
        elif method.routing_key == "leilao_vencedor" or method.routing_key == "link_pagamento":
            client_id = data["cliente_vencedor"]
        elif method.routing_key == "status_pagamento":
            client_id = data["client_id"]
        
        sse.publish(data, type=f"notification_{client_id}")

    channel.basic_consume(
        queue=queue_name, on_message_callback=on_message, auto_ack=False
    )

    print("[API-Gateway] Waiting for messages. To exit press CTRL+C")

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("[API-Gateway] Exiting...")
        connection.close()

    if connection.is_open:
        connection.close()

    return 1


def main_flask():
    app.run(port=8888, threaded=False)

    return 1


if __name__ == "__main__":
    threads: list[Thread] = []

    threads.append(Thread(target=main_rabbitmq, daemon=True))

    for thread in threads:
        thread.start()

    main_flask()
