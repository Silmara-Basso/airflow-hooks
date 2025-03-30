# Automação de Pipelines de Bancos de Dados com Hooks, XComs e Variáveis no Airflow

# Imports
import csv
import logging
from airflow import DAG
from airflow.operators.python_operator import PythonOperator, BranchPythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.email_operator import EmailOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.email import send_email_smtp
from airflow.models import Variable
from datetime import datetime, timedelta

# Definição dos argumentos para a DAG
default_args = {
    "owner": "Silmara Basso",
    "depends_on_past": False,
    "start_date": datetime(2024, 5, 3),
    "email_on_failure": True, # enviar email
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1)
}

# Criação da DAG 
sil_dag = DAG(
    "dag-hooks",
    default_args=default_args,
    schedule_interval=None,
    catchup=False
)

# Criação do Schema (se não existir) no Banco de Dados via Hook
def sil_cria_schema():

    # Cria um hook de conexão com o PostgreSQL
    pg_hook = PostgresHook(postgres_conn_id='postgres')
    
    # Define a consulta SQL para criar o schema silp5 se ele não existir
    create_schema_query = """
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'silhooks') THEN
            CREATE SCHEMA silhooks;
        END IF;
    END $$;
    """
    
    # Executa a consulta SQL definida acima
    pg_hook.run(create_schema_query, autocommit=True)
    
    logging.info("Schema silhooks criado com sucesso.")


# Criação da Tabela (se não existir) no Banco de Dados via Hook
def sil_cria_tabela():

    # Cria um hook de conexão com o PostgreSQL
    pg_hook = PostgresHook(postgres_conn_id='postgres')
    
    # Define a consulta SQL para criar a tabela silhooks.clientes se ela não existir
    create_table_query = """
    CREATE TABLE IF NOT EXISTS silhooks.clientes (
        id INT PRIMARY KEY,
        nome VARCHAR(50),
        cidade VARCHAR(50),
        pais VARCHAR(50)
    );
    """
    
    pg_hook.run(create_table_query, autocommit=True)

    logging.info("Tabela silhooks.clientes criada com sucesso.")


# Inserindo os Dados no Banco de Dados via Hook e Tratando Duplicidade
def sil_insere_dados():

    # Cria um hook de conexão com o PostgreSQL
    pg_hook = PostgresHook(postgres_conn_id='postgres')
    
    # Lista de clientes a serem inseridos
    clientes = [
        (1, 'João Silva', 'São Paulo', 'Brasil'),
        (2, 'Maria Souza', 'Rio de Janeiro', 'Brasil'),
        (3, 'Carlos Santos', 'Belo Horizonte', 'Brasil')
    ]
    
    for cliente in clientes:

        # Verifica se o cliente já existe
        query_check = f"SELECT COUNT(1) FROM silhooks.clientes WHERE id = {cliente[0]}"
        count = pg_hook.get_first(query_check)[0]
        
        # Insere o cliente se ele não existir - f=formatação
        if count == 0:
            query_insert = f"""
            INSERT INTO silhooks.clientes (id, nome, cidade, pais) VALUES
            ({cliente[0]}, '{cliente[1]}', '{cliente[2]}', '{cliente[3]}');
            """
            pg_hook.run(query_insert, autocommit=True)
            logging.info(f"Cliente {cliente[1]} inserido com sucesso.")
        else:
            logging.info(f"Cliente {cliente[1]} já existe na tabela.")

# Extraindo Dados do Banco de Dados com XCom Push - **kwargs para enviar qualquer numero de variáveis
# ti = task instance    
# Seleciona os dados da tabela
def sil_seleciona_dados(**kwargs):

    # Cria um hook de conexão com o PostgreSQL
    pg_hook = PostgresHook(postgres_conn_id='postgres')
    
    records = pg_hook.get_records('SELECT * FROM silhooks.clientes;')
    
    # Envia os registros selecionados para o XCom (cross-communication) do Airflow
    kwargs['ti'].xcom_push(key='query_result', value=records)
    
    logging.info("Dados selecionados da tabela silhooks.clientes.")

# Salvando Dados do Banco de Dados com XCom Pull
# Salva os dados
def sil_salva_dados(ti):

    # Busca os dados da instância da tarefa anterior usando o XCom
    task_instance = ti.xcom_pull(key='query_result', task_ids='tarefa_seleciona_dados')
    
    # Verifica se há dados disponíveis
    if task_instance:

        # Abre o arquivo clientes.csv para escrita
        with open('/opt/airflow/dags/clientes.csv', mode='w', newline='') as file:
            # Cria um escritor CSV
            writer = csv.writer(file)
            writer.writerow(['id', 'nome', 'cidade', 'pais']) 
            writer.writerows(task_instance)
        
        logging.info("Dados salvos em /opt/airflow/dags/clientes.csv.")
    else:
        logging.info("Nenhum dado encontrado.")

# Módulo de Envio de E-mail
def sil_envia_email():
    try:
        send_email_smtp(
            to=["silmarabasso@yahoo.com.br"],
            subject="DAG hooks - Sucesso",
            html_content="A DAG Hooks foi executada com sucesso.",
            files=["/opt/airflow/dags/clientes.csv"]
        )
        logging.info("E-mail enviado com sucesso.")
    except Exception as e:
        logging.error(f"Falha ao enviar e-mail: {str(e)}")

# Módulo de Decisão do Workflow com Base em Variável e Branch Python Operator
def sil_decide_envio_email():

    # Obtém o valor da variável "send_email" do Airflow; se não existir, usa "false" como padrão
    send_email = Variable.get("send_email", default_var="false").lower()
    
    # Verifica se o valor da variável é "true"
    if send_email == "true":
        # Retorna o ID da tarefa de envio de e-mail se a variável for "true"
        return "tarefa_envia_email"
    else:
        # Retorna o ID da tarefa dummy se a variável for "false"
        return "tarefa_dummy"

# Tarefas

tarefa_cria_schema = PythonOperator(task_id='tarefa_cria_schema',
                                    python_callable=sil_cria_schema,
                                    dag=sil_dag)

tarefa_cria_tabela = PythonOperator(task_id='tarefa_cria_tabela',
                                    python_callable=sil_cria_tabela, 
                                    dag=sil_dag)

tarefa_insere_dados = PythonOperator(task_id='tarefa_insere_dados',
                                     python_callable=sil_insere_dados, 
                                     dag=sil_dag)

tarefa_seleciona_dados = PythonOperator(task_id='tarefa_seleciona_dados',
                                        python_callable=sil_seleciona_dados,
                                        provide_context=True,
                                        dag=sil_dag)

tarefa_salva_dados = PythonOperator(task_id='tarefa_salva_dados',
                                    python_callable=sil_salva_dados, 
                                    provide_context=True,
                                    dag=sil_dag)

decisao_envio_email = BranchPythonOperator(task_id='decisao_envio_email',
                                           python_callable=sil_decide_envio_email,
                                           dag=sil_dag)

tarefa_envia_email = PythonOperator(task_id='tarefa_envia_email',
                                    python_callable=sil_envia_email,
                                    dag=sil_dag)

tarefa_dummy = DummyOperator(task_id='tarefa_dummy', dag=sil_dag)

# Sequência de tarefas com tomada de decisão no Airflow
tarefa_cria_schema >> tarefa_cria_tabela >> tarefa_insere_dados >> tarefa_seleciona_dados >> tarefa_salva_dados >> decisao_envio_email
decisao_envio_email >> tarefa_envia_email
decisao_envio_email >> tarefa_dummy
