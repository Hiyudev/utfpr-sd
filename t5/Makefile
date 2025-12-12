ex:
	python3 src/services/externo.py

la:
	python3 src/services/lance.py

le:
	python3 src/services/leilao.py

pa:
	python3 src/services/pagamento.py

api:
	gunicorn gateway:app --worker-class gevent --bind 127.0.0.1:8888 --chdir src

debug-api: 
	gunicorn gateway:app --access-logfile - --error-logfile - --log-level debug --worker-class gevent --bind 127.0.0.1:8888 --chdir src

up:
	docker compose -f docker-compose.services.yml up -d

down:
	docker compose -f docker-compose.services.yml down -v

gen:
	python -m grpc_tools.protoc -I./src/protocols --python_out=./src/utils --mypy_out=./src/utils --grpc_python_out=./src/utils --mypy_grpc_out=./src/utils ./src/protocols/gateway.proto
	python -m grpc_tools.protoc -I./src/protocols --python_out=./src/utils --mypy_out=./src/utils --grpc_python_out=./src/utils --mypy_grpc_out=./src/utils ./src/protocols/lance.proto
	python -m grpc_tools.protoc -I./src/protocols --python_out=./src/utils --mypy_out=./src/utils --grpc_python_out=./src/utils --mypy_grpc_out=./src/utils ./src/protocols/leilao.proto
	python -m grpc_tools.protoc -I./src/protocols --python_out=./src/utils --mypy_out=./src/utils --grpc_python_out=./src/utils --mypy_grpc_out=./src/utils ./src/protocols/pagamento.proto