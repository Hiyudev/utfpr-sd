import pika
import sys
import os

# Adiciona o diretório raiz do projeto ao sys.path para importar 'common'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from common.serial import serialize_leilao

# Variáveis globais
EXCHANGE_NAME = "exchange"


def main():
    # Realiza a conexao com o RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="direct")

    # Cria uma fila com nome aleatória
    result = channel.queue_declare(queue="", exclusive=True)
    queue_name = result.method.queue

    # Conecta a fila criada com o exchange, aceitando apenas mensagens com o identificador "lance_validado" e "leilao_vencedor"
    # Requisito 5.1 - Escuta os eventos das filas lance_validado e leilao_vencedor.
    channel.queue_bind(
        exchange=EXCHANGE_NAME, queue=queue_name, routing_key="lance_validado"
    )
    channel.queue_bind(
        exchange=EXCHANGE_NAME, queue=queue_name, routing_key="leilao_vencedor"
    )

    # Requisito 5.2 - Publica esses eventos nas filas específicas para cada leilão, de acordo com o seu ID (leilao_1, leilao_2, ...), de modo que somente os consumidores interessados nesses leilões recebam as notificações correspondentes.
    def on_message(ch, method, properties, body):
        if method.routing_key == "lance_validado":
            # TODO
            pass
        elif method.routing_key == "leilao_vencedor":
            # TODO
            pass

        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue=queue_name, on_message_callback=on_message, auto_ack=True
    )

    channel.start_consuming()


if __name__ == "__main__":
    main()
