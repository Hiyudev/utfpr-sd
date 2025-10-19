import pika
import json
import base64
import datetime
import functools
import uuid
import os
import sys

from pika.adapters.blocking_connection import BlockingChannel
from simple_term_menu import TerminalMenu
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes

# Adiciona o diretório raiz do projeto ao sys.path para importar 'common'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from common.serial import deserialize_leilao, deserialize_dict, serialize_dict

# Variáveis globais
EXCHANGE_NAME = "exchange"
ID_SUMMARY_LENGTH = 8


def publisher(
    user_id: str, leilao: dict, channel: BlockingChannel, private_key: rsa.RSAPrivateKey
):
    value = input("[Cliente] Digite o valor do lance: ")
    message = serialize_dict(
        {"user_id": user_id, "leilao_id": leilao["id"], "value": value}
    )

    print(
        f"[Cliente] Você deu um lance de {value} no leilão {leilao['id'][:ID_SUMMARY_LENGTH]}"
    )

    # Requisito 2.3 - O cliente assina digitalmente cada lance com sua chave privada.
    signature = private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )
    encoded_signature = base64.b64encode(signature).decode("utf-8")

    # Requisito 2.3 - Cada lance contém: ID do leilão, ID do usuário, valor do lance.
    message = deserialize_dict(message)
    message["signature"] = encoded_signature
    message = serialize_dict(message)

    # Requisito 2.3 - Publica lances na fila de mensagens lance_realizado.
    print(
        f"[Log] Foi enviado uma mensagem para \"lance_realizado\" para o leilão {leilao['id'][:ID_SUMMARY_LENGTH]}"
    )
    channel.basic_publish(
        exchange=EXCHANGE_NAME, routing_key="lance_realizado", body=message
    )

    return 1


def consumer(channel, queue_name, connection, user_id, private_key: rsa.RSAPrivateKey):
    def on_message(ch, method, properties, body):
        if method.routing_key == "leilao_iniciado":
            leilao = deserialize_leilao(body)

            answer = input(
                f"[Cliente] O leilao {leilao['id'][:ID_SUMMARY_LENGTH]} foi iniciado! Deseja realizar um lance?"
            )

            if answer.lower() in ["s", "sim", "y", "yes"]:
                publisher(user_id, leilao, channel, private_key)

                # Requisito 2.4 - Ao dar um lance em um leilão, o cliente atuará como consumidor desse leilão
                channel.queue_bind(
                    exchange=EXCHANGE_NAME,
                    queue=queue_name,
                    routing_key=f"leilao_{leilao['id']}",
                )
        elif method.routing_key.startswith("leilao_"):
            message = deserialize_dict(body)
            assert "type" in message, "Key 'type' does not exist in the dictionary."

            type = message["type"]

            if type == "lance_validado":
                assert message["user_id"]
                assert message["leilao_id"]
                assert message["value"]

                if message["user_id"] == user_id:
                    log = f"[Log] Seu lance de {message['value']} no leilão {message['leilao_id'][:ID_SUMMARY_LENGTH]} foi validado."
                else:
                    log = f"[Log] O usuário {message['user_id'][:ID_SUMMARY_LENGTH]} deu um lance de {message['value']} no leilão {message['leilao_id'][:ID_SUMMARY_LENGTH]} que foi validado."

                print(log)

                if message["user_id"] != user_id:
                    answer = input(
                        f"[Cliente] Deseja dar um lance maior que {message['value']} no leilão {message['leilao_id'][:ID_SUMMARY_LENGTH]}? "
                    )

                    if answer.lower() in ["s", "sim", "y", "yes"]:
                        leilao = {"id": message["leilao_id"]}
                        publisher(user_id, leilao, channel, private_key)
            elif type == "leilao_vencedor":
                assert message["leilao_id"]
                assert message["lance_vencedor"]
                assert message["cliente_vencedor"]

                if message["cliente_vencedor"] == user_id:
                    log = f"[Log] Parabéns! Você venceu o leilão {message['leilao_id'][:ID_SUMMARY_LENGTH]} com um lance de {message['lance_vencedor']}."
                else:
                    log = f"[Log] Leilão {message['leilao_id'][:ID_SUMMARY_LENGTH]} finalizado. O vencedor foi o usuário {message['cliente_vencedor'][:ID_SUMMARY_LENGTH]} com um lance de {message['lance_vencedor']}."

                print(log)
            else:
                print(f"[Warning] Tipo de mensagem desconhecido: {type}")

        cb = functools.partial(ch.basic_ack, delivery_tag=method.delivery_tag)
        connection.add_callback_threadsafe(cb)

    channel.basic_consume(
        queue=queue_name, on_message_callback=on_message, auto_ack=False
    )

    print(" [Client] Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()


def main():
    user_id = random_id = str(uuid.uuid4().hex)
    print(f"[Client] Seu ID de usuário é {user_id[:ID_SUMMARY_LENGTH]}")

    # Inicializa o par de chaves
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()

    # Salva a chave pública
    # Verifica se o diretório existe
    if not os.path.isdir("./keys"):
        os.makedirs("./keys")

    with open(f"./keys/{user_id}.pem", "wb") as f:
        f.write(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )

    # Realiza a conexao com o RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="direct")

    # Cria uma fila com nome aleatória
    result = channel.queue_declare(queue="", exclusive=True)
    queue_name = result.method.queue

    # Conecta a fila criada com o exchange, aceitando apenas mensagens com o identificador "leilao_iniciado"
    # Requisito 2.2 - Logo ao inicializar, atuará como consumidor recebendo eventos da fila leilao_iniciado.
    channel.queue_bind(
        exchange=EXCHANGE_NAME, queue=queue_name, routing_key="leilao_iniciado"
    )

    try:
        consumer(
            channel,
            queue_name,
            connection,
            user_id,
            private_key,
        )
    except KeyboardInterrupt:
        print("[Client] Exiting...")
        connection.close()

    if connection.is_open:
        connection.close()
        
    return 1


if __name__ == "__main__":
    main()
