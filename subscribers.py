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

class NoUpdatesFound(Exception):
    pass

# Função para enviar um e-mail
def send_email(body):
    sender_email = "contaservico.horadoqa@gmail.com"  # Substitua pelo seu e-mail
    receiver_email = "horadoqa@gmail.com"  # E-mail do destinatário
    password = os.getenv('EMAIL_PASSWORD')  # Substitua pela senha do seu e-mail ou senha de app

    # Configura o servidor SMTP
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(sender_email, password)

    # Criação da mensagem
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = "📢 Mudança no número de inscritos"

    # Corpo do e-mail
    message.attach(MIMEText(body, 'plain'))

    # Enviar e-mail
    server.sendmail(sender_email, receiver_email, message.as_string())
    server.quit()
    print("E-mail enviado com sucesso!")

# Função para enviar uma mensagem para o discord
def send_discord_message(message):
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')

    data = {
        "content": message
    }

    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(webhook_url, json=data, headers=headers)

    if response.status_code == 204:
        print("Mensagem enviada para o Discord com sucesso!")
    else:
        print(f"Erro ao enviar mensagem: {response.status_code} - {response.text}")

# Função para registrar a mudança no número de inscritos no arquivo de log
def log_subscriber_change(last_subscriber_count, current_subscriber_count):
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_message = f"{current_time} - O número de inscritos mudou! De {last_subscriber_count} para {current_subscriber_count}\n"
    
    with open("subscribe.log", "a") as log_file:
        log_file.write(log_message)
    
    print(f"Log gravado: {log_message.strip()}")

# Função para obter o número de inscritos
def get_subscriber_count():
    # Acessar a página do canal
    driver.get(url)
    
    try:
        # Aguardar até que o número de inscritos esteja visível
        subscriber_count_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="page-header"]/yt-page-header-renderer/yt-page-header-view-model/div/div[1]/div/yt-content-metadata-view-model/div[2]/span[1]'))
        )
        
        # Pegar o texto do elemento
        subscriber_count_text = subscriber_count_element.text.strip()
        
        # Retirar a palavra "subscribers" do texto, se presente
        subscriber_count_text = subscriber_count_text.replace(' subscribers', '').strip()

        return subscriber_count_text
    except Exception as e:
        print(f"Erro ao encontrar o número de inscritos: {e}")
        return None


def save_subscribers_update(subscribers_updates, current_subscriber_count):
    subscriber_update = {
        "UpdateTime": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "SubscribersCount": current_subscriber_count
    }

    subscribers_updates['SubscribersUpdates'].append(subscriber_update)

    with open("subscribers_updates.json", "w") as f:
        json.dump(subscribers_updates, f, indent=4)

def main():
    # Carregar ou inicializar o dicionário de atualizações
    if os.path.exists("subscribers_updates.json"):
        with open("subscribers_updates.json", "r") as f:
            subscribers_updates = json.load(f)
    else:
        subscribers_updates = {"SubscribersUpdates": []}

    current_subscriber_count = get_subscriber_count()

    if not current_subscriber_count:
        print("Erro ao obter o número de inscritos.")
        return

    # Criar a mensagem de alerta
    body = f'📢 O número de inscritos atual: {current_subscriber_count}'
    print(body)

    # Enviar mensagem no Discord
    send_discord_message(body)
    
    # Gravar no log
    log_subscriber_change(None, current_subscriber_count)  # Log da primeira vez (sem comparação)
    
    # Salvar a atualização
    save_subscribers_update(subscribers_updates, current_subscriber_count)
    
    # Enviar e-mail
    send_email(body)  


if __name__ == "__main__":
    main()