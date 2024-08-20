from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time

def criar_navegador():
    """ Cria e retorna uma nova instância do navegador Chrome. """
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--headless")
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")
    servico = Service(ChromeDriverManager().install())
    navegador = webdriver.Chrome(service=servico, options=options)
    print("Navegador Chrome aberto.")
    return navegador

def idade(navegador):
    """ Lida com a verificação de idade se necessário. """
    try:
        if "agecheck" in navegador.current_url:
            print("Página de verificação de idade detectada.")
            wait = WebDriverWait(navegador, 10)
            
            # Selecionar o ano no menu suspenso
            select_ano = wait.until(EC.presence_of_element_located((By.ID, 'ageYear')))
            select = Select(select_ano)
            select.select_by_value('2000')
            
            button = navegador.find_element(By.ID, 'view_product_page_btn')
            button.click()
            
            # Aguarda a página carregar após a seleção
            wait.until(EC.url_changes(navegador.current_url))
    except NoSuchElementException:
        print("Elemento de verificação de idade não encontrado.")
    except TimeoutException:
        print("Timeout ao lidar com a verificação de idade.")

def extrair_dados(url):
    navegador = criar_navegador()
    wait = WebDriverWait(navegador, 30)

    try:
        print(f"Acessando a URL: {url}")
        navegador.get(url)

        idade(navegador)

        # Coletar dados <div>
        info = wait.until(EC.presence_of_element_located((By.ID, 'genresAndManufacturer')))
        div_id = info.get_attribute('innerHTML')
        soup = BeautifulSoup(div_id, 'html.parser')

        # Localizando os gêneros
        span_element = soup.find('span', {'data-panel': True})
        if not span_element:
            print("Elemento <span> com atributo 'data-panel' não encontrado.")
            return None

        links = span_element.find_all('a')
        if not links:
            print("Nenhum link encontrado dentro do <span>.")
            return None

        # Extrair os gêneros
        genres = [link.get_text() for link in links]

        return genres
    except TimeoutException:
        print(f"Timeout ao localizar elementos na URL {url}.")
        return None
    except NoSuchElementException:
        print(f"Elemento não encontrado na URL {url}.")
        return None
    finally:
        navegador.quit()

# Carrega o CSV existente
df_existente_tr = pd.read_csv(r'G:\Vscode projetos\steamdb\coleta_de_dados\c_span.csv')

# Carregando o CSV com novos dados
df_novos = pd.read_csv(r'G:\Vscode projetos\steamdb\coleta_de_dados\b_nome_url_steam.csv')
links = df_novos['URL']
nomes = df_novos['Nome']
app_ids = df_novos['app_id']

# Lista para armazenar dados temporariamente
dados_reviews = []

# Iterar sobre os links, nomes e app_ids
for link, nome, app_id in zip(links, nomes, app_ids):
    print(f"Iniciando coleta para: {nome} (App ID: {app_id})")
    dados_r = extrair_dados(link)
    if dados_r:
        df = pd.DataFrame({
            'app_id': [app_id],
            'genres': [', '.join(dados_r)],
            'Nome': [nome],
        })
        dados_reviews.append(df)
        
    # Concatena todos os DataFrames em um único DataFrame
    df_final = pd.concat(dados_reviews, ignore_index=True)

    # Verifica quais app_ids já existem e adiciona apenas novos
    df_existente_app_ids = df_existente_tr['app_id'].tolist()
    df_novos_dados = df_final[~df_final['app_id'].isin(df_existente_app_ids)]

    # Adiciona os novos dados ao DataFrame existente e salva
    if not df_novos_dados.empty:
        df_atualizado_tr = pd.concat([df_existente_tr, df_novos_dados], ignore_index=True)
        df_atualizado_tr.to_csv(r'G:\Vscode projetos\steamdb\coleta_de_dados\c_span.csv', index=False)
        print("Dados salvos com sucesso.")
    else:
        print("Nenhum dado novo para salvar.")

print("Todos os dados foram processados e salvos.")
