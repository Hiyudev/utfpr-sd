import pika
import datetime
import uuid
from faker import Faker

import sys
import os

# Adiciona o diretório raiz do projeto ao sys.path para importar 'common'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from common.serial import serialize_leilao

# Variáveis globais
LEILOES = 3
EXCHANGE_NAME = "exchange"


def generate_random_leilao():
    fake = Faker()
    random_id = str(uuid.uuid4().hex)
    random_description = fake.sentence(5)
    random_start: datetime.datetime = fake.future_datetime(
        end_date=datetime.timedelta(seconds=30)
    )
    random_end: datetime.datetime = random_start + datetime.timedelta(seconds=20)

    return {
        "id": random_id,
        "description": random_description,
        "start": random_start,
        "end": random_end,
    }


def main():
    # Inicializa a lista de leiloes
    leiloes: list[dict[str, any]] = []
    for _ in range(LEILOES):
        leiloes.append(generate_random_leilao())

    # Realiza a conexao com o RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="direct")

    # Elabora uma lista das datas de inicio e fim
    starts: list[datetime.datetime] = [leilao["start"] for leilao in leiloes]
    ends: list[datetime.datetime] = [leilao["end"] for leilao in leiloes]

    sorted_starts: list[tuple[int, datetime.datetime]] = sorted(
        enumerate(starts), key=lambda i: i[1]
    )
    sorted_ends: list[tuple[int, datetime.datetime]] = sorted(
        enumerate(ends), key=lambda i: i[1]
    )

    try:
        while True:
            now = datetime.datetime.now()

            has_elements_in_starts = len(sorted_starts) > 0
            has_elements_in_ends = len(sorted_ends) > 0

            # Verifica se há algum leilão pendente ou, em andamento
            if not has_elements_in_starts and not has_elements_in_ends:
                break

            if has_elements_in_starts:
                already_passed_start = sorted_starts[0][1] < now
                start_element: dict[str, any] = leiloes[sorted_starts[0][0]]

                if already_passed_start:
                    message = serialize_leilao(start_element)

                    channel.basic_publish(
                        exchange=EXCHANGE_NAME,
                        routing_key="leilao_iniciado",
                        body=message,
                    )
                    sorted_starts.pop(0)

                    print(
                        f"[MS-Leilao] Leilao com o id {start_element['id']} foi iniciado."
                    )

            if has_elements_in_ends:
                already_passed_end = sorted_ends[0][1] < now
                end_element: str = leiloes[sorted_ends[0][0]]["id"]

                if already_passed_end:
                    message = end_element.encode("utf-8")

                    channel.basic_publish(
                        exchange=EXCHANGE_NAME,
                        routing_key="leilao_finalizado",
                        body=message,
                    )
                    sorted_ends.pop(0)

                    print(f"[MS-Leilao] Leilao com o id {end_element} foi finalizado.")
    except Exception as e:
        print("Expection: ", e)

    connection.close()


if __name__ == "__main__":
    main()
