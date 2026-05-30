"""
============================================================
MÓDULO 4: OTIMIZADOR — COMBINANDO AS DUAS ABORDAGENS
============================================================

ESTRATÉGIA DE COMBINAÇÃO:
--------------------------
Temos dois critérios para definir Q:

  Q_confiabilidade → menor Q que atinge o nível de serviço alvo
                     (abordagem conservadora: garante disponibilidade)

  Q_custo          → Q que minimiza o custo total esperado
                     (abordagem econômica: minimiza gasto)

DECISÃO FINAL:
--------------
  Q_recomendado = max(Q_confiabilidade, Q_custo)

Por quê o máximo?
  → Q_custo pode sugerir 0 peças se o componente raramente falha,
    mas isso pode ser inaceitável operacionalmente.
  → Q_confiabilidade garante um piso mínimo de disponibilidade.
  → O máximo dos dois satisfaz AMBOS os critérios simultaneamente.

Em algumas situações você pode preferir o mínimo (política mais
econômica) ou deixar o engenheiro decidir com base no contexto.
"""

import pandas as pd
from modules.weibull_analysis import ajustar_weibull
from modules.reliability import (
    calcular_falhas_esperadas,
    calcular_distribuicao_demanda,
    quantidade_por_nivel_servico,
)
from modules.cost_model import otimizar_quantidade


def analisar_componente(
    nome: str,
    tempos_falha: list,
    custo_peca: float,
    custo_parada_hora: float,
    lead_time_horas: float,
    horizonte_horas: float,
    nivel_servico_alvo: float = 0.95,
    taxa_holding_anual: float = 0.25,
) -> dict:
    """
    Executa a análise COMPLETA para um único componente.

    PIPELINE:
    ---------
    1. Ajusta Weibull aos tempos de falha → β, η, MTTF
    2. Calcula falhas esperadas no horizonte → λ
    3. Monta distribuição de probabilidade da demanda → P(D=k)
    4. Abordagem 1 (confiabilidade): Q para nível de serviço alvo
    5. Abordagem 2 (custo): Q que minimiza custo total
    6. Combina: Q_final = max(Q1, Q2)

    Parâmetros:
    -----------
    nome              : nome do componente
    tempos_falha      : lista de tempos até a falha (horas)
    custo_peca        : valor de compra da peça (R$)
    custo_parada_hora : custo de produção parada por hora (R$/h)
    lead_time_horas   : tempo para receber a peça do fornecedor
    horizonte_horas   : período de planejamento (geralmente 8760h = 1 ano)
    nivel_servico_alvo: probabilidade de não ter falta (ex: 0.95)
    taxa_holding_anual: custo anual de manter estoque (fração do valor)

    Retorna:
    --------
    dict com todos os resultados intermediários e finais
    """

    # ── PASSO 1: Ajuste Weibull ────────────────────────────────────────
    weibull = ajustar_weibull(tempos_falha)
    beta = weibull["beta"]
    eta = weibull["eta"]

    # ── PASSO 2: Demanda esperada ──────────────────────────────────────
    lambda_demanda = calcular_falhas_esperadas(beta, eta, horizonte_horas, lead_time_horas)

    # ── PASSO 3: Distribuição de probabilidade ─────────────────────────
    distribuicao = calcular_distribuicao_demanda(lambda_demanda, q_max=15)

    # ── PASSO 4: Abordagem por Confiabilidade ──────────────────────────
    q_confiabilidade = quantidade_por_nivel_servico(distribuicao, nivel_servico_alvo)

    # ── PASSO 5: Abordagem por Custo ───────────────────────────────────
    resultado_custo = otimizar_quantidade(
        distribuicao=distribuicao,
        custo_peca=custo_peca,
        custo_parada_hora=custo_parada_hora,
        lead_time_horas=lead_time_horas,
        horizonte_horas=horizonte_horas,
        taxa_holding_anual=taxa_holding_anual,
    )
    q_custo = resultado_custo["q_otimo"]

    # ── PASSO 6: Decisão final ─────────────────────────────────────────
    q_final = max(q_confiabilidade, q_custo)

    # Nível de serviço real com a quantidade final
    nivel_servico_real = distribuicao["prob_acumulada"][
        min(q_final, len(distribuicao["prob_acumulada"]) - 1)
    ]

    return {
        "nome": nome,
        # Weibull
        "beta": beta,
        "eta": eta,
        "mttf": weibull["mttf"],
        "padrao_falha": weibull["padrao_falha"],
        "n_amostras": weibull["n_amostras"],
        # Demanda
        "lambda_demanda": lambda_demanda,
        "distribuicao": distribuicao,
        # Abordagem confiabilidade
        "q_confiabilidade": q_confiabilidade,
        "nivel_servico_alvo": nivel_servico_alvo,
        # Abordagem custo
        "q_custo": q_custo,
        "resultado_custo": resultado_custo,
        # Decisão final
        "q_recomendado": q_final,
        "nivel_servico_real": round(nivel_servico_real * 100, 1),
        # Parâmetros de entrada (para referência)
        "custo_peca": custo_peca,
        "custo_parada_hora": custo_parada_hora,
        "lead_time_horas": lead_time_horas,
        "horizonte_horas": horizonte_horas,
    }


def analisar_todos_componentes(
    df: pd.DataFrame,
    nivel_servico: float = 0.95,
    taxa_holding_anual: float = 0.25,
) -> list:
    """
    Processa todos os componentes do DataFrame de falhas.

    Agrupa os dados por componente e chama analisar_componente()
    para cada um, retornando uma lista de resultados.

    Parâmetros:
    -----------
    df                 : DataFrame com colunas do arquivo failures.csv
    nivel_servico      : nível de serviço alvo (aplicado a todos)
    taxa_holding_anual : custo anual de manter estoque (fração do valor da peça)

    Retorna:
    --------
    list de dicts (um por componente)
    """
    resultados = []

    for componente, grupo in df.groupby("componente"):
        tempos = grupo["tempo_falha_horas"].tolist()
        # Pega os parâmetros de custo da primeira linha do grupo
        # (assumimos que são iguais para todas as linhas do mesmo componente)
        params = grupo.iloc[0]

        resultado = analisar_componente(
            nome=componente,
            tempos_falha=tempos,
            custo_peca=float(params["custo_peca"]),
            custo_parada_hora=float(params["custo_falta_hora"]),
            lead_time_horas=float(params["lead_time_horas"]),
            horizonte_horas=float(params["horizonte_planejamento_horas"]),
            nivel_servico_alvo=nivel_servico,
            taxa_holding_anual=taxa_holding_anual,
        )
        resultados.append(resultado)

    return resultados


def gerar_tabela_resumo(resultados: list) -> pd.DataFrame:
    """
    Gera uma tabela resumida com os principais resultados por componente.

    Útil para exportar para Excel ou exibir no dashboard.
    """
    linhas = []
    for r in resultados:
        linhas.append({
            "Componente": r["nome"],
            "β (forma)": r["beta"],
            "η - Vida Caract. (h)": r["eta"],
            "MTTF (h)": r["mttf"],
            "Padrão de Falha": r["padrao_falha"].split(" — ")[0],
            "λ Demanda Esperada": round(r["lambda_demanda"], 3),
            "Q (Confiabilidade)": r["q_confiabilidade"],
            "Q (Custo Ótimo)": r["q_custo"],
            "Q RECOMENDADO": r["q_recomendado"],
            "Nível de Serviço (%)": r["nivel_servico_real"],
            "Custo Total Esperado (R$)": r["resultado_custo"]["custo_total_otimo"],
        })
    return pd.DataFrame(linhas)
