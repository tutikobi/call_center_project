# call_center_project/desktop_agent/main.py
import sys
import time
import requests
from datetime import datetime
import platform
import json

CONFIG_FILE = 'agent_config.json'

def load_config():
    """Carrega as configurações de um arquivo JSON."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERRO: Arquivo de configuração '{CONFIG_FILE}' não encontrado.")
        print("Por favor, crie o arquivo com o seguinte conteúdo e preencha seus dados:")
        print('{\n    "SERVER_URL": "http://127.0.0.1:5000/api/productivity/log",\n    "API_KEY": "seu-email@suaempresa.com",\n    "LOG_INTERVAL_SECONDS": 15\n}')
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Erro ao ler o arquivo de configuração '{CONFIG_FILE}'. Verifique se é um JSON válido.")
        sys.exit(1)

config = load_config()
SERVER_URL = config.get("SERVER_URL")
API_KEY = config.get("API_KEY")
LOG_INTERVAL_SECONDS = config.get("LOG_INTERVAL_SECONDS", 15)

if platform.system() == "Windows":
    try:
        from monitors.windows_monitor import get_active_window_info
    except ImportError:
        print("Erro: Bibliotecas para monitoramento do Windows não encontradas.")
        print("Por favor, instale-as com: pip install psutil pywin32 uiautomation")
        sys.exit(1)
else:
    print(f"Sistema operacional {platform.system()} ainda não é suportado.")
    sys.exit(1)

def send_log(activity_data):
    headers = {'Content-Type': 'application/json', 'X-API-KEY': API_KEY}
    try:
        response = requests.post(SERVER_URL, json=activity_data, headers=headers, timeout=10)
        if response.status_code == 201:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Log enviado: {activity_data.get('process_name')}")
        else:
            print(f"ERRO ao enviar log: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"ERRO de conexão com o servidor: {e}")

def main():
    print("================================================")
    print("  Agente de Monitoramento de Produtividade")
    print("================================================")
    print(f"Servidor: {SERVER_URL}")
    print(f"Agente: {API_KEY}")
    print(f"Intervalo: {LOG_INTERVAL_SECONDS} segundos")
    print("Pressione Ctrl+C para encerrar.")
    print("------------------------------------------------")

    while True:
        try:
            info = get_active_window_info()
            if info and info.get('title'):
                log_data = {
                    "timestamp": datetime.now().isoformat(),
                    "window_title": info.get("title"),
                    "process_name": info.get("process"),
                    "url": info.get("url")
                }
                send_log(log_data)

            time.sleep(LOG_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            # Esta é a parte que foi corrigida
            print("\nAgente encerrado pelo usuário.")
            break
        except Exception as e:
            print(f"Ocorreu um erro inesperado no loop principal: {e}")
            time.sleep(LOG_INTERVAL_SECONDS * 2)

if __name__ == "__main__":
    if not all([SERVER_URL, API_KEY]):
        print("ERRO: 'SERVER_URL' e 'API_KEY' devem estar definidos em agent_config.json.")
    else:
        main()