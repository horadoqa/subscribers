import time
import smtplib
import os
import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Caminho para o seu ChromeDriver
chromedriver_path = "/usr/bin/chromedriver"  # Substitua pelo caminho do seu chromedriver

# Configurações para rodar o Selenium sem abrir uma janela do navegador (headless)
options = Options()
options.headless = True
options.add_argument("--headless")  # Rodar o Chrome em modo headless

driver = webdriver.Chrome(service=Service(chromedriver_path), options=options)

# URL do canal
url = "https://www.youtube.com/@horadoqa"

# Função para obter o número de inscritos
def get_subscriber_count():
    # Inicializando o WebDriver
    driver = webdriver.Chrome(service=Service(chromedriver_path), options=options)
    
    # Acessar a página do canal
    driver.get(url)
    
    try:
        # Aguardar até que o número de inscritos esteja visível
        subscriber_count_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="page-header"]/yt-page-header-renderer/yt-page-header-view-model/div/div[1]/div/yt-content-metadata-view-model/div[2]/span[1]')))
        
        # Pegar o texto do elemento
        subscriber_count_text = subscriber_count_element.text.strip()
        print(f'Texto de inscritos: {subscriber_count_text}')

        # Retornar o texto original, sem fazer a conversão
        print(f'O canal tem {subscriber_count_text} inscritos.')
        return subscriber_count_text
    except Exception as e:
        # Fechar o navegador
        driver.quit()

        print(f"Erro ao encontrar o número de inscritos: {e}")
        return None
    finally:
        driver.quit()

# Executando a função
get_subscriber_count()
