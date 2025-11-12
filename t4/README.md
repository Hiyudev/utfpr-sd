# Configuração do projeto
Para instalar as dependências do projeto:
1. `python3 -m venv .venv` -- Cria um ambiente virtual
2. `source .venv/bin/activate` -- Ativa o ambiente virtual
3. `pip install -r requirements.txt` -- Instala as dependências do projeto

Caso adicione uma nova biblioteca:
1. `pip install <nome-da-biblioteca>` -- Instala a nova biblioteca
2. `pip freeze > requirements.txt` -- Atualiza o arquivo de dependências

# Configuração do RabbitMQ e Redis
No projeto, é utilizado o Docker para instanciar o RabbitMQ, e o Redis para o Flask-SSE:
1. `docker-compose -f docker-compose.services.yml up -d` -- Instancia o RabbitMQ/Redis

Caso a execução falhe, e um problema de porta em uso esteja presente:
1. `./scripts/fix_port_used.sh` -- Elimina os processos que estão utilizando as portas

Caso queira parar o RabbitMQ/Redis:
1. `docker-compose -f docker-compose.services.yml down` -- Para o RabbitMQ

Caso queira "resetar" o RabbitMQ/Redis:
1. `docker-compose -f docker-compose.services.yml down -v` -- Para e remove volumes do RabbitMQ/Redis, e volumes seriam os dados persistentes do RabbitMQ/Redis.

# Execução do projeto
É necessário que o RabbitMQ/Redis esteja em execução.

Em particular ao `API Gateway`, deve ser executado o seguinte comando:
`gunicorn gateway:app --worker-class gevent`

Em particular ao `Client`, deve ser executado o seguinte comando: `npm run dev`

# Portas
- `5000`: `MS Pagamento`
- `5555`: `Sistema de pagamento externo`
- `8000`: `MS Leilao`
- `8100`: `MS Lance`
- `8888`: `API Gateway`