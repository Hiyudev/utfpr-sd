import functools
from threading import Thread, Lock
import uuid
import pika
import requests
from flask import Blueprint, Flask, request, jsonify, session
from flask_sse import sse
from flask_cors import CORS
from common.serial import deserialize_dict

app = Flask(__name__)
CORS(app)
app.secret_key = "DUTRA"
app.config["REDIS_URL"] = "redis://localhost"

sse_blueprint = Blueprint("sse_bp", __name__)
CORS(sse_blueprint)
sse_blueprint.register_blueprint(sse, url_prefix="/")

app.register_blueprint(sse_blueprint, url_prefix="/events")

global_ms_leilao_url = "http://127.0.0.1:8111/leilao"
global_ms_lance_url = "http://127.0.0.1:8100/lance"
global_interests: dict[str, list[str]] = {}
global_interests_mutex: Lock = None
EXCHANGE_NAME = "exchange"


@app.route("/", methods=["GET"])
def index():
    return str(uuid.uuid4()), 200


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

            return "Leilao criado com sucesso", 201
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

            return "Lance realizado", 201
        except requests.exceptions.RequestException as e:
            return f"Erro no lance: {e}", 500
    else:
        return "Method Not Allowed", 405


@app.route("/notificacoes/<leilao_id>", methods=["POST", "DELETE"])
def route_notificacoes(leilao_id: str):
    client_id = request.headers.get("Authorization", default="", type=str)

    if request.method == "POST":
        if len(client_id) == 0:
            return "Bad Request", 400

        global_interests_mutex.acquire()
        if client_id not in global_interests:
            global_interests[client_id] = []

        global_interests[client_id].append(leilao_id)
        global_interests_mutex.release()

        return "", 200
    elif request.method == "DELETE":
        if len(client_id) == 0:
            return "Bad Request", 400

        global_interests_mutex.acquire()
        if client_id not in global_interests:
            global_interests_mutex.release()
            return "Bad Request", 400

        if leilao_id not in global_interests[client_id]:
            global_interests_mutex.release()
            return "", 200

        global_interests[client_id].remove(leilao_id)
        global_interests_mutex.release()

        return "", 200
    else:
        return "Method Not Allowed", 405


def main_rabbitmq():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="localhost", heartbeat=0)
    )
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

        global_interests_mutex.acquire()

        event_leilao_id = ""
        targeted_user_id = ""

        if (
            method.routing_key == "lance_validado"
            or method.routing_key == "lance_invalidado"
        ):
            event_leilao_id = data["leilao_id"]
        elif (
            method.routing_key == "leilao_vencedor"
            or method.routing_key == "link_pagamento"
        ):
            event_leilao_id = data["leilao_id"]
        elif method.routing_key == "status_pagamento":
            targeted_user_id = data["client_id"]

        if len(event_leilao_id) > 0:
            for client_id, leiloes in global_interests.items():
                if event_leilao_id not in leiloes:
                    continue

                print("[API-Gateway] Enviado um evento SSE")

                with app.app_context():
                    print(f"notification_{client_id}")
                    payload = data.copy()
                    payload["event_name"] = method.routing_key
                    sse.publish(payload, type=f"notification_{client_id}")

        if len(targeted_user_id) > 0:
            print("[API-Gateway] Enviado um evento SSE")

            with app.app_context():
                print(f"notification_{targeted_user_id}")
                payload = data.copy()
                payload["event_name"] = method.routing_key
                sse.publish(payload, type=f"notification_{targeted_user_id}")

        global_interests_mutex.release()

        cb = functools.partial(ch.basic_ack, delivery_tag=method.delivery_tag)
        connection.add_callback_threadsafe(cb)

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


if __name__ == "gateway":
    global_interests_mutex = Lock()
    threads: list[Thread] = []

    threads.append(Thread(target=main_rabbitmq, daemon=True))

    for thread in threads:
        thread.start()
