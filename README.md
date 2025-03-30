# airflow-hooks
Criação de DAG (Directed Acyclic Graph) para tarefas como extração, transformação e carregamento de dados (ETL) e a implementação de mecanismos de acesso ao banco de dados através de Hooks, XComs e variáveis no Airflow, além do envio de e-mail e sequência de tarefas com tomada de decisão dentro do workflow


# Automação de Pipelines de Bancos de Dados com Hooks, XComs e Variáveis no Airflow

# Instruções:

# 1- Inicialize ou use o ambiente Airflow

Abra o terminal ou prompt de comando e navegue até a pasta airflow onde estão os arquivos.

Execute o comando abaixo para criar as imagens Docker do Airflow e inicializar o banco de dados:

`docker compose up airflow-init`

`docker compose up`

Abra o navegador e efetue login. 

http://localhost:8080/login

User: airflow
Senha: airflow

Obs: Se você tiver o PostgreSQL instalado na sua máquina rodando na porta 5432 desligue-o ou haverá conflito de portas impedindo a inicialização do Airflow.

Se desejar o arquivo do docker compose mais recente no link abaixo:

https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html

# Execute o comando abaixo para criar o container com a base de dados externa:

`docker run --name sildb -p 5445:5432 -e POSTGRES_USER=usersil -e POSTGRES_PASSWORD=silpass5050 -e POSTGRES_DB=sildb -d postgres:16.1`

Execute os comandos abaixo para inspecionar os containers e fazer modificação do ambiente de rede:

`docker inspect sildb -f "{{json .NetworkSettings.Networks }}"`

`docker network ls`

`docker ps`

`docker inspect container_id`

`docker network disconnect bridge sildb`

`docker network connect rede_do_airflow sildb`

`docker inspect sildb`

# Configuraçãoes das conexões e variaveis no Airflow

Para atender as linhas abaixo da dag, você vai precisar:
- Configure a variavel send_mail no ariflow como true se quiser enviar email ou false se quiser usar o dummy
    send_email = Variable.get("send_email", default_var="false").lower()
- Configure a conexão com o banco do tipo Postgres e chamada 'postgres' com os dados do banco criado
    pg_hook = PostgresHook(postgres_conn_id='postgres')
- configure a conexão para envio de email chamada 'smtp_default' do tipo smtp com os dados da sua conta de email para envio, como não identificamos a conexao tem que ser smtp_default
    try: send_email_smtp(