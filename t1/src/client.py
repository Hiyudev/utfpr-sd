import pika
import json
import base64
import datetime
import functools
import uuid
import os
import sys

from simple_term_menu import TerminalMenu
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from threading import Thread, Lock

# Adiciona o diretório raiz do projeto ao sys.path para importar 'common'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from common.serial import deserialize_leilao, deserialize_dict, serialize_dict

lock = Lock()

# Variáveis globais
leiloes: list[dict[str, str | datetime.datetime]] = []
logs: list[str] = []

EXCHANGE_NAME = "exchange"


def consume_worker(lock: Lock, channel, queue_name, connection):
    def on_message(ch, method, properties, body):
        if method.routing_key == "leilao_iniciado":
            leilao = deserialize_leilao(body)

            lock.acquire()
            leiloes.append(leilao)
            logs.append(f"[info] Leilão com o id {leilao['id']} foi iniciado")
            lock.release()

        lock.acquire()
        logs.append(
            f"[debug] Mensagem recebida com a routing key {method.routing_key} foi: {body}"
        )
        lock.release()
        cb = functools.partial(ch.basic_ack, delivery_tag=method.delivery_tag)
        #ch.basic_ack(delivery_tag=method.delivery_tag)
        connection.add_callback_threadsafe(cb)

    channel.basic_consume(queue=queue_name, on_message_callback=on_message)

    channel.start_consuming()


def show_submenu(lock: Lock, channel, user_id, private_key, queue_name):
    if len(leiloes) == 0:
        print("Nenhum leilão disponível no momento.")
        return

    options = [l["id"] for l in leiloes]
    terminal_menu = TerminalMenu(options)
    menu_entry_index = terminal_menu.show()
    leilao: dict[str, str | datetime.datetime] = leiloes[menu_entry_index]

    value = input("Digite o valor do lance: ")
    
    b_value = value.encode('utf-8')

    message = json.dumps(
    {"user_id": user_id, "leilao_id": leilao["id"], "value": value}
    ).encode("utf-8")


    print(f"Você deu um lance de {value} no leilão {leilao['id']}")
    
    # Requisito 2.3 - O cliente assina digitalmente cada lance com sua chave privada.
    signature = private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )
    encoded_signature = base64.b64encode(signature).decode('utf-8')
        # Requisito 2.3 - Cada lance contém: ID do leilão, ID do usuário, valor do lance.
    message = deserialize_dict(message)
    message['signature'] = encoded_signature
    message = serialize_dict(message)

    #message = json.dumps(
    #    {"user_id": user_id, "leilao_id": leilao["id"], "value": value, "signature": encoded_signature}
    #).encode("utf-8")

    # Requisito 2.3 - Publica lances na fila de mensagens lance_realizado.
    channel.basic_publish(
        exchange=EXCHANGE_NAME, routing_key="lance_realizado", body=message
    )

    # Requisito 2.4 - Ao dar um lance em um leilão, o cliente atuará como consumidor desse leilão
    channel.queue_bind(
        exchange=EXCHANGE_NAME,
        queue=queue_name,
        routing_key=f"leilao_{leilao['id']}",
    )


def show_mainmenu(lock: Lock, channel, user_id, private_key, queue_name):
    while True:
        options = ["Listar leilões", "Lançar um lance", "Verificar logs", None, "Sair"]
        terminal_menu = TerminalMenu(options, skip_empty_entries=True)
        menu_entry_index = terminal_menu.show()

        if menu_entry_index == 0:
            lock.acquire()
            for leilao in leiloes:
                print(
                    f"ID: {leilao['id']}, Description: {leilao['description']}, Início: {leilao['start']}, Fim: {leilao['end']}"
                )
            lock.release()
        elif menu_entry_index == 1:
            show_submenu(lock, channel, user_id, private_key, queue_name)
        elif menu_entry_index == 2:
            lock.acquire()
            for log in logs:
                print(log)
            lock.release()
        else:
            break


def main():
    user_id = random_id = str(uuid.uuid4().hex)

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

    consume_thread = Thread(
        target=consume_worker,
        args=(
            lock,
            channel,
            queue_name,
            connection,
        ),
        daemon=True,
    )

    try:
        consume_thread.start()

        show_mainmenu(
            lock,
            channel,
            user_id,
            private_key,
            queue_name,
        )

        consume_thread.join()
    except Exception as e:
        print("Exception: ", e)


if __name__ == "__main__":
    main()
