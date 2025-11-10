import pika
import datetime
import uuid
import sys
import os
from time import sleep
from threading import Thread, Lock

from faker import Faker
from flask import Flask, jsonify, request

app = Flask(__name__)

# Adiciona o diretório raiz do projeto ao sys.path para importar 'common'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from common.serial import serialize_leilao

# Variáveis globais
LEILOES = 3
EXCHANGE_NAME = "exchange"
ID_SUMMARY_LENGTH = 8
leiloes: list[dict[str, any]] = []
leiloes_mutex = None


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

        assert "id" in data
        assert "name" in data
        assert "description" in data
        assert "value" in data
        assert "start" in data
        assert "end" in data

        assert isinstance(data["id"], str)
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

        leiloes_mutex.acquire()
        leiloes.append(data)
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

    already_started: list[str] = []
    already_ended: list[str] = []

    # TODO: REFORMULAR PARA UTILIZAR ADVANCED PYTHON SCHEDULER

    try:
        while True:
            sleep(0.2)  # Dorme por 200ms

            # Evita problemas com threads
            leiloes_mutex.acquire()

            # Elabora uma lista das datas de inicio e fim
            starts: list[datetime.datetime] = [leilao["start"] for leilao in leiloes]
            ends: list[datetime.datetime] = [leilao["end"] for leilao in leiloes]

            sorted_starts: list[tuple[int, datetime.datetime]] = sorted(
                enumerate(starts), key=lambda i: i[1]
            )
            sorted_ends: list[tuple[int, datetime.datetime]] = sorted(
                enumerate(ends), key=lambda i: i[1]
            )

            now = datetime.datetime.now()

            has_elements_in_starts = len(sorted_starts) > 0
            has_elements_in_ends = len(sorted_ends) > 0

            if has_elements_in_starts:
                already_passed_start = sorted_starts[0][1] < now
                start_element: dict[str, any] = leiloes[sorted_starts[0][0]]

                if already_passed_start and start_element["id"] not in already_started:
                    message = serialize_leilao(start_element)

                    # Requisito 3.2 - O leilão de um determinado produto deve ser iniciado quando o tempo definido para esse leilão for atingido. Quando um leilão começa, ele publica o evento na fila: leilao_iniciado.
                    channel.basic_publish(
                        exchange=EXCHANGE_NAME,
                        routing_key="leilao_iniciado",
                        body=message,
                    )
                    already_started.append(start_element["id"])

                    print(
                        f"[MS-Leilao] Leilao com o id {start_element['id'][:ID_SUMMARY_LENGTH]} foi iniciado."
                    )

            if has_elements_in_ends:
                already_passed_end = sorted_ends[0][1] < now
                end_element: str = leiloes[sorted_ends[0][0]]["id"]

                if already_passed_end and end_element not in already_ended:
                    message = end_element.encode("utf-8")

                    # Requisito 3.3 - O leilão de um determinado produto deve ser finalizado quando o tempo definido para esse leilão expirar. Quando um leilão termina, ele publica o evento na fila: leilao_finalizado.
                    channel.basic_publish(
                        exchange=EXCHANGE_NAME,
                        routing_key="leilao_finalizado",
                        body=message,
                    )
                    already_ended.append(end_element)

                    print(
                        f"[MS-Leilao] Leilao com o id {end_element[:ID_SUMMARY_LENGTH]} foi finalizado."
                    )

            # Libera o lock
            leiloes_mutex.release()
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
    leiloes_mutex = Lock()
    threads: list[Thread] = []

    threads.append(Thread(target=main_rabbitmq, daemon=True))

    for thread in threads:
        thread.start()

    main_flask()
