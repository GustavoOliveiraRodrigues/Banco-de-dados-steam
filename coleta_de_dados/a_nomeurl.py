#Bibliotecas
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchWindowException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time


#Iniciando a pagina vazia do crome
options = Options()
options.add_argument('--headless')

servico = Service(ChromeDriverManager().install())
navegador = webdriver.Chrome(service=servico)

try:
    #entrando no navegador
    navegador.get('https://steamdb.info/charts/')
    time.sleep(5)
    
    #variaveis
    nomes = []
    urls = []
    pagina = 1

    #Quantidade de paginas
    while pagina <=10:
        try:
            links = navegador.find_elements(By.XPATH, '//td/a')

            #Passando pelos links
            for link in links:
                nome = link.text
                #confirmando se tem o nome e o link para não pegar informações a mais
                if nome:
                    href = link.get_attribute('href')

                    urls.append(href)  
                    nomes.append(nome)

                
            #buscando o botão de next e verificando se ele existe "A parte da verificação e so pq estava com erro"
            try:
                next_button = WebDriverWait(navegador, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.dt-paging-button.next'))
                )
                next_button.click()
                time.sleep(5)
                pagina += 1
            except TimeoutException:
                print("botão não licalizado")
                break
        #Verificando se a pagina estava disponivel            
        except NoSuchWindowException:
            print ("janela não encotrada")  
            break

    #Criando o data frame        
    df = pd.DataFrame({
        'Nome' : nomes,
        'URL'  : urls
    })
    #Criando o csv
    df.to_csv('nome_url.csv', index=False)
#Fechando a pagina
finally:
    try:
        navegador.quit()
    #Verificando se não fechei a pagina sem querer e fiz o codigo dar erro    
    except NoSuchWindowException:
        print("A janela do navegador não estava disponível para ser fechada.")