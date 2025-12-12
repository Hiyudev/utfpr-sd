# Configuração do projeto
Para instalar as dependências do projeto:
1. `python3 -m venv .venv` -- Cria um ambiente virtual
2. `source .venv/bin/activate` -- Ativa o ambiente virtual
3. `pip install -r requirements.txt` -- Instala as dependências do projeto

Caso adicione uma nova biblioteca:
1. `pip install <nome-da-biblioteca>` -- Instala a nova biblioteca
2. `pip freeze > requirements.txt` -- Atualiza o arquivo de dependências

# Configuração do Redis
No projeto, é utilizado o Docker para instanciar o Redis que é utilizada pelo Flask-SSE:
1. `docker-compose -f docker-compose.redis.yml up -d` -- Instancia o Redis

Caso a execução falhe, possivelmente é um problema de porta em uso esteja presente:
1. `./scripts/fix_port_used.sh` -- Elimina os processos que estão utilizando as portas

Caso queira parar o Redis:
1. `docker-compose -f docker-compose.redis.yml down` -- Para o Redis

Caso queira "resetar" o Redis:
1. `docker-compose -f docker-compose.redis.yml down -v` -- Para e remove volumes do Redis, e volumes seriam os dados persistentes do Redis.

# Execução do projeto
É necessário que o Redis esteja em execução.

Em particular ao `Client`, deve ser executado o seguinte comando no diretório `client`: `npm run dev`
O resto dos serviços são executados via terminal, cada um em uma aba diferente e executando o comando `make {nome_do_serviço}`:
- `make ex` -- Executa o Serviço de pagamento externo
- `make pa` -- Executa o MS Pagamento
- `make le` -- Executa o MS Leilao
- `make la` -- Executa o MS Lance
- `make api` -- Executa o API Gateway

# Portas
- `5000`: `MS Pagamento`
- `5555`: `Sistema de pagamento externo`
- `8111`: `MS Leilao`
- `8100`: `MS Lance`
- `8888`: `API Gateway`

# Gerando gRPC
Para gerar os arquivos gRPC, basta executar o comando `make gen` no terminal, estando no diretório raiz do projeto.