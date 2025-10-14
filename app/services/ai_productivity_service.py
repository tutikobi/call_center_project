# call_center_project/app/services/ai_productivity_service.py
import openai
from flask import current_app
import json

class AiProductivityService:
    def __init__(self, app=None):
        self.api_key = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.api_key = app.config.get('OPENAI_API_KEY')
        if self.api_key:
            openai.api_key = self.api_key
            print("INFO: Serviço de IA da OpenAI configurado.")
        else:
            print("AVISO: Chave da OpenAI não configurada. A análise por IA está desativada.")

    def analyze_activity(self, activity_data: dict, rules: dict) -> dict:
        process_name = activity_data.get('process_name', '')
        url = activity_data.get('url', '')

        for rule in rules.get('process_rules', []):
            if rule.get('process', '').lower() in process_name.lower():
                return {"is_productive": rule.get('classification') == 'productive', "category": rule.get('category', 'N/A'), "reason": "Classificado por regra de processo."}
        
        for rule in rules.get('url_rules', []):
            if rule.get('keyword', '').lower() in url.lower():
                return {"is_productive": rule.get('classification') == 'productive', "category": rule.get('category', 'N/A'), "reason": "Classificado por regra de URL."}

        if not self.api_key:
            return {"is_productive": None, "category": "Não Classificado", "reason": "IA não configurada."}

        prompt_template = rules.get('custom_ai_prompt') or """
        Você é um analista de produtividade de um call center. Analise a atividade e classifique-a.
        Contexto: O trabalho envolve atender clientes, usar CRM, comunicar via Slack/Email. WhatsApp Business é produtivo. Redes sociais são improdutivas.
        Atividade: Título: {window_title}, Processo: {process_name}, URL: {url}
        Responda APENAS em JSON com as chaves: "is_productive" (true, false, ou null para neutro), "category" (uma palavra), "reason" (frase curta).
        """
        
        prompt = prompt_template.format(
            window_title=activity_data.get('window_title', 'N/A'),
            process_name=activity_data.get('process_name', 'N/A'),
            url=activity_data.get('url', 'N/A')
        )
        
        try:
            response = openai.chat.completions.create(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            current_app.logger.error(f"Erro na API OpenAI: {e}")
            return {"error": str(e), "is_productive": None, "category": "Erro IA"}

ai_productivity_service = AiProductivityService()