# call_center_project/desktop_agent/main.py

import sys
import time
import requests
from datetime import datetime
import platform
import json
import os
import tkinter as tk
from tkinter import simpledialog, messagebox
from urllib.parse import urlparse, parse_qs
import logging

# --- ALTERAÇÃO APLICADA AQUI: Define o caminho do log para a Área de Trabalho ---
try:
    # Obtém o caminho da Área de Trabalho do utilizador atual
    desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    log_file_path = os.path.join(desktop_path, 'agent_debug.log')
except Exception:
    # Fallback para a pasta do script se não conseguir encontrar a Área de Trabalho
    log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'agent_debug.log')

logging.basicConfig(filename=log_file_path, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filemode='a') # filemode='a' para adicionar ao ficheiro
# --- FIM DA ALTERAÇÃO ---

CONFIG_FILE = 'agent_config.json'
SERVER_URL_BASE = "http://127.0.0.1:5000"

def get_token_from_args():
    logging.info(f"Argumentos recebidos: {sys.argv}")
    if len(sys.argv) > 1:
        url = sys.argv[1]
        if url.startswith("callcenteragent:"):
            try:
                parsed_url = urlparse(url)
                query_params = parse_qs(parsed_url.query)
                token = query_params.get('token', [None])[0]
                logging.info(f"Token extraído dos argumentos: {token}")
                return token
            except Exception as e:
                logging.error(f"Erro ao parsear argumentos: {e}")
                return None
        else:
            logging.warning(f"Argumento recebido não parece ser um link de protocolo: {url}")
            return None
    logging.info("Nenhum argumento de token encontrado.")
    return None

def load_config():
    # Procura o config na pasta do executável
    config_path = os.path.join(os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__)), CONFIG_FILE)
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                logging.info(f"Configuração carregada: API_KEY={config.get('API_KEY')}")
                return config.get("API_KEY")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Erro ao carregar config de {config_path}: {e}")
        return None
    logging.info(f"Ficheiro de config não encontrado em {config_path}")
    return None


def save_config(api_key):
    # Salva o config na pasta do executável
    config_path = os.path.join(os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__)), CONFIG_FILE)
    config = {
        "SERVER_URL": f"{SERVER_URL_BASE}/api/productivity/log",
        "API_KEY": api_key,
        "LOG_INTERVAL_SECONDS": 15
    }
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        logging.info(f"Configuração salva em {config_path} com API_KEY: {api_key}")
    except Exception as e:
        logging.error(f"Erro ao salvar config em {config_path}: {e}")


def link_agent(token=None):
    logging.info(f"Função link_agent chamada com token: {'Fornecido' if token else 'Não fornecido'}")
    root = tk.Tk()
    root.withdraw()

    token_origin = get_token_from_args() # Verifica se veio do argumento antes de pedir

    if not token and not token_origin: # Só pede na GUI se não veio como argumento
        logging.info("Token não fornecido diretamente ou via args, mostrando diálogo.")
        token = simpledialog.askstring("Vincular Agente", "Por favor, cole o token gerado no seu dashboard web:", parent=root)
    elif token_origin:
         token = token_origin # Usa o token do argumento
         logging.info("Token obtido via argumento, pulando diálogo.")
    else:
         # Token foi passado para a função, mas não via argumento (caso raro, mas possível)
         logging.info("Token fornecido diretamente para a função.")


    if not token:
        logging.warning("Nenhum token fornecido ou diálogo cancelado.")
        # Só mostra erro se não foi via link
        if token_origin is None:
             messagebox.showerror("Erro", "O processo foi cancelado. O token é necessário.")
        return None

    try:
        logging.info(f"Tentando vincular com o token: {token[:5]}...")
        response = requests.post(f"{SERVER_URL_BASE}/api/desktop_agent/link", json={"token": token}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            api_key = data.get('api_key')
            save_config(api_key)
            logging.info(f"Vinculação bem-sucedida. API_KEY: {api_key}")
            messagebox.showinfo("Sucesso", f"Agente vinculado com sucesso!\nO monitoramento será iniciado.")
            return api_key
        else:
            logging.error(f"Falha na vinculação. Status: {response.status_code}, Resposta: {response.text}")
            messagebox.showerror("Erro de Vinculação", f"Token inválido ou expirado: {response.json().get('message')}")
            # Limpa config inválido se existir
            config_path = os.path.join(os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__)), CONFIG_FILE)
            if os.path.exists(config_path):
                os.remove(config_path)
                logging.info("Configuração antiga removida devido a falha na vinculação.")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro de conexão durante a vinculação: {e}")
        messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao servidor: {e}")
        return None

