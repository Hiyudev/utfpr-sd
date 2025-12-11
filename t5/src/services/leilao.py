import sys
import os
import grpc
import uuid
import sys
import os
from time import sleep
from concurrent import futures
import datetime
from threading import Thread, Lock
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger

# Adiciona o diretório raiz do projeto ao sys.path para importar 'utils'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from protocols.leilao_pb2 import Leilao_instance, GetLeiloesRequest, GetLeiloesResponse, CreateLeilaoRequest, CreateLeilaoResponse
from protocols.leilao_pb2_grpc import LeilaoServicer, add_LeilaoServicer_to_server

from protocols.lance_pb2 import OnLanceRequest, OnLanceResponse, OnInitLeilaoRequest, OnInitLeilaoResponse, OnEndLeilaoResponse, OnEndLeilaoRequest
from protocols.lance_pb2_grpc import LanceStub

# Variáveis globais
LEILOES = 3
#EXCHANGE_NAME = "exchange"
ID_SUMMARY_LENGTH = 8
leiloes: list[dict[str, any]] = []
leiloes_mutex = None
start_leiloes: list[dict[str, any]] = []
start_leiloes_mutex: Lock = None
end_leiloes: list[dict[str, any]] = []
end_leiloes_mutex: Lock = None


#deixar isso global provavelmente é um erro gigantesco, nao sei se vai dar certo. 50051 = lance
channel = grpc.insecure_channel('localhost:50051')
lanceStub = LanceStub(channel)

scheduler = BackgroundScheduler()

def trigger_start(payload: dict[str, any]):
    start_leiloes_mutex.acquire()
    start_leiloes.append(payload)
    start_leiloes_mutex.release()


def trigger_end(payload: dict[str, any]):
    end_leiloes_mutex.acquire()
    end_leiloes.append(payload)
    end_leiloes_mutex.release()

class LeilaoServicer(LeilaoServicer):
    def GetLeiloes(self, request: GetLeiloesRequest, _): #stream response

        data = GetLeiloesResponse()

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

            data.id = leilao["id"],
            data.name = leilao["name"],
            data.description = leilao["description"],
            data.value = leilao["value"],
            data.start = str(leilao["start"].timestamp()),
            data.end = str(leilao["end"].timestamp()),
        
            yield data

    
    def CreateLeilao(self, request: CreateLeilaoRequest, _):

        data: dict[str, any]
        value_float = float(request.value)
        start_datetime = datetime.datetime.fromtimestamp(float(request.start))
        end_datetime = datetime.datetime.fromtimestamp(float(request.end))
        data["start"] = start_datetime
        data["end"] = end_datetime
        data["value"] = value_float
        data["id"] = str(uuid.uuid4())
        data["description"] = request.description

        leiloes_mutex.acquire()
        leiloes.append(data)

        now = datetime.datetime.now()
        #acho q o certo seria mudar isso ne, ja q nao precisa mais
        if now < start_datetime:
            start_scheduler_trigger = DateTrigger(run_date=start_datetime)
            scheduler.add_job(
                trigger_start, args=(data,), trigger=start_scheduler_trigger
            )
        else:
            trigger_start(data)

        if now < end_datetime:
            end_scheduler_trigger = DateTrigger(run_date=end_datetime)
            scheduler.add_job(trigger_end, args=(data,), trigger=end_scheduler_trigger)
        else:
            trigger_end(data)

        leiloes_mutex.release()


        return CreateLeilaoResponse(ok=True)
    

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_LeilaoServicer_to_server(LeilaoServicer(), server)
    server.add_insecure_port("[::]:50052")
    server.start()
    print("starting leilao server...")
    #server.wait_for_termination()

    try:
        while True:
            sleep(0.2)  # Dorme por 200ms

            # Evita problemas com threads
            start_leiloes_mutex.acquire()
            end_leiloes_mutex.acquire()

            has_elements_in_starts = len(start_leiloes) > 0
            has_elements_in_ends = len(end_leiloes) > 0

            test = OnInitLeilaoRequest()
            test.id = "test"
            test.description = "test"
            test.start = 0
            test.end = 0


            message_test = OnInitLeilaoRequest(id=test.id, description=test.description, start=test.start, end=test.end)
            response_test: OnInitLeilaoResponse = lanceStub.OnInitLeilao(message_test)
            print(response_test.message)

            if has_elements_in_starts:
                for start_leilao in start_leiloes:
                    #message = serialize_leilao(start_leilao)
                    message_test = OnInitLeilaoRequest(id="", description="", start=0, end=0)
                    message.id = start_leilao["id"]
                    message.description = start_leilao["description"]
                    message.start = start_leilao["start"]
                    message.end = start_leilao["end"]

                    response = lanceStub.OnInitLeilao(message)

                    print(
                        f"[MS-Leilao] Leilao com o id {start_leilao['id'][:ID_SUMMARY_LENGTH]} foi iniciado."
                    )

            if has_elements_in_ends:
                for end_leilao in end_leiloes:
                    message = end_leilao["id"].encode("utf-8")
                    message: OnEndLeilaoRequest
                    message.id = end_leilao["id"]

                    response = lanceStub.OnEndLeilao(message)
                    print(
                        f"[MS-Leilao] Leilao com o id {message[:ID_SUMMARY_LENGTH]} foi finalizado."
                    )

            start_leiloes.clear()
            end_leiloes.clear()

            start_leiloes_mutex.release()
            end_leiloes_mutex.release()
    except KeyboardInterrupt:
        print("[MS-Leilao] Exiting...")
        #connection.close()

    #if connection.is_open:
    #    connection.close()

    return 1


if __name__ == "__main__":
    scheduler.start()
    leiloes_mutex = Lock()
    start_leiloes_mutex = Lock()
    end_leiloes_mutex = Lock()
    serve()

