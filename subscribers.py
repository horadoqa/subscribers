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
    message['Subject'] = "ALERTA: Mudança no número de inscritos"

    # Corpo do e-mail
    message.attach(MIMEText(body, 'plain'))

    # Enviar e-mail
    server.sendmail(sender_email, receiver_email, message.as_string())
    server.quit()
    print("E-mail enviado com sucesso!")

# Função para enviar uma mensagem para o discord
def send_discord_message(message):
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')  # Substitua pelo seu Webhook URL

    # Criação da mensagem
    data = {
        "content": message
    }

    headers = {
        "Content-Type": "application/json"
    }

    # Enviar mensagem para o Discord
    response = requests.post(webhook_url, json=data, headers=headers)
    # print("Mensagem enviada para o Discord com sucesso!")

    if response.status_code == 204:
        print("Mensagem enviada para o Discord com sucesso!")
    else:
        print(f"Erro ao enviar mensagem: {response.status_code} - {response.text}")

# Função para registrar a mudança no número de inscritos no arquivo de log
def log_subscriber_change(last_subscriber_count, current_subscriber_count):
    # Obtém data e hora atual
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_message = f"{current_time} - O número de inscritos mudou! De {last_subscriber_count} para {current_subscriber_count}\n"
    
    # Abrir o arquivo subscribe.log e escrever a mensagem
    with open("subscribe.log", "a") as log_file:
        log_file.write(log_message)
    
    print(f"Log gravado: {log_message.strip()}")

# Função para obter o número de inscritos
def get_subscriber_count():
    # Inicializando o WebDriver
    driver = webdriver.Chrome(service=Service(chromedriver_path), options=options)
    
    # Acessar a página do canal
    driver.get(url)
    
    try:
        # Aguardar até que o número de inscritos esteja visível
        subscriber_count_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="page-header"]/yt-page-header-renderer/yt-page-header-view-model/div/div[1]/div/yt-content-metadata-view-model/div[2]/span[1]'))
        )
        
        # Pegar o texto do elemento
        subscriber_count = subscriber_count_element.text.strip()

        # Garantir que estamos pegando apenas o número (sem o texto "subscribers")
        if 'subscribers' in subscriber_count:
            subscriber_count = subscriber_count.split(' ')[0]  # Pegar só o número antes de "subscribers"
        
        print(f'O canal tem {subscriber_count} inscritos.')
        return subscriber_count
    except Exception as e:
        print(f"Erro ao encontrar o número de inscritos: {e}")
        return None
    finally:
        # Fechar o navegador
        driver.quit()

# Função para verificar o número de inscritos periodicamente e enviar e-mail
def check_subscriber_count_periodically():
    # Obter o primeiro número de inscritos
    first_subscriber_count = get_subscriber_count()
    
    if not first_subscriber_count:
        print("Erro ao obter o número de inscritos inicialmente.")
        return

    last_subscriber_count = first_subscriber_count

    while True:
        time.sleep(600)  # Espera 10 minutos (600 segundos)
        current_subscriber_count = get_subscriber_count()
        
        if current_subscriber_count != last_subscriber_count:
            body = f'ALERTA: O número de inscritos mudou! De {last_subscriber_count} para {current_subscriber_count}.'
            print(body)
            send_email(body)  # Enviar e-mail
            log_subscriber_change(last_subscriber_count, current_subscriber_count)  # Gravar no log
            send_discord_message(body)
            last_subscriber_count = current_subscriber_count
        else:
            print(f'O número de inscritos permanece o mesmo: {current_subscriber_count}. Nenhuma mensagem enviada.')

def save_subscribers_update(subscribers_updates, current_subscriber_count):

    subscriber_update = {
        "UpdateTime": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "SubscribersCount": current_subscriber_count
    }

    subscribers_updates['SubscribersUpdates'].append(subscriber_update)

    with open("subscribers_updates.json", "w") as f:
        json.dump(subscribers_updates, f, indent=4)


def main():

    with open("subscribers_updates.json", "r") as f:
        subscribers_updates = json.load(f)

    last_subscriber_count = [
        update['SubscribersCount'] for update in subscribers_updates['SubscribersUpdates']
    ].sort(reverse=True)[0]

    current_subscriber_count = get_subscriber_count()

    if current_subscriber_count == last_subscriber_count:
        raise NoUpdatesFound(
            f'O número de inscritos permanece o mesmo: {current_subscriber_count}. Nenhuma mensagem enviada.'
        )

    body = f'ALERTA: O número de inscritos mudou! De {last_subscriber_count} para {current_subscriber_count}.'
    print(body)
    send_email(body)  # Enviar e-mail
    # log_subscriber_change(last_subscriber_count, current_subscriber_count)  # Gravar no log
    send_discord_message(body)
    
    save_subscribers_update(subscribers_updates, current_subscriber_count)


if __name__ == "__main__":
    # Rodar a verificação
    # check_subscriber_count_periodically()
    main()