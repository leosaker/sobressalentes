"""
============================================================
MÓDULO 1: ANÁLISE DE WEIBULL
============================================================

O que é a distribuição de Weibull?
------------------------------------
A distribuição de Weibull é a mais usada em confiabilidade porque
é FLEXÍVEL: dependendo do parâmetro β (beta), ela representa
diferentes padrões de falha:

  β < 1  → Falhas precoces (mortalidade infantil)
            Ex: defeitos de fabricação
  β = 1  → Falhas aleatórias (taxa constante = exponencial)
            Ex: falhas por eventos externos
  β > 1  → Falhas por desgaste (vida útil se esgota)
            Ex: rolamentos, selos mecânicos

Dois parâmetros principais:
  β (beta)  = Parâmetro de forma  → "como" as falhas ocorrem
  η (eta)   = Parâmetro de escala → "quando" tipicamente ocorrem
                                     (vida característica: 63,2% falhou)
"""

import numpy as np
from scipy import stats
from scipy.special import gamma as gamma_func


def ajustar_weibull(tempos_falha: list) -> dict:
    """
    Ajusta a distribuição de Weibull a um conjunto de tempos de falha.

    COMO FUNCIONA:
    --------------
    A scipy usa a parametrização: f(x) = (c/scale) * (x/scale)^(c-1) * exp(-(x/scale)^c)
    onde:
      c     = β (parâmetro de forma)
      scale = η (parâmetro de escala / vida característica)
      loc   = parâmetro de localização (fixado em 0 para Weibull de 2 parâmetros)

    O ajuste é feito por Máxima Verossimilhança (MLE), que encontra os
    parâmetros que maximizam a probabilidade de observar os dados fornecidos.

    Parâmetros:
    -----------
    tempos_falha : list
        Lista de tempos até a falha (em horas)

    Retorna:
    --------
    dict com β, η, MTTF e interpretação do padrão de falha
    """
    tempos = np.array(tempos_falha)

    # scipy.stats.weibull_min faz o ajuste MLE automaticamente
    # floc=0 fixa o parâmetro de localização em zero (Weibull de 2 parâmetros)
    forma, loc, escala = stats.weibull_min.fit(tempos, floc=0)

    beta = forma   # parâmetro de forma
    eta = escala   # parâmetro de escala (vida característica)

    # MTTF = Tempo Médio até a Falha
    # Fórmula: MTTF = η × Γ(1 + 1/β)
    # onde Γ é a função Gamma
    mttf = eta * gamma_func(1 + 1 / beta)

    # Interpretação automática do padrão de falha
    if beta < 0.95:
        padrao = "Mortalidade Infantil (falhas precoces) — revisar processo de instalação/fabricação"
    elif beta <= 1.05:
        padrao = "Falhas Aleatórias (taxa constante) — eventos externos ou causas aleatórias"
    elif beta <= 3.0:
        padrao = "Desgaste Normal — componente com vida útil definida"
    else:
        padrao = "Desgaste Acentuado — componente envelhece rapidamente"

    return {
        "beta": round(beta, 4),
        "eta": round(eta, 2),
        "mttf": round(mttf, 2),
        "padrao_falha": padrao,
        "n_amostras": len(tempos),
    }


def calcular_confiabilidade(t: float, beta: float, eta: float) -> float:
    """
    Calcula R(t): probabilidade de o componente SOBREVIVER até o tempo t.

    FÓRMULA:
    --------
    R(t) = exp( -(t/η)^β )

    Interpretação:
      R(1000) = 0.85 → há 85% de chance de o componente ainda estar
                        funcionando após 1000 horas de operação

    Parâmetros:
    -----------
    t    : tempo de interesse (horas)
    beta : parâmetro de forma
    eta  : parâmetro de escala

    Retorna:
    --------
    float: probabilidade de sobrevivência (0 a 1)
    """
    return np.exp(-((t / eta) ** beta))


def calcular_taxa_falha(t: float, beta: float, eta: float) -> float:
    """
    Calcula h(t): taxa de falha instantânea no tempo t (função hazard).

    FÓRMULA:
    --------
    h(t) = (β/η) × (t/η)^(β-1)

    Interpretação:
      h(1000) = 0.002 → naquele instante, o componente tem 0,2% de chance
                         de falhar por hora

    Quando β > 1, h(t) CRESCE com o tempo → desgaste
    Quando β = 1, h(t) é CONSTANTE → falhas aleatórias
    Quando β < 1, h(t) DECRESCE com o tempo → mortalidade infantil
    """
    return (beta / eta) * ((t / eta) ** (beta - 1))


def gerar_curva_confiabilidade(beta: float, eta: float, n_pontos: int = 200) -> tuple:
    """
    Gera vetores (tempo, confiabilidade) para plotar a curva R(t).

    O range de tempo vai de 0 até 2.5× a vida característica η,
    cobrindo a região onde a maioria das falhas ocorre.

    Retorna:
    --------
    (array de tempos, array de R(t))
    """
    t_max = eta * 2.5
    tempos = np.linspace(0, t_max, n_pontos)
    confiabilidades = np.array([calcular_confiabilidade(t, beta, eta) for t in tempos])
    return tempos, confiabilidades


def gerar_curva_taxa_falha(beta: float, eta: float, n_pontos: int = 200) -> tuple:
    """
    Gera vetores (tempo, taxa_falha) para plotar a curva h(t) (banheira).

    O famoso gráfico da "curva da banheira" é obtido combinando
    três componentes com β < 1, β = 1 e β > 1.
    """
    t_max = eta * 2.0
    # Começa em 0.01 para evitar divisão por zero quando β < 1
    tempos = np.linspace(t_max * 0.01, t_max, n_pontos)
    taxas = np.array([calcular_taxa_falha(t, beta, eta) for t in tempos])
    return tempos, taxas
