import pika
import datetime
import uuid
import sys
import os
from time import sleep
from threading import Thread, Lock
from flask import Flask, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger

app = Flask(__name__)
scheduler = BackgroundScheduler()

# Adiciona o diretório raiz do projeto ao sys.path para importar 'common'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from common.serial import serialize_leilao

# Variáveis globais
LEILOES = 3
EXCHANGE_NAME = "exchange"
ID_SUMMARY_LENGTH = 8
leiloes: list[dict[str, any]] = []
leiloes_mutex = None
start_leiloes: list[dict[str, any]] = []
start_leiloes_mutex: Lock = None
end_leiloes: list[dict[str, any]] = []
end_leiloes_mutex: Lock = None


def trigger_start(payload: dict[str, any]):
    start_leiloes_mutex.acquire()
    start_leiloes.append(payload)
    start_leiloes_mutex.release()


def trigger_end(payload: dict[str, any]):
    end_leiloes_mutex.acquire()
    end_leiloes.append(payload)
    end_leiloes_mutex.release()


@app.route("/leilao", methods=["GET", "POST"])
def route_leilao():
    method = request.method

    if method == "GET":
        leiloes_mutex.acquire()
        data: list[dict[str, any]] = []

        for leilao in leiloes:
            assert "id" in leilao
            assert "name" in leilao
            assert "description" in leilao
            assert "value" in leilao
            assert "start" in leilao
            assert "end" in leilao

            assert isinstance(leilao["id"], str)
            assert isinstance(leilao["name"], str)
            assert isinstance(leilao["description"], str)
            assert isinstance(leilao["value"], float)
            assert isinstance(leilao["start"], datetime.datetime)
            assert isinstance(leilao["end"], datetime.datetime)

            data.append(
                {
                    "id": leilao["id"],
                    "name": leilao["name"],
                    "description": leilao["description"],
                    "value": str(leilao["value"]),
                    "start": str(leilao["start"].timestamp()),
                    "end": str(leilao["end"].timestamp()),
                }
            )
        leiloes_mutex.release()

        response = jsonify(data)
        return response, 200
    elif method == "POST":
        data = request.get_json()

        assert "name" in data
        assert "description" in data
        assert "value" in data
        assert "start" in data
        assert "end" in data

        assert isinstance(data["name"], str)
        assert isinstance(data["description"], str)
        assert isinstance(data["value"], str)
        assert isinstance(data["start"], str)
        assert isinstance(data["end"], str)

        value_float = float(data["value"])
        start_datetime = datetime.datetime.fromtimestamp(float(data["start"]))
        end_datetime = datetime.datetime.fromtimestamp(float(data["end"]))
        data["start"] = start_datetime
        data["end"] = end_datetime
        data["value"] = value_float
        data["id"] = str(uuid.uuid4())

        leiloes_mutex.acquire()
        leiloes.append(data)

        start_scheduler_trigger = DateTrigger(run_date=start_datetime)
        end_scheduler_trigger = DateTrigger(run_date=end_datetime)
        scheduler.add_job(trigger_start, args=(data), trigger=start_scheduler_trigger)
        scheduler.add_job(trigger_end, args=(data), trigger=end_scheduler_trigger)

        leiloes_mutex.release()

        return "", 204

    return jsonify("Comando inválido."), 400


def main_rabbitmq():
    # Requisito 3.1 - Mantém internamente uma lista pré-configurada (hardcoded) de leilões com: ID do leilão, descrição, data e hora de início e fim, status (ativo, encerrado).
    # Realiza a conexao com o RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="direct")

    result = channel.queue_declare(queue="", exclusive=True)
    queue_name = result.method.queue

    # Conecta a fila criada com o exchange, aceitando apenas mensagens com o identificador "lance_validado" e "leilao_vencedor"
    # Requisito 5.1 - Escuta os eventos das filas lance_validado e leilao_vencedor.
    channel.queue_bind(
        exchange=EXCHANGE_NAME, queue=queue_name, routing_key="leilao_iniciado"
    )
    channel.queue_bind(
        exchange=EXCHANGE_NAME, queue=queue_name, routing_key="leilao_finalizado"
    )

    try:
        while True:
            sleep(0.2)  # Dorme por 200ms

            # Evita problemas com threads
            start_leiloes_mutex.acquire()
            end_leiloes_mutex.acquire()

            has_elements_in_starts = len(start_leiloes) > 0
            has_elements_in_ends = len(end_leiloes) > 0

            if has_elements_in_starts:
                for start_leilao in start_leiloes:
                    message = serialize_leilao(start_leilao)

                    channel.basic_publish(
                        exchange=EXCHANGE_NAME,
                        routing_key="leilao_iniciado",
                        body=message,
                    )

                    print(
                        f"[MS-Leilao] Leilao com o id {start_leilao['id'][:ID_SUMMARY_LENGTH]} foi iniciado."
                    )

            if has_elements_in_ends:
                for end_leilao in end_leiloes:
                    message = end_leilao["id"].encode("utf-8")

                    channel.basic_publish(
                        exchange=EXCHANGE_NAME,
                        routing_key="leilao_finalizado",
                        body=message,
                    )

                    print(
                        f"[MS-Leilao] Leilao com o id {message[:ID_SUMMARY_LENGTH]} foi finalizado."
                    )

            start_leiloes.clear()
            end_leiloes.clear()

            start_leiloes_mutex.release()
            end_leiloes_mutex.release()
    except KeyboardInterrupt:
        print("[MS-Leilao] Exiting...")
        connection.close()

    if connection.is_open:
        connection.close()

    return 1


def main_flask():
    app.run(port=8000)

    return 1


if __name__ == "__main__":
    scheduler.start()
    leiloes_mutex = Lock()
    threads: list[Thread] = []

    threads.append(Thread(target=main_rabbitmq, daemon=True))

    for thread in threads:
        thread.start()

    main_flask()
