#!/usr/bin/env python
import pika
import sys
import datetime

from ..static import exchange_name


def main():
    today = datetime.datetime.now()
    leiloes = [
        {
            "id": 123,
            "descricao": "Descrição qualquer",
            "start": today,
            "end": today + datetime.timedelta(minutes=1),
        },
        {
            "id": 234,
            "descricao": "Mais uma descrição",
            "start": today + datetime.timedelta(seconds=20),
            "end": today + datetime.timedelta(minutes=1, seconds=20),
        },
    ]

    connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
    channel = connection.channel()
    channel.exchange_declare(exchange=exchange_name, exchange_type="direct")

    starts = [leilao["start"] for leilao in leiloes]
    ends = [leilao["end"] for leilao in leiloes]
    
    o_start = 
    o_end = 

    try:
        while True:
            pass
    except Exception as e:
        print("Expection: ", e)

    channel.basic_publish(exchange=exchange_name, routing_key=severity, body=message)
    print(f" [x] Sent {severity}:{message}")
    connection.close()


if __name__ == "__main__":
    main()