if platform.system() == "Windows":
    try:
        from monitors.windows_monitor import get_active_window_info
    except ImportError as e:
        logging.critical(f"Erro fatal ao importar dependências do Windows: {e}")
        root = tk.Tk(); root.withdraw()
        messagebox.showerror("Erro Crítico", "Bibliotecas (psutil, pywin32, uiautomation) não encontradas ou corrompidas. Por favor, reinstale o programa ou contate o suporte.")
        sys.exit(1)
else:
    logging.critical(f"Sistema operacional não suportado: {platform.system()}")
    root = tk.Tk(); root.withdraw()
    messagebox.showerror("Erro Crítico", f"Sistema operacional {platform.system()} não é suportado.")
    sys.exit(1)

def send_log(activity_data, api_key):
    headers = {'Content-Type': 'application/json', 'X-API-KEY': api_key}
    try:
        url = f"{SERVER_URL_BASE}/api/productivity/log"
        response = requests.post(url, json=activity_data, headers=headers, timeout=10)
        if response.status_code != 201:
             logging.warning(f"Erro ao enviar log: Status={response.status_code}, Resposta={response.text[:100]}") # Limita o tamanho da resposta no log
    except requests.exceptions.RequestException as e:
        logging.warning(f"Erro de conexão ao enviar log: {e}")
        pass # Continua tentando

def main():
    logging.info("--- Agente de Monitoramento Iniciado ---")
    # Tenta evitar múltiplas instâncias
    mutex = None # Garante que mutex é definido
    try:
        import win32event, win32api, winerror
        mutex_name = "CallCenterAgentMutex_some_unique_string_v3"
        mutex = win32event.CreateMutex(None, 1, mutex_name)
        last_error = win32api.GetLastError()
        if last_error == winerror.ERROR_ALREADY_EXISTS:
            logging.warning("Mutex já existe. Outra instância pode estar rodando. Encerrando esta.")
            root = tk.Tk(); root.withdraw()
            messagebox.showwarning("Aviso", "O agente de monitoramento já está em execução.")
            sys.exit(0)
        elif last_error != 0:
             logging.warning(f"Erro não fatal ao criar mutex: {last_error}")
    except ImportError:
        logging.warning("pywin32 não encontrado. Não é possível garantir instância única.")
    except Exception as e:
        logging.error(f"Erro inesperado ao verificar instância única: {e}")


    api_key = load_config()
    token_from_arg = get_token_from_args()

    if token_from_arg:
        logging.info("Token encontrado nos argumentos. Tentando vincular/revincular...")
        api_key_new = link_agent(token=token_from_arg)
        if api_key_new:
            api_key = api_key_new # Atualiza a api_key se a vinculação foi bem sucedida
        elif not api_key: # Se a vinculação falhou E não havia config anterior
            logging.error("Falha ao vincular com token do argumento e sem config existente. Encerrando.")
            sys.exit(1)
        # Se a vinculação falhou mas existe config anterior, continua usando a antiga (pode ser temporário)
        elif api_key:
             logging.warning("Falha ao vincular com token do argumento. Usando API Key da configuração existente.")

    elif not api_key:
        logging.info("Nenhuma configuração encontrada e nenhum token nos argumentos. Pedindo token via GUI...")
        api_key = link_agent() # Pede token via GUI

    if not api_key:
        logging.error("Não foi possível obter a API Key (email do agente). Encerrando.")
        sys.exit(1)

    logging.info(f"Iniciando loop de monitoramento para o agente: {api_key}")
    while True:
        try:
            info = get_active_window_info()
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "window_title": info.get("title") if info else None,
                "process_name": info.get("process") if info else None,
                "url": info.get("url") if info else None
            }
            send_log(log_data, api_key)
            time.sleep(15)
        except KeyboardInterrupt:
             logging.info("Agente encerrado pelo usuário (Ctrl+C).")
             break
        except Exception as e:
            logging.error(f"Erro inesperado no loop principal: {e}", exc_info=True)
            time.sleep(30)
    
    # Libera o mutex ao sair
    if mutex:
        try:
             win32api.CloseHandle(mutex)
             logging.info("Mutex liberado.")
        except Exception as e:
             logging.error(f"Erro ao liberar mutex: {e}")


if __name__ == "__main__":
    main()