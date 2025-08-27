# app/rh/calculos.py

from datetime import date
from decimal import Decimal, ROUND_UP

def calcular_rescisao(salario_bruto, data_admissao, data_demissao, motivo, aviso_previo_indenizado=False, ferias_vencidas=False):
    """
    Calcula os valores de uma rescisão de contrato de trabalho.
    Retorna um dicionário com os resultados.
    """
    try:
        salario = Decimal(salario_bruto)
        dias_trabalhados_no_mes = data_demissao.day
        
        # --- 1. Saldo de Salário ---
        saldo_salario = (salario / Decimal(30)) * Decimal(dias_trabalhados_no_mes)

        # --- 2. Férias Proporcionais + 1/3 ---
        meses_trabalhados_ano = data_demissao.month
        if data_demissao.day >= 15:
            meses_trabalhados_ano += 1
        
        ferias_proporcionais = (salario / Decimal(12)) * Decimal(meses_trabalhados_ano)
        um_terco_ferias = ferias_proporcionais / Decimal(3)

        # --- 3. 13º Salário Proporcional ---
        decimo_terceiro_proporcional = (salario / Decimal(12)) * Decimal(data_demissao.month)

        # --- Itens que dependem do motivo da demissão ---
        aviso_previo_valor = Decimal(0)
        multa_fgts = Decimal(0)

        if motivo == 'demissao_sem_justa_causa':
            if aviso_previo_indenizado:
                aviso_previo_valor = salario
            # Cálculo do FGTS total estimado para a multa (simplificado)
            meses_totais = (data_demissao.year - data_admissao.year) * 12 + data_demissao.month - data_admissao.month
            fgts_depositado_estimado = (salario * Decimal('0.08')) * Decimal(meses_totais)
            multa_fgts = fgts_depositado_estimado * Decimal('0.40')
        
        # --- Férias Vencidas (se aplicável) ---
        ferias_vencidas_valor = Decimal(0)
        um_terco_ferias_vencidas = Decimal(0)
        if ferias_vencidas:
            ferias_vencidas_valor = salario
            um_terco_ferias_vencidas = salario / Decimal(3)

        # --- Consolidação dos resultados ---
        verbas_rescisorias = {
            "saldo_salario": saldo_salario,
            "aviso_previo": aviso_previo_valor,
            "decimo_terceiro_proporcional": decimo_terceiro_proporcional,
            "ferias_proporcionais": ferias_proporcionais,
            "um_terco_ferias": um_terco_ferias,
            "ferias_vencidas": ferias_vencidas_valor,
            "um_terco_ferias_vencidas": um_terco_ferias_vencidas,
        }
        
        total_bruto = sum(verbas_rescisorias.values())

        # --- Simulação de Descontos (INSS e IRRF sobre saldo de salário e 13º) ---
        salario_base_inss = saldo_salario + decimo_terceiro_proporcional
        # Tabela INSS 2025 (simulada)
        if salario_base_inss <= 1500:
            inss = salario_base_inss * Decimal('0.075')
        elif salario_base_inss <= 2800:
            inss = salario_base_inss * Decimal('0.09')
        else:
            inss = salario_base_inss * Decimal('0.12')
        
        # Simples IRRF
        irrf = (total_bruto - inss) * Decimal('0.05') if (total_bruto - inss) > 2500 else Decimal(0)

        total_descontos = inss + irrf
        total_liquido = total_bruto - total_descontos

        return {
            "success": True,
            "verbas": verbas_rescisorias,
            "multa_fgts": multa_fgts,
            "descontos": {"inss": inss, "irrf": irrf},
            "totais": {
                "bruto": total_bruto,
                "descontos": total_descontos,
                "liquido": total_liquido
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def calcular_folha_pagamento(salario_bruto, dias_uteis=22, valor_diario_vt=0, valor_mensal_va=0):
    """
    Calcula uma simulação da folha de pagamento mensal de um funcionário.
    """
    try:
        salario = Decimal(salario_bruto)
        
        # --- BENEFÍCIOS (PROVENTOS) ---
        proventos = {
            "salario_base": salario
        }

        # --- DESCONTOS ---
        descontos = {}

        # 1. Vale-Transporte (VT)
        valor_total_vt = Decimal(valor_diario_vt) * Decimal(dias_uteis)
        desconto_max_vt = salario * Decimal('0.06')
        desconto_vt = min(valor_total_vt, desconto_max_vt)
        descontos['vale_transporte'] = desconto_vt

        # 2. Vale-Alimentação/Refeição (VA)
        desconto_va = Decimal(valor_mensal_va) * Decimal('0.01')
        descontos['vale_alimentacao'] = desconto_va

        # 3. INSS (Tabela simulada 2025)
        if salario <= 1500:
            inss = salario * Decimal('0.075')
        elif salario <= 2800:
            inss = salario * Decimal('0.09')
        elif salario <= 4200:
            inss = salario * Decimal('0.12')
        else:
            inss = salario * Decimal('0.14')
        descontos['inss'] = inss

        # 4. IRRF (Imposto de Renda Retido na Fonte)
        base_calculo_irrf = salario - inss
        if base_calculo_irrf <= 2259.20:
            irrf = Decimal(0)
        elif base_calculo_irrf <= 2826.65:
            irrf = (base_calculo_irrf * Decimal('0.075')) - Decimal('169.44')
        else:
            irrf = (base_calculo_irrf * Decimal('0.15')) - Decimal('381.44')
        descontos['irrf'] = max(Decimal(0), irrf)

        # 5. FGTS (Não é descontado do funcionário, é um depósito da empresa)
        fgts_deposito = salario * Decimal('0.08')

        # --- TOTAIS ---
        total_proventos = sum(proventos.values())
        total_descontos = sum(descontos.values())
        salario_liquido = total_proventos - total_descontos

        return {
            "success": True,
            "proventos": proventos,
            "descontos": descontos,
            "fgts_deposito_mes": fgts_deposito,
            "totais": {
                "proventos": total_proventos,
                "descontos": total_descontos,
                "liquido": salario_liquido
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}