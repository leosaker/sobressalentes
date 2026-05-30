"""
============================================================
MÓDULO 2: DEMANDA ESPERADA DE SOBRESSALENTES
============================================================

A pergunta central deste módulo:
"Quantas falhas (e portanto, quantas peças) eu devo esperar
 durante o período de lead time + horizonte de planejamento?"

CONCEITO-CHAVE: Processo de Poisson Não-Homogêneo
---------------------------------------------------
Quando temos uma distribuição de Weibull, o número esperado de
falhas em um intervalo [0, T] é dado pela função de valor médio
(Mean Value Function) do processo de renovação:

  H(T) ≈ (T/η)^β    [aproximação via Weibull]

Para o estoque de sobressalentes, precisamos saber quantas
falhas esperar durante o "tempo de exposição ao risco":
  T_exposição = lead_time + horizonte_planejamento

Depois, usamos a distribuição de Poisson para calcular a
probabilidade de ocorrer exatamente k falhas nesse período.
"""

import numpy as np
from scipy.stats import poisson
from modules.weibull_analysis import calcular_confiabilidade


def calcular_falhas_esperadas(
    beta: float,
    eta: float,
    horizonte: float,
    lead_time: float,
) -> float:
    """
    Estima o número ESPERADO de falhas durante o período de exposição.

    PERÍODO DE EXPOSIÇÃO = lead_time + horizonte_planejamento
    -------------------------------------------------------
    Por quê somar lead_time?
    Porque quando uma peça falha e você faz o pedido, você fica
    SEM estoque durante todo o lead_time. Portanto, você precisa
    cobrir as falhas que podem ocorrer DURANTE esse período também.

    FÓRMULA (aproximação Weibull para processo de renovação):
    ---------------------------------------------------------
    E[N(T)] = (T / η)^β

    Esta é uma aproximação conservadora. Para β = 1 (exponencial),
    ela é exata.

    Parâmetros:
    -----------
    beta      : parâmetro de forma Weibull
    eta       : parâmetro de escala Weibull (horas)
    horizonte : período de planejamento (horas)
    lead_time : tempo de reposição do fornecedor (horas)

    Retorna:
    --------
    float: número esperado de falhas
    """
    T = horizonte + lead_time
    falhas_esperadas = (T / eta) ** beta
    return round(falhas_esperadas, 4)


def calcular_distribuicao_demanda(
    falhas_esperadas: float,
    q_max: int = 15
) -> dict:
    """
    Calcula a distribuição de probabilidade do número de falhas.

    MODELO: Distribuição de Poisson
    --------------------------------
    Aproximamos o número de falhas por uma distribuição de Poisson
    com parâmetro λ = falhas_esperadas.

    P(N = k) = (λ^k × e^(-λ)) / k!

    Esta aproximação é razoável quando:
      - As falhas são eventos raros em relação ao horizonte
      - As falhas são (aproximadamente) independentes

    Parâmetros:
    -----------
    falhas_esperadas : λ (parâmetro da Poisson)
    q_max            : quantidade máxima a considerar no cálculo

    Retorna:
    --------
    dict:
      'quantidades'    : [0, 1, 2, ..., q_max]
      'prob_exata'     : P(N = k) para cada k
      'prob_acumulada' : P(N ≤ k) para cada k  ← nível de serviço
    """
    quantidades = list(range(q_max + 1))

    # P(N = k): probabilidade de exactamente k falhas
    prob_exata = [poisson.pmf(k, falhas_esperadas) for k in quantidades]

    # P(N ≤ k): probabilidade de NO MÁXIMO k falhas
    # = nível de serviço se tivermos k peças em estoque
    prob_acumulada = [poisson.cdf(k, falhas_esperadas) for k in quantidades]

    return {
        "quantidades": quantidades,
        "prob_exata": [round(p, 6) for p in prob_exata],
        "prob_acumulada": [round(p, 6) for p in prob_acumulada],
        "lambda": round(falhas_esperadas, 4),
    }


def quantidade_por_nivel_servico(
    distribuicao: dict,
    nivel_servico_alvo: float = 0.95
) -> int:
    """
    Encontra a menor quantidade Q que atinge o nível de serviço alvo.

    NÍVEL DE SERVIÇO
    ----------------
    Nível de serviço = P(demanda ≤ Q) = probabilidade de NÃO ter falta
    de peças durante o período de planejamento.

    Exemplo:
      nivel_servico_alvo = 0.95 → queremos 95% de chance de não faltar peça

    O algoritmo percorre as quantidades em ordem crescente e retorna
    a PRIMEIRA que atinge ou supera o nível de serviço desejado.

    Parâmetros:
    -----------
    distribuicao        : saída de calcular_distribuicao_demanda()
    nivel_servico_alvo  : float entre 0 e 1 (ex: 0.95 = 95%)

    Retorna:
    --------
    int: quantidade mínima recomendada
    """
    quantidades = distribuicao["quantidades"]
    prob_acumulada = distribuicao["prob_acumulada"]

    for q, p in zip(quantidades, prob_acumulada):
        if p >= nivel_servico_alvo:
            return q

    # Se nenhuma quantidade na lista atingir o nível, retorna o máximo
    return quantidades[-1]
