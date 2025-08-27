# app/rh/calculos.py

from datetime import date, timedelta
from decimal import Decimal, ROUND_UP
import calendar

# --- FUNÇÃO AUXILIAR PARA CALCULAR DIAS ÚTEIS ---
def _get_dias_uteis_no_mes(ano, mes, jornada='5x2'):
    """Calcula o número de dias úteis em um mês, com base na jornada."""
    _, num_dias = calendar.monthrange(ano, mes)
    dias_uteis = 0
    
    # Feriados nacionais fixos (simplificado)
    feriados = [
        date(ano, 1, 1),   # Confraternização Universal
        date(ano, 4, 21),  # Tiradentes
        date(ano, 5, 1),   # Dia do Trabalho
        date(ano, 9, 7),   # Independência do Brasil
        date(ano, 10, 12), # Nossa Senhora Aparecida
        date(ano, 11, 2),  # Finados
        date(ano, 11, 15), # Proclamação da República
        date(ano, 12, 25)  # Natal
    ]

    for dia in range(1, num_dias + 1):
        data_atual = date(ano, mes, dia)
        dia_da_semana = data_atual.weekday() # Segunda-feira é 0 e Domingo é 6

        if data_atual in feriados:
            continue

        if jornada == '5x2': # Trabalha de segunda a sexta
            if dia_da_semana < 5: # 0-4 são Seg-Sex
                dias_uteis += 1
        elif jornada == '6x1': # Trabalha de segunda a sábado
             if dia_da_semana < 6: # 0-5 são Seg-Sáb
                dias_uteis += 1
        else: # Para outras jornadas, considera todos os dias como "úteis"
            dias_uteis +=1
            
    return dias_uteis

