from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import Select
import pandas as pd
from webdriver_manager.chrome import ChromeDriverManager
import re
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

def extrair_info(html, rotulo, delimitador):
    pattern = rf'<b>{rotulo}:</b>\s*{delimitador}'
    match = re.search(pattern, html, re.DOTALL)
    if match:
        return match.group(1).strip()
    return "Não encontrado"

def idade(navegador):
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

    except NoSuchElementException:
        print("Elemento não encontrado na página de confirmação de idade.")
        
def extrair_dados(url):
    navegador = criar_navegador()
    wait = WebDriverWait(navegador, 30)
    
    try:
        print(f"Acessando a URL: {url}")
        navegador.get(url)

        idade(navegador)
        
        try: 
            # Coletor <label>
            labels = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'label')))
            reviews_data = {
                'review_type_negative': None,
                'review_type_positive': None,
                'Nome': None,
                'URL': url
            }

            for label in labels:
                try:
                    label_html = label.get_attribute('innerHTML').replace('&nbsp;', ' ')
                    
                    match = re.search(r'(\w+)\s*<span class="user_reviews_count">\(([\d,]+)\)</span>', label_html)
                    
                    if match:
                        review_type = match.group(1).strip()
                        review_count = match.group(2)
                        
                        if 'Positive' in review_type:
                            reviews_data['review_type_positive'] = review_count
                        elif 'Negative' in review_type:
                            reviews_data['review_type_negative'] = review_count
                except NoSuchElementException:
                    pass

            # Coletor dados <div>
            info = wait.until(EC.presence_of_element_located((By.ID, 'genresAndManufacturer')))
            div_id = info.get_attribute('innerHTML')

            title = extrair_info(div_id, 'Title', '(.*?)<br>')
            developer = extrair_info(div_id, 'Developer', '<a [^>]*>(.*?)</a>')
            publisher = extrair_info(div_id, 'Publisher', '<a [^>]*>(.*?)</a>')
            release_date = extrair_info(div_id, 'Release Date', '(.*?)<br>')

            reviews_data.update({
                'Title': title,
                'developer': developer,
                'publisher': publisher,
                'release_date': release_date
            })

            print(f"Dados coletados da URL {url}.")
            return reviews_data

        except TimeoutException:
            print(f"Timeout ao localizar elementos <label> na URL {url}.")
            return None

    except TimeoutException:
        print(f"Timeout ao acessar a URL {url}.")
        return None
    except Exception as e:
        print(f"Erro ao acessar a URL {url}: {e}")
        return None
    finally:
        navegador.quit()
        print("Navegador fechado.")

# Carregando o CSV existente
df_existente = pd.read_csv(r'G:\Vscode projetos\steamdb\coleta_de_dados\c_li.csv')
df_existente_tr = pd.read_csv(r'G:\Vscode projetos\steamdb\coleta_de_dados\c_tr.csv')
# Carregando o CSV com novos dados
df_novos = pd.read_csv(r'G:\Vscode projetos\steamdb\coleta_de_dados\b_nome_url_steam_faltante.csv')
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
        dados_r['Nome'] = nome
        dados_r['app_id'] = app_id
        dados_r['app_type'] = 'Game'
        
        # Calcular a porcentagem de resenhas positivas
        positive = int(dados_r['review_type_positive'].replace(',', '')) if dados_r['review_type_positive'] else 0
        negative = int(dados_r['review_type_negative'].replace(',', '')) if dados_r['review_type_negative'] else 0
        percentage = round((positive / (positive + negative)) * 100, 1) if (positive + negative) > 0 else 0
        dados_r['percentage_reviews'] = percentage
        
        # Adicionar os dados à lista
        dados_reviews.append({
            'app_id': app_id,
            'Nome': nome,
            'positive_reviews': positive,
            'negative_reviews': negative,
            'percentage_reviews': percentage
        })

        # Criar um DataFrame com os dados coletados
        df_novos_dados = pd.DataFrame(dados_reviews)

        # Concatenar os novos dados ao final do DataFrame existente
        df_atualizado = pd.concat([df_existente, df_novos_dados], ignore_index=True)
        df_atualizado.to_csv(r'G:\Vscode projetos\steamdb\coleta_de_dados\c_li.csv', index=False)
        
        df_novos_dados_tr = pd.DataFrame([{
            'app_id': app_id,
            'app_type': 'Game',
            'developer': dados_r.get('developer', ''),
            'publisher': dados_r.get('publisher', ''),
            'release_date': dados_r.get('release_date', '')
        }])

        df_existente_tr = pd.read_csv(r'G:\Vscode projetos\steamdb\coleta_de_dados\c_tr.csv')

        if not df_existente_tr[df_existente_tr['app_id'] == app_id].empty:
            print(f"Dados para {app_id} já existentes no arquivo c_tr.csv.")
        else:
            # Adiciona os novos dados
            df_atualizado_tr = pd.concat([df_existente_tr, df_novos_dados_tr], ignore_index=True)
            df_atualizado_tr.to_csv(r'G:\Vscode projetos\steamdb\coleta_de_dados\c_tr.csv', index=False)

        print(f"Dados salvos para: {nome} (App ID: {app_id})")
    else:
        print(f"Falha ao coletar dados para: {nome} (App ID: {app_id})")

print("Todos os dados foram processados e salvos.")