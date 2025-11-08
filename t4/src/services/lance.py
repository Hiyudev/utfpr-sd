import pika
import base64
import json
import functools
import datetime
import sys
import os

# Adiciona o diretório raiz do projeto ao sys.path para importar 'common'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from common.serial import deserialize_dict, deserialize_leilao, serialize_dict

# Variáveis globais

leiloes: list[dict[str, str | datetime.datetime]] = []

EXCHANGE_NAME = "exchange"


def main():
    # Realiza a conexao com o RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="direct")

    # Cria uma fila com nome aleatória
    result = channel.queue_declare(queue="", exclusive=True)
    queue_name = result.method.queue

    # Conecta a fila criada com o exchange, aceitando apenas mensagens com o identificador "lance_realizado", "leilao_iniciado" e "leilao_finalizado"
    # Requisito 4.2 - Escuta os eventos das filas lance_realizado, leilao_iniciado e leilao_finalizado.
    channel.queue_bind(
        exchange=EXCHANGE_NAME, queue=queue_name, routing_key="lance_realizado"
    )
    channel.queue_bind(
        exchange=EXCHANGE_NAME, queue=queue_name, routing_key="leilao_iniciado"
    )
    channel.queue_bind(
        exchange=EXCHANGE_NAME, queue=queue_name, routing_key="leilao_finalizado"
    )

    # Requisito 4.3 - Recebe lances de usuários (ID do leilão; ID do usuário, valor do lance) e checa a assinatura digital da mensagem utilizando a
    # chave pública correspondente. Somente aceitará o lance se: A assinatura for válida

    def on_message(ch, method, properties, body):
        if method.routing_key == "lance_realizado":
            lance = deserialize_dict(body)

            # checa se id do leilao existe em leiloes
            if any(lance["leilao_id"] in d["id"] for d in leiloes):
                print("[MS-Lance] leilao existe!")
                # checa se eh maior lance
                lance_vencedor = [
                    d.get("highest_bid")
                    for d in leiloes
                    if lance["leilao_id"] in d["id"]
                ]
                if int(lance["value"]) > int(lance_vencedor[0]):
                    # Requisito 4.4 - Se o lance for válido, o MS Lance publica o evento na fila lance_validado.
                    [
                        d.update(highest_bid=lance["value"])
                        for d in leiloes
                        if lance["leilao_id"] in d["id"]
                    ]
                    [
                        d.update(winner=lance["user_id"])
                        for d in leiloes
                        if lance["leilao_id"] in d["id"]
                    ]
                    channel.basic_publish(
                        exchange=EXCHANGE_NAME,
                        body=body,
                        routing_key="lance_validado",
                    )
                    print("[MS-Lance] Lance validado!")
                else:
                    channel.basic_publish(
                        exchange=EXCHANGE_NAME,
                        body=body,
                        routing_key="lance_invalidado",
                    )
                    print("[MS-Lance] Lance invalidado!")
            else:
                print("[MS-Lance] leilao nao existe!")

        if method.routing_key == "leilao_iniciado":
            # Somente aceitará o lance se: ID do leilão existir e se o leilão estiver ativo;
            leilao = deserialize_leilao(body)
            leilao["highest_bid"] = "0"
            leilao["winner"] = "ninguem"
            leiloes.append(leilao)

        if method.routing_key == "leilao_finalizado":
            # Requisito 4.5 - Ao finalizar um leilão, deve publicar na fila leilao_vencedor,
            # informando o ID do leilão, o ID do vencedor do leilão e o valor
            # negociado. O vencedor é o que efetuou o maior lance válido até o
            # encerramento.

            print("pacote recebido: ", body)
            leilao_id = body.decode("utf-8")
            print("leilao id: ", leilao_id)

            lance_vencedor = next(
                (d.get("highest_bid") for d in leiloes if leilao_id in d["id"]), None
            )

            cliente_vencedor = next(
                (d.get("winner") for d in leiloes if leilao_id in d["id"]), None
            )

            message = serialize_dict(
                {
                    "leilao_id": leilao_id,
                    "lance_vencedor": lance_vencedor,
                    "cliente_vencedor": cliente_vencedor,
                }
            )

            # Remove o leilão finalizado da lista de leilões ativos
            leiloes.remove(next(d for d in leiloes if leilao_id in d["id"]))

            cb = functools.partial(ch.basic_ack, delivery_tag=method.delivery_tag)
            connection.add_callback_threadsafe(cb)

            channel.basic_publish(
                exchange=EXCHANGE_NAME, body=message, routing_key="leilao_vencedor"
            )

    channel.basic_consume(
        queue=queue_name, on_message_callback=on_message, auto_ack=False
    )

    print("[MS-Lance] Waiting for messages. To exit press CTRL+C")

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("[MS-Lance] Exiting...")
        connection.close()

    if connection.is_open:
        connection.close()

    return 1


if __name__ == "__main__":
    main()
