import pika
import base64
import sys
import os

from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes

# Adiciona o diretório raiz do projeto ao sys.path para importar 'common'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from common.serial import deserialize_dict

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

    #Requisito 4.3 - Recebe lances de usuários (ID do leilão; ID do usuário, valor do lance) e checa a assinatura digital da mensagem utilizando a
    #chave pública correspondente. Somente aceitará o lance se: A assinatura for válida

    def on_message(ch, method, properties, body):
        if method.routing_key == "lance_realizado":
            lance = deserialize_dict(body)
            print("lance recebido: ", lance)

            #necessario converter a assinatura e valor para bytes pra permitir o processo de verificacao
            b_signature = base64.b64decode(lance['signature'])
            b_value = lance['value'].encode('utf-8')

            #esses blocos try catch estavam mais para encontrar os erros que estavam aparecendo, se achar feio pode retirar

            #Requisito 4.1 - Possui as chaves públicas de todos os clientes.
            try:
                with open(f"./keys/{lance['user_id']}.pem", "rb") as f:
                    public_key_data = f.read()
            except:
                print("abertura de arquivo falhou!")
                
            try:
                public_key = load_pem_public_key(public_key_data)
            except:
                print("carregamento da chave falhou!")

            try:
                public_key.verify(
                b_signature,
                b_value,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            except Exception as e:
                print("Exception: ", type(e))
            else:
                print("Assinatura valida!")
            #checa se leilao existe

            #checa se eh maior lance

            #Requisito 4.4 - Se o lance for válido, o MS Lance publica o evento na fila lance_validado.

            channel.basic_publish(exchange=EXCHANGE_NAME, body=body, routing_key="lance_validado")
            print('lance validado!')


        if method.routing_key == "leilao_iniciado":
            #Somente aceitará o lance se: ID do leilão existir e se o leilão estiver ativo;
            #TODO: Imagino que sera necessario manter os leiloes ativos igual no client.py? mesma estrutura, mantendo tambem o maior lance para cada
            pass

        if method.routing_key == "leilao_finalizado":
            #TODO: Requisito 4.5 - Ao finalizar um leilão, deve publicar na fila leilao_vencedor,
            #informando o ID do leilão, o ID do vencedor do leilão e o valor
            #negociado. O vencedor é o que efetuou o maior lance válido até o
            #encerramento.
            pass

    channel.basic_consume(
        queue=queue_name, on_message_callback=on_message, auto_ack=True
    )

    channel.start_consuming()


if __name__ == "__main__":
    main()
