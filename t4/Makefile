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

up:
	docker compose -f docker-compose.services.yml up -d

down:
	docker compose -f docker-compose.services.yml down -v