def calcular_rescisao(salario_bruto, data_admissao, data_demissao, motivo, aviso_previo_indenizado=False, ferias_vencidas=False):
    """
    Calcula os valores de uma rescisão de contrato de trabalho.
    Retorna um dicionário com os resultados.
    """
    try:
        salario = Decimal(salario_bruto)
        dias_trabalhados_no_mes = data_demissao.day
        
        saldo_salario = (salario / Decimal(30)) * Decimal(dias_trabalhados_no_mes)
        meses_trabalhados_ano = data_demissao.month
        if data_demissao.day >= 15:
            meses_trabalhados_ano += 1
        
        ferias_proporcionais = (salario / Decimal(12)) * Decimal(meses_trabalhados_ano)
        um_terco_ferias = ferias_proporcionais / Decimal(3)
        decimo_terceiro_proporcional = (salario / Decimal(12)) * Decimal(data_demissao.month)
        aviso_previo_valor = Decimal(0)
        multa_fgts = Decimal(0)

        if motivo == 'demissao_sem_justa_causa':
            if aviso_previo_indenizado:
                aviso_previo_valor = salario
            meses_totais = (data_demissao.year - data_admissao.year) * 12 + data_demissao.month - data_admissao.month
            fgts_depositado_estimado = (salario * Decimal('0.08')) * Decimal(meses_totais)
            multa_fgts = fgts_depositado_estimado * Decimal('0.40')
        
        ferias_vencidas_valor = Decimal(0)
        um_terco_ferias_vencidas = Decimal(0)
        if ferias_vencidas:
            ferias_vencidas_valor = salario
            um_terco_ferias_vencidas = salario / Decimal(3)

        verbas_rescisorias = {
            "saldo_salario": saldo_salario, "aviso_previo": aviso_previo_valor,
            "decimo_terceiro_proporcional": decimo_terceiro_proporcional,
            "ferias_proporcionais": ferias_proporcionais, "um_terco_ferias": um_terco_ferias,
            "ferias_vencidas": ferias_vencidas_valor, "um_terco_ferias_vencidas": um_terco_ferias_vencidas,
        }
        total_bruto = sum(verbas_rescisorias.values())
        salario_base_inss = saldo_salario + decimo_terceiro_proporcional
        
        if salario_base_inss <= 1500: inss = salario_base_inss * Decimal('0.075')
        elif salario_base_inss <= 2800: inss = salario_base_inss * Decimal('0.09')
        else: inss = salario_base_inss * Decimal('0.12')
        
        irrf = (total_bruto - inss) * Decimal('0.05') if (total_bruto - inss) > 2500 else Decimal(0)
        total_descontos = inss + irrf
        total_liquido = total_bruto - total_descontos

        return {
            "success": True, "verbas": verbas_rescisorias, "multa_fgts": multa_fgts,
            "descontos": {"inss": inss, "irrf": irrf},
            "totais": { "bruto": total_bruto, "descontos": total_descontos, "liquido": total_liquido }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def calcular_folha_pagamento(funcionario, ano=None, mes=None):
    """
    Calcula uma simulação da folha de pagamento mensal de um funcionário,
    de forma automatizada e condicional.
    """
    try:
        if ano is None: ano = date.today().year
        if mes is None: mes = date.today().month

        salario = Decimal(funcionario.salario)
        dias_uteis = _get_dias_uteis_no_mes(ano, mes, funcionario.jornada_trabalho)
        
        # --- PROVENTOS (COM LÓGICA DE CÁLCULO ATUALIZADA) ---
        proventos = {"salario_base": salario}
        if funcionario.recebe_va:
            proventos['vale_alimentacao'] = Decimal(funcionario.vale_alimentacao_diario or 0) * dias_uteis
        else:
            proventos['vale_alimentacao'] = Decimal(0)
            
        if funcionario.recebe_vr:
            proventos['vale_refeicao'] = Decimal(funcionario.vale_refeicao_diario or 0) * dias_uteis
        else:
            proventos['vale_refeicao'] = Decimal(0)

        # --- DESCONTOS (COM LÓGICA CONDICIONAL) ---
        descontos = {}
        if funcionario.recebe_vt:
            valor_total_vt = Decimal(funcionario.vale_transporte_diario or 0) * Decimal(dias_uteis)
            desconto_max_vt = salario * Decimal('0.06')
            descontos['vale_transporte'] = min(valor_total_vt, desconto_max_vt)
        else:
            valor_total_vt = Decimal(0)
            descontos['vale_transporte'] = Decimal(0)
        
        if salario <= 1500: inss = salario * Decimal('0.075')
        elif salario <= 2800: inss = salario * Decimal('0.09')
        elif salario <= 4200: inss = salario * Decimal('0.12')
        else: inss = salario * Decimal('0.14')
        descontos['inss'] = inss

        base_calculo_irrf = salario - inss
        if base_calculo_irrf <= 2259.20: irrf = Decimal(0)
        elif base_calculo_irrf <= 2826.65: irrf = (base_calculo_irrf * Decimal('0.075')) - Decimal('169.44')
        else: irrf = (base_calculo_irrf * Decimal('0.15')) - Decimal('381.44')
        descontos['irrf'] = max(Decimal(0), irrf)
        
        custos_empresa = {}
        custos_empresa['fgts'] = salario * Decimal('0.08')
        custos_empresa['inss_patronal'] = salario * Decimal('0.20')

        total_proventos = sum(proventos.values())
        total_descontos = sum(descontos.values())
        salario_liquido = total_proventos - total_descontos
        
        custo_total_empresa = (
            salario + 
            custos_empresa['fgts'] + 
            custos_empresa['inss_patronal'] + 
            proventos['vale_alimentacao'] + 
            proventos['vale_refeicao'] +
            (valor_total_vt - descontos['vale_transporte'])
        )

        return {
            "success": True,
            "dias_uteis_mes": dias_uteis,
            "proventos": proventos,
            "descontos": descontos,
            "custos_empresa": custos_empresa,
            "totais": {
                "proventos": total_proventos,
                "descontos": total_descontos,
                "liquido_funcionario": salario_liquido,
                "custo_total_empresa": custo_total_empresa
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}