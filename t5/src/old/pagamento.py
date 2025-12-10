import functools
import os
import sys
import requests
from threading import Thread, Lock
from time import sleep
from flask import Flask, request, jsonify
import pika
from pika.adapters.blocking_connection import BlockingChannel

# Adiciona o diretório raiz do projeto ao sys.path para importar 'common'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from common.serial import deserialize_dict, serialize_dict

app = Flask(__name__)

# Variáveis globais
global_exchange_name = "exchange"
global_externo_url = "http://127.0.0.1:5555/transaction"
global_transactions_mutex = None
global_transactions: list[dict[str, any]] = []


@app.route("/webhook", methods=["POST"])
def receive_webhook():
    if request.method == "POST":
        try:
            data = request.json

            assert "value" in data
            assert "status" in data
            assert "transaction_id" in data
            assert "client_id" in data

            global_transactions_mutex.acquire()
            global_transactions.append(data)
            global_transactions_mutex.release()

            print("[MS-Pagamento] Webhook recebido.")

            return jsonify("Webhook received successfully"), 200
        except Exception as e:
            return str(e), 400
    else:
        return jsonify("Method Not Allowed"), 405


def main_rabbitmq_transactions(channel: BlockingChannel, channel_mutex: Lock):
    try:
        while True:
            sleep(0.2)  # Dorme por 200ms

            global_transactions_mutex.acquire()

            if len(global_transactions) == 0:
                global_transactions_mutex.release()
                continue

            for transaction in global_transactions:
                print("[MS-Pagamento] Enviado uma mensagem para 'status_pagamento'.")

                payload = serialize_dict(transaction)

                channel_mutex.acquire()
                channel.basic_publish(
                    exchange=global_exchange_name,
                    routing_key="status_pagamento",
                    body=payload,
                )
                channel_mutex.release()

            global_transactions.clear()
            global_transactions_mutex.release()

    except KeyboardInterrupt:
        print("[MS-Pagamento] Exiting...")


def main_rabbitmq_consume(
    connection: pika.BlockingConnection, channel: BlockingChannel, channel_mutex: Lock
):
    def on_message(ch, method, properties, body):
        data = deserialize_dict(body)

        assert "leilao_id" in data
        assert "lance_vencedor" in data
        assert "cliente_vencedor" in data

        payload = {
            "value": data["lance_vencedor"],
            "client_id": data["cliente_vencedor"],
        }

        try:
            response = requests.post(global_externo_url, json=payload)
            response.raise_for_status()

            link = response.text.replace("\n", "")

            print("[MS-Pagamento] Um link de pagamento foi criado.")

            body = data.copy()
            body["link"] = link
            body = serialize_dict(body)

            channel.basic_publish(
                exchange=global_exchange_name,
                routing_key="link_pagamento",
                body=body,
            )

            print("[MS-Pagamento] Enviado uma mensagem para 'link_pagamento'.")
        except requests.exceptions.RequestException as e:
            print("[MS-Pagamento] Algum problema no MS-Externo foi encontrado.", e)

        cb = functools.partial(ch.basic_ack, delivery_tag=method.delivery_tag)
        connection.add_callback_threadsafe(cb)

    channel.basic_consume(
        queue=queue_name, on_message_callback=on_message, auto_ack=False
    )

    print("[MS-Pagamento] Waiting for messages. To exit press CTRL+C")

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("[MS-Pagamento] Exiting...")

    return 1


def main_flask():
    app.run(port=5000)
    return 1


if __name__ == "__main__":
    global_transactions_mutex = Lock()
    threads: list[Thread] = []

    connection_transactions = pika.BlockingConnection(
        pika.ConnectionParameters("localhost", heartbeat=0)
    )
    channel_transactions = connection_transactions.channel()
    channel_transactions.exchange_declare(
        exchange=global_exchange_name, exchange_type="direct"
    )

    # Cria uma fila com nome aleatória
    result_transactions = channel_transactions.queue_declare(queue="", exclusive=True)
    queue_name_transactions = result_transactions.method.queue

    channel_transactions.queue_bind(
        exchange=global_exchange_name,
        queue=queue_name_transactions,
        routing_key="status_pagamento",
    )

    connection_consume = pika.BlockingConnection(
        pika.ConnectionParameters("localhost", heartbeat=0)
    )
    channel_consume = connection_consume.channel()
    channel_consume.exchange_declare(
        exchange=global_exchange_name, exchange_type="direct"
    )

    # Cria uma fila com nome aleatória
    result = channel_consume.queue_declare(queue="", exclusive=True)
    queue_name = result.method.queue

    channel_consume.queue_bind(
        exchange=global_exchange_name, queue=queue_name, routing_key="leilao_vencedor"
    )

    channel_mutex = Lock()

    threads.append(
        Thread(
            target=main_rabbitmq_transactions,
            daemon=True,
            args=(
                channel_transactions,
                channel_mutex,
            ),
        )
    )
    threads.append(
        Thread(
            target=main_rabbitmq_consume,
            daemon=True,
            args=(connection_consume, channel_consume, channel_mutex),
        )
    )

    for thread in threads:
        thread.start()

    main_flask()
