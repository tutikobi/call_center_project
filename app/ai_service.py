# call_center_project/app/ai_service.py

import os
import re

KNOWLEDGE_BASE_DIR = 'knowledge_base'

def load_knowledge_base():
    """Lê todos os ficheiros da pasta knowledge_base e compila o conteúdo."""
    knowledge = {}
    if not os.path.exists(KNOWLEDGE_BASE_DIR):
        return knowledge

    for filename in os.listdir(KNOWLEDGE_BASE_DIR):
        if filename.endswith(".txt"):
            with open(os.path.join(KNOWLEDGE_BASE_DIR, filename), 'r', encoding='utf-8') as f:
                content = f.read()
                qa_pairs = re.findall(r'Pergunta:\s*(.*?)\s*Resposta:\s*(.*?)(?=\nPergunta:|\Z)', content, re.DOTALL | re.IGNORECASE)
                for q, a in qa_pairs:
                    knowledge[q.strip().lower()] = a.strip()
    return knowledge

def get_ai_response(user_message, knowledge_base):
    """Tenta encontrar uma resposta na base de conhecimento."""
    user_message = user_message.lower().strip()

    # Procura por palavras-chave da pergunta na mensagem do utilizador
    for question, answer in knowledge_base.items():
        keywords = question.split()
        if all(keyword in user_message for keyword in keywords):
            return answer
            
    return None