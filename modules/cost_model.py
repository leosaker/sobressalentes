"""
============================================================
MÓDULO 3: MODELO DE CUSTO
============================================================

OBJETIVO: encontrar a quantidade Q que MINIMIZA o custo total
esperado de manter sobressalentes.

DOIS TIPOS DE CUSTO em conflito:
---------------------------------

1. CUSTO DE MANUTENÇÃO DE ESTOQUE (Ch — holding cost)
   "Custo de ter peças demais"
   → Custo de comprar peças que talvez não sejam usadas
   → Custo de armazenagem, capital imobilizado, obsolescência
   → Fórmula simplificada: Ch = Q × custo_peca × taxa_holding

   taxa_holding típica: 20-30% ao ano do valor da peça

2. CUSTO DE FALTA (Cs — shortage cost)
   "Custo de ter peças de menos"
   → Produção parada esperando a peça chegar
   → Fórmula: Cs = E[falta] × custo_parada_por_hora × lead_time

   E[falta] = número esperado de falhas que excedem o estoque Q

CUSTO TOTAL ESPERADO:
---------------------
  CT(Q) = Ch(Q) + Cs(Q)

O ponto ótimo Q* é onde CT(Q) é mínimo, representando o
EQUILÍBRIO entre o risco de falta e o custo de excesso.
"""

import numpy as np
from modules.reliability import calcular_distribuicao_demanda


def calcular_custo_holding(
    quantidade: int,
    custo_peca: float,
    taxa_holding_anual: float = 0.25,
    horizonte_horas: float = 8760,
) -> float:
    """
    Custo de manter Q peças em estoque durante o horizonte.

    FÓRMULA:
    --------
    Ch = Q × custo_peça × taxa_holding × (horizonte / 8760)

    A taxa_holding representa o custo anual de manter 1 unidade
    monetária imobilizada em estoque (inclui capital, armazenagem,
    obsolescência, seguros).

    Valor típico: 20-30% ao ano.

    O fator (horizonte/8760) ajusta para o período de planejamento:
    se o horizonte é 6 meses (4380h), pagamos metade do custo anual.

    Parâmetros:
    -----------
    quantidade         : Q (peças em estoque)
    custo_peca         : valor unitário da peça (R$)
    taxa_holding_anual : fração do custo da peça por ano (ex: 0.25 = 25%)
    horizonte_horas    : duração do horizonte de planejamento (horas)
    """
    fator_periodo = horizonte_horas / 8760  # normaliza para anos
    return quantidade * custo_peca * taxa_holding_anual * fator_periodo


def calcular_custo_falta(
    quantidade: int,
    distribuicao: dict,
    custo_parada_hora: float,
    lead_time_horas: float,
) -> float:
    """
    Custo ESPERADO de falta de peças para um dado estoque Q.

    COMO CALCULAR:
    --------------
    Falta ocorre quando a demanda D > Q (mais falhas do que temos peças)
    Quando isso acontece, ficamos SEM a peça durante o lead_time inteiro.

    E[Custo de falta] = Σ P(D=k) × max(0, k-Q) × custo_parada_hora × lead_time
                        k=0 até inf

    Onde:
      P(D=k)             = probabilidade de exatamente k falhas (Poisson)
      max(0, k-Q)        = número de falhas sem cobertura (falta líquida)
      custo_parada × LT  = custo total de uma falta (parado durante o LT)

    Intuição:
      Se Q=2 e ocorrem 4 falhas, temos falta de 2 peças.
      Cada falta significa esperar o lead_time sem o equipamento.

    Parâmetros:
    -----------
    quantidade       : Q (estoque disponível)
    distribuicao     : saída de calcular_distribuicao_demanda()
    custo_parada_hora: custo de produção parada por hora (R$/h)
    lead_time_horas  : tempo de espera pelo fornecedor (horas)
    """
    quantidades = distribuicao["quantidades"]
    prob_exata = distribuicao["prob_exata"]

    custo_total_falta = 0
    for k, p in zip(quantidades, prob_exata):
        falta_liquida = max(0, k - quantidade)
        custo_evento = falta_liquida * custo_parada_hora * lead_time_horas
        custo_total_falta += p * custo_evento

    return round(custo_total_falta, 2)


def otimizar_quantidade(
    distribuicao: dict,
    custo_peca: float,
    custo_parada_hora: float,
    lead_time_horas: float,
    horizonte_horas: float,
    taxa_holding_anual: float = 0.25,
    q_max: int = 15,
) -> dict:
    """
    Calcula o custo total para cada quantidade Q e encontra o ótimo.

    ALGORITMO:
    ----------
    Para Q = 0, 1, 2, ..., q_max:
      1. Calcule Ch(Q) — custo de manutenção de estoque
      2. Calcule Cs(Q) — custo esperado de falta
      3. CT(Q) = Ch(Q) + Cs(Q)

    Q* = argmin CT(Q)

    Retorna:
    --------
    dict com:
      'resultados'       : tabela completa Q × custos
      'q_otimo'          : quantidade que minimiza custo total
      'custo_total_otimo': custo mínimo esperado (R$)
      'detalhes'         : métricas adicionais no ponto ótimo
    """
    resultados = []

    for q in range(q_max + 1):
        ch = calcular_custo_holding(q, custo_peca, taxa_holding_anual, horizonte_horas)
        cs = calcular_custo_falta(q, distribuicao, custo_parada_hora, lead_time_horas)
        ct = ch + cs

        resultados.append({
            "quantidade": q,
            "custo_holding": round(ch, 2),
            "custo_falta": round(cs, 2),
            "custo_total": round(ct, 2),
        })

    # Encontra o índice com menor custo total
    custos_totais = [r["custo_total"] for r in resultados]
    idx_otimo = int(np.argmin(custos_totais))
    q_otimo = resultados[idx_otimo]["quantidade"]

    # Nível de serviço no ponto ótimo
    nivel_servico_otimo = distribuicao["prob_acumulada"][
        min(q_otimo, len(distribuicao["prob_acumulada"]) - 1)
    ]

    return {
        "resultados": resultados,
        "q_otimo": q_otimo,
        "custo_total_otimo": resultados[idx_otimo]["custo_total"],
        "custo_holding_otimo": resultados[idx_otimo]["custo_holding"],
        "custo_falta_otimo": resultados[idx_otimo]["custo_falta"],
        "nivel_servico_otimo": round(nivel_servico_otimo * 100, 1),
    }
