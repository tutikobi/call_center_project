# call_center_project/app/ai_service.py

import os
import re

KNOWLEDGE_BASE_DIR = 'knowledge_base'
KNOWLEDGE_FILE = os.path.join(KNOWLEDGE_BASE_DIR, 'funcionalidades.txt')

def load_knowledge_base():
    """Lê todos os ficheiros da pasta knowledge_base e compila o conteúdo."""
    knowledge = {}
    if not os.path.exists(KNOWLEDGE_BASE_DIR):
        os.makedirs(KNOWLEDGE_BASE_DIR)
    
    if not os.path.exists(KNOWLEDGE_FILE):
        return {}

    with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
        qa_pairs = re.findall(r'Pergunta:\s*(.*?)\s*Resposta:\s*(.*?)(?=\n\nPergunta:|\Z)', content, re.DOTALL | re.IGNORECASE)
        for q, a in qa_pairs:
            knowledge[q.strip().lower()] = a.strip()
    return knowledge

def get_ai_response(user_message, knowledge_base):
    """Tenta encontrar uma resposta na base de conhecimento."""
    user_message = user_message.lower().strip()

    # Procura por palavras-chave da pergunta na mensagem do utilizador
    for question, answer in knowledge_base.items():
        keywords = re.split(r'\s+|_|-', question)
        if all(keyword in user_message for keyword in keywords):
            return answer
            
    return None

def add_to_knowledge_base(question, answer):
    """Adiciona um novo par de pergunta e resposta à base de conhecimento."""
    try:
        with open(KNOWLEDGE_FILE, 'a', encoding='utf-8') as f:
            f.write(f"\n\nPergunta: {question.strip()}\n")
            f.write(f"Resposta: {answer.strip()}")
        return True
    except Exception as e:
        print(f"Erro ao escrever na base de conhecimento: {e}")
        return False