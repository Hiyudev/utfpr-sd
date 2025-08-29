# Configuração do projeto
Para instalar as dependências do projeto:
1. `python3 -m venv .venv` -- Cria um ambiente virtual
2. `source .venv/bin/activate` -- Ativa o ambiente virtual
3. `pip install -r requirements.txt` -- Instala as dependências do projeto

Caso adicione uma nova biblioteca:
1. `pip install <nome-da-biblioteca>` -- Instala a nova biblioteca
2. `pip freeze > requirements.txt` -- Atualiza o arquivo de dependências

# Configuração do RabbitMQ
No projeto, é utilizado o Docker para instanciar o RabbitMQ:
1. `docker-compose -f docker-compose.rabbitmq.yml up -d` -- Instancia o RabbitMQ

Caso a execução falhe, e um problema de porta em uso esteja presente:
1. `./scripts/fix_port_used.sh` -- Elimina os processos que estão utilizando as portas

Caso queira parar o RabbitMQ:
1. `docker-compose -f docker-compose.rabbitmq.yml down` -- Para o RabbitMQ

Caso queira "resetar" o RabbitMQ:
1. `docker-compose -f docker-compose.rabbitmq.yml down -v` -- Para e remove volumes do RabbitMQ, e volumes seriam os dados persistentes do RabbitMQ.

# Execução do projeto
É necessário que o RabbitMQ esteja em execução.
É necessário que mais de um terminal esteja aberto, para representar os clientes.