# ⚙️ Gestão de Sobressalentes — Modelo Python

Modelo didático para dimensionamento de estoque de sobressalentes em plantas industriais,
combinando **Análise de Confiabilidade (Weibull)** e **Otimização de Custo**.

---

## 📁 Estrutura do Projeto

```
spare_parts_model/
│
├── data/
│   └── failures.csv          # Dados de falha (edite com seus dados reais)
│
├── modules/
│   ├── weibull_analysis.py   # MÓDULO 1: Ajuste Weibull, R(t), h(t)
│   ├── reliability.py        # MÓDULO 2: Demanda esperada, distribuição Poisson
│   ├── cost_model.py         # MÓDULO 3: Custo holding, custo falta, otimização
│   └── optimizer.py          # MÓDULO 4: Combina abordagens, gera resumo
│
├── app.py                    # Dashboard Streamlit
├── requirements.txt
└── README.md
```

---

## 🚀 Como Executar

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Rodar o dashboard
```bash
streamlit run app.py
```

---

## 📊 Como Funciona o Modelo

### Fluxo completo:

```
Dados de falha (tempos em horas)
           ↓
[1] Ajuste Weibull (scipy MLE)
    → β (forma) e η (escala)
           ↓
[2] Demanda esperada no horizonte
    λ = ((horizonte + lead_time) / η)^β
           ↓
[3] Distribuição de Poisson P(D = k)
    → probabilidade de k falhas ocorrerem
           ↓
    ┌──────────────────────────────────┐
    │                                  │
[4a] Q por Confiabilidade         [4b] Q por Custo
     menor Q tal que                   argmin CT(Q)
     P(D ≤ Q) ≥ NS_alvo               CT = Ch + Cs
    │                                  │
    └─────────────┬────────────────────┘
                  ↓
    Q_recomendado = max(Q_confiab, Q_custo)
```

### Os dois critérios explicados:

| Critério | Pergunta | Método |
|---|---|---|
| **Confiabilidade** | "Qual o menor estoque que garante X% de não faltar?" | Poisson CDF ≥ NS_alvo |
| **Custo** | "Qual estoque minimiza o gasto total esperado?" | argmin(Ch + Cs) |

---

## 📋 Formato do CSV de Entrada

```csv
componente,tempo_falha_horas,custo_peca,custo_falta_hora,lead_time_horas,horizonte_planejamento_horas
Bomba A,1200,3500,800,72,8760
Bomba A,1450,3500,800,72,8760
...
```

**Campos obrigatórios:**
- `componente`: nome do componente
- `tempo_falha_horas`: tempo até a falha (horas)
- `custo_peca`: valor de compra da peça (R$)
- `custo_falta_hora`: custo de produção parada por hora (R$/h)
- `lead_time_horas`: tempo para receber a peça do fornecedor
- `horizonte_planejamento_horas`: período de análise (8760 = 1 ano)

> ⚠️ Mínimo recomendado: **6-8 falhas** por componente para ajuste Weibull confiável.

---

## 🔧 Parâmetros Ajustáveis no Dashboard

| Parâmetro | Padrão | Descrição |
|---|---|---|
| Nível de Serviço | 95% | Probabilidade de não ter falta |
| Taxa de Manutenção | 25% a.a. | Custo anual de manter 1 peça em estoque |

---

## 📚 Conceitos-Chave

### β (beta) — Parâmetro de Forma
| Valor | Padrão | Ação recomendada |
|---|---|---|
| β < 1 | Mortalidade infantil | Revisar instalação/processo |
| β = 1 | Falhas aleatórias | Manutenção corretiva planejada |
| β > 1 | Desgaste | Substituição preventiva |

### η (eta) — Vida Característica
Tempo em que 63,2% dos componentes já falharam.
Relaciona-se com o MTTF por: `MTTF = η × Γ(1 + 1/β)`

### Distribuição de Poisson
Usada para modelar o número de falhas em um período.
Válida quando falhas são eventos raros e aproximadamente independentes.

---

## 🔄 Próximas Evoluções Sugeridas

- [ ] Ponto de reposição (quando pedir, não só quanto)
- [ ] Análise de sensibilidade (variação de custo_falta)
- [ ] Dados censurados (componentes que ainda não falharam)
- [ ] Múltiplos fornecedores com lead times distintos
- [ ] Exportação para Excel formatado
