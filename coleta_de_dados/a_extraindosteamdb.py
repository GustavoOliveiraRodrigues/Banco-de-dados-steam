#bibliotecas
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import pandas as pd
from webdriver_manager.chrome import ChromeDriverManager

def criar_navegador():
    """ Cria e retorna uma nova instância do navegador Chrome. """
    options = Options()
    #options.add_argument('--headless')
    servico = Service(ChromeDriverManager().install())
    navegador = webdriver.Chrome(service=servico, options=options)
    return navegador

def formatar_chave(texto):
    """ Formata a chave do dicionário para um formato consistente. """
    return texto.strip().lower().replace(' ', '_').replace('%', 'percent')

def extrair_dados(url):
    navegador = criar_navegador()
    wait = WebDriverWait(navegador, 30)
    
    try:
        print(f"Acessando a URL: {url}")
        navegador.get(url)
        
        # Extração dos dados de <tr>
        trs = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, 'tr')))
        print("Elementos <tr> encontrados")
        
        buscatd = {
            'app_id': None,
            'app_type': None,
            'developer': None,
            'publisher': None,
            'last_record_update': None,
            'release_date': None
        }
        
        for tr in trs:
            tds = tr.find_elements(By.TAG_NAME, 'td')
            if len(tds) == 2:
                chave = formatar_chave(tds[0].text)
                if chave in buscatd:
                    buscatd[chave] = tds[1].text.strip()

        # Extração dos dados de <li> contendo <strong>
        elementos_li = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'li')))
        print("Elementos <li> encontrados")
        
        buscali = {
            'positive_reviews': None,
            'negative_reviews': None
        }

        for li in elementos_li:
            try:
                strong_elements = li.find_elements(By.TAG_NAME, 'strong')
                if strong_elements:
                    strong_element = strong_elements[0]
                    valor = strong_element.text.strip()
                    titulo = li.text.replace(valor, '').strip()
                    chave = formatar_chave(titulo)

                    if chave in buscali:
                        buscali[chave] = valor
            except NoSuchElementException:
                print("Elemento <strong> não encontrado dentro de <li>")

        return buscatd, buscali
    except TimeoutException:
        print(f"Timeout ao acessar a URL {url}")
        return None, None
    except Exception as e:
        print(f"Erro ao extrair a informação da página {url}: {e}")
        return None, None
    finally:
        navegador.quit()

# Carregando o CSV
df = pd.read_csv('b_nome_url.csv')
links = df['URL']
nomes = df['Nome']

# Listas para armazenar dados temporariamente
dados_tr = []
dados_li = []

# Iterar sobre os links e nomes
for link, nome in zip(links, nomes):
    dados_t, dados_l = extrair_dados(link)
    
    if dados_t and dados_t['app_id']:
        dados_t['Nome'] = nome
        dados_t['URL'] = link
        dados_tr.append(dados_t)

    if dados_l and any(dados_l.values()):
        dados_l['app_id'] = dados_t.get('app_id', None)
        dados_l['Nome'] = nome    
        dados_l['URL'] = link
        dados_li.append(dados_l)

# Salvando os dados em arquivos CSV
df_tr = pd.DataFrame(dados_tr)
df_li = pd.DataFrame(dados_li)

df_tr.to_csv('c_tr.csv', index=False)
df_li.to_csv('c_li.csv', index=False)
