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

CONFIG_FILE = 'agent_config.json'
SERVER_URL_BASE = "http://127.0.0.1:5000"

def get_token_from_args():
    """Verifica se um token foi passado como argumento de linha de comando."""
    if len(sys.argv) > 1:
        # O argumento será algo como "callcenteragent:?token=..."
        url = sys.argv[1]
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        return query_params.get('token', [None])[0]
    return None

def load_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config.get("API_KEY")
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return None

def save_config(api_key):
    config = {
        "SERVER_URL": f"{SERVER_URL_BASE}/api/productivity/log",
        "API_KEY": api_key,
        "LOG_INTERVAL_SECONDS": 15
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def link_agent(token=None):
    """Vincula o agente usando um token (via GUI ou argumento)."""
    root = tk.Tk()
    root.withdraw()

    if not token:
        token = simpledialog.askstring("Vincular Agente", "Por favor, cole o token gerado no seu dashboard web:", parent=root)
    
    if not token:
        if not get_token_from_args(): # Só mostra erro se não foi via link
            messagebox.showerror("Erro", "O processo foi cancelado. O token é necessário.")
        return None

    try:
        response = requests.post(f"{SERVER_URL_BASE}/api/desktop_agent/link", json={"token": token}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            api_key = data.get('api_key')
            save_config(api_key)
            messagebox.showinfo("Sucesso", f"Agente vinculado com sucesso!\nO monitoramento será iniciado em segundo plano.")
            return api_key
        else:
            messagebox.showerror("Erro de Vinculação", f"Token inválido ou expirado: {response.json().get('message')}")
            return None
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao servidor: {e}")
        return None

if platform.system() == "Windows":
    try:
        from monitors.windows_monitor import get_active_window_info
    except ImportError:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Erro de Dependência", "Bibliotecas para monitoramento não encontradas. Contate o suporte.")
        sys.exit(1)
else:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Erro de Compatibilidade", f"Sistema operacional {platform.system()} não é suportado.")
    sys.exit(1)

def send_log(activity_data, api_key):
    headers = {'Content-Type': 'application/json', 'X-API-KEY': api_key}
    try:
        url = f"{SERVER_URL_BASE}/api/productivity/log"
        requests.post(url, json=activity_data, headers=headers, timeout=10)
    except requests.exceptions.RequestException:
        pass

def main():
    # Evita que múltiplas instâncias rodem
    try:
        import win32event, win32api, winerror
        mutex_name = "CallCenterAgentMutex_some_unique_string"
        mutex = win32event.CreateMutex(None, 1, mutex_name)
        if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo("Informação", "O agente de monitoramento já está em execução.")
            sys.exit(0)
    except ImportError:
        pass # Ignora se pywin32 não estiver instalado

    api_key = load_config()
    token_from_arg = get_token_from_args()

    # Se recebeu um token via link, força a revinculação
    if token_from_arg:
        api_key = link_agent(token=token_from_arg)
    # Se não tem config, pede para vincular
    elif not api_key:
        api_key = link_agent()

    if not api_key:
        sys.exit(1)
    
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
                send_log(log_data, api_key)
            time.sleep(15)
        except Exception:
            time.sleep(30)

if __name__ == "__main__":
    main()