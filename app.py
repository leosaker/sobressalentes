"""
============================================================
APP.PY — DASHBOARD STREAMLIT
Gestão de Sobressalentes com Análise de Confiabilidade
============================================================

Como executar:
  streamlit run app.py

Estrutura do dashboard:
  Sidebar    → controles e parâmetros globais
  Aba 1      → Análise Weibull (curvas e parâmetros)
  Aba 2      → Demanda & Probabilidades (distribuição Poisson)
  Aba 3      → Modelo de Custo (gráfico de otimização)
  Aba 4      → Recomendação Final (tabela consolidada)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from modules.weibull_analysis import (
    ajustar_weibull,
    gerar_curva_confiabilidade,
    gerar_curva_taxa_falha,
)
from modules.optimizer import analisar_todos_componentes, gerar_tabela_resumo

# ─────────────────────────────────────────────
# CONFIGURAÇÃO DA PÁGINA
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Gestão de Sobressalentes",
    page_icon="⚙️",
    layout="wide",
)

# ─────────────────────────────────────────────
# ESTILOS CUSTOMIZADOS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: #1e2130;
        border: 1px solid #2d3250;
        border-radius: 10px;
        padding: 16px 20px;
        margin: 6px 0;
    }
    .metric-label { color: #8892b0; font-size: 0.82rem; margin-bottom: 4px; }
    .metric-value { color: #e6f1ff; font-size: 1.6rem; font-weight: 700; }
    .metric-sub   { color: #64ffda; font-size: 0.78rem; margin-top: 4px; }
    .explain-box {
        background: #0d1117;
        border-left: 3px solid #64ffda;
        border-radius: 4px;
        padding: 12px 16px;
        margin: 10px 0;
        font-size: 0.88rem;
        color: #ccd6f6;
    }
    .formula-box {
        background: #161b22;
        border: 1px dashed #30363d;
        border-radius: 6px;
        padding: 10px 14px;
        font-family: monospace;
        font-size: 0.85rem;
        color: #79c0ff;
        margin: 8px 0;
    }
    h1, h2, h3 { color: #1e293b !important; }
    .stTabs [data-baseweb="tab"] { color: #8892b0; font-size: 0.95rem; }
    .stTabs [aria-selected="true"] { color: #64ffda !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.title("⚙️ Gestão de Sobressalentes")
st.markdown("**Modelo baseado em Análise de Confiabilidade (Weibull) + Otimização de Custo**")
st.divider()


# ─────────────────────────────────────────────
# SIDEBAR — CONTROLES
# ─────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Parâmetros Globais")

    uploaded = st.file_uploader("📂 Carregar arquivo CSV", type=["csv"])

    st.subheader("Configurações do Modelo")
    nivel_servico = st.slider(
        "Nível de Serviço Alvo (%)",
        min_value=80, max_value=99, value=95, step=1,
        help="Probabilidade de não ter falta de peça durante o horizonte"
    ) / 100

    taxa_holding = st.slider(
        "Taxa de Manutenção de Estoque (% a.a.)",
        min_value=10, max_value=40, value=25, step=5,
        help="Custo anual de manter 1 peça em estoque (% do valor da peça)"
    ) / 100

    st.divider()
    st.markdown("""
    **Legenda β (Weibull):**
    - `β < 1` → Mortalidade infantil
    - `β = 1` → Falhas aleatórias
    - `β > 1` → Desgaste
    """)


# ─────────────────────────────────────────────
# CARREGAMENTO DOS DADOS
# ─────────────────────────────────────────────
@st.cache_data
def carregar_dados(fonte):
    return pd.read_csv(fonte)

if uploaded:
    df = carregar_dados(uploaded)
else:
    df = carregar_dados("data/failures.csv")
    st.info("📋 Usando dados de exemplo. Carregue seu próprio CSV na barra lateral.")

with st.expander("📄 Ver dados carregados"):
    st.dataframe(df, use_container_width=True)
    st.caption(f"{len(df)} linhas · {len(df.columns)} colunas — {', '.join(df.columns.tolist())}")


# ─────────────────────────────────────────────
# PROCESSAMENTO
# ─────────────────────────────────────────────
with st.spinner("Calculando análise de confiabilidade..."):
    resultados = analisar_todos_componentes(df, nivel_servico, taxa_holding)
    tabela_resumo = gerar_tabela_resumo(resultados)

componentes = [r["nome"] for r in resultados]
componente_sel = st.selectbox("🔍 Selecionar Componente para Análise Detalhada", componentes)
res = next(r for r in resultados if r["nome"] == componente_sel)


# ─────────────────────────────────────────────
# ABAS PRINCIPAIS
# ─────────────────────────────────────────────
aba1, aba2, aba3, aba4, aba5 = st.tabs([
    "📈 Análise Weibull",
    "📊 Demanda & Probabilidades",
    "💰 Modelo de Custo",
    "✅ Recomendação Final",
    "📚 Metodologia",
])


# ════════════════════════════════════════════════════════════
# ABA 1: ANÁLISE WEIBULL
# ════════════════════════════════════════════════════════════
with aba1:
    st.subheader(f"Análise de Confiabilidade — {componente_sel}")

    st.markdown(f"""
    <div class="explain-box">
    <b>O que estamos fazendo aqui?</b><br>
    Ajustamos a <b>distribuição de Weibull</b> aos {res['n_amostras']} tempos de falha registrados
    para este componente. O ajuste nos dá os parâmetros β e η, que descrevem
    matematicamente como este componente falha ao longo do tempo.
    </div>
    """, unsafe_allow_html=True)

    # ── Métricas ────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(
            "β — Parâmetro de Forma", res['beta'],
            delta="▲ Desgaste" if res['beta'] > 1.05 else ("→ Aleatório" if res['beta'] >= 0.95 else "▼ Mortalidade Infantil"),
            help=(
                "Controla o **formato** da curva de falha.\n\n"
                "- **β < 1** → Mortalidade infantil: componente falha mais cedo; "
                "taxa de falha decresce com o tempo. Revisar processo de instalação.\n"
                "- **β ≈ 1** → Falhas aleatórias: taxa constante, independe da idade. "
                "Causas externas ou eventos imprevisíveis.\n"
                "- **β > 1** → Desgaste: componente envelhece; "
                "taxa de falha cresce com o tempo. Há vida útil definida."
            ),
        )
    with c2:
        st.metric(
            "η — Vida Característica (h)", f"{res['eta']:,.0f}",
            help=(
                "Parâmetro de **escala** da Weibull, em horas.\n\n"
                "Representa o tempo no qual **63,2 % dos componentes já falharam**. "
                "Esse valor é independente de β e serve como referência temporal: "
                "quanto maior η, mais durável o componente."
            ),
        )
    with c3:
        st.metric(
            "MTTF (h)", f"{res['mttf']:,.0f}",
            help=(
                "**Mean Time To Failure** — Tempo Médio até a Falha.\n\n"
                "É a média da distribuição de Weibull, calculada por:\n"
                "MTTF = η × Γ(1 + 1/β)\n\n"
                "Interprete como: em média, um componente deste tipo dura esse número de horas "
                "antes de falhar. Diferente de η, leva em conta a assimetria da distribuição."
            ),
        )
    with c4:
        st.metric(
            "Amostras", res['n_amostras'],
            help=(
                "Número de **registros de falha** usados para ajustar a distribuição.\n\n"
                "Quanto mais amostras, mais confiáveis são os parâmetros β e η estimados. "
                "Com menos de ~5 amostras, os resultados devem ser interpretados com cautela."
            ),
        )

    st.markdown(f"""
    <div class="explain-box">
    <b>Interpretação:</b> {res['padrao_falha']}
    </div>
    """, unsafe_allow_html=True)

    # ── Curvas R(t) e h(t) ──────────────────────────────────
    tempos_rt, rt = gerar_curva_confiabilidade(res['beta'], res['eta'])
    tempos_ht, ht = gerar_curva_taxa_falha(res['beta'], res['eta'])

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=["R(t) — Função de Confiabilidade", "h(t) — Taxa de Falha (Hazard)"],
    )

    # Curva R(t)
    fig.add_trace(go.Scatter(
        x=tempos_rt, y=rt * 100,
        mode="lines", name="R(t)",
        line=dict(color="#64ffda", width=2.5),
        fill="tozeroy", fillcolor="rgba(100,255,218,0.07)",
    ), row=1, col=1)

    # Linha de referência MTTF
    r_mttf = np.exp(-((res['mttf'] / res['eta']) ** res['beta'])) * 100
    fig.add_vline(x=res['mttf'], line_dash="dash", line_color="#ff6b6b",
                  annotation_text=f"MTTF={res['mttf']:,.0f}h", row=1, col=1)

    # Curva h(t)
    fig.add_trace(go.Scatter(
        x=tempos_ht, y=ht * 1000,  # × 1000 para mostrar em falhas/1000h
        mode="lines", name="h(t) × 1000",
        line=dict(color="#ffd700", width=2.5),
    ), row=1, col=2)

    fig.update_layout(
        height=420, template="plotly_dark",
        paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
        showlegend=False, margin=dict(t=50, b=30),
        font=dict(color="#e6f1ff"),
    )
    fig.update_yaxes(title_text="Confiabilidade (%)", row=1, col=1)
    fig.update_yaxes(title_text="Taxa de Falha (×10⁻³ /h)", row=1, col=2)
    fig.update_xaxes(title_text="Tempo (horas)")

    st.plotly_chart(fig, use_container_width=True)

    st.markdown(f"""
    <div class="formula-box">
    R(t) = exp( -(t / η)^β ) = exp( -(t / {res['eta']:,.0f})^{res['beta']} )<br>
    h(t) = (β/η) × (t/η)^(β-1) = ({res['beta']} / {res['eta']:,.0f}) × (t / {res['eta']:,.0f})^{res['beta']-1:.4f}
    </div>
    """, unsafe_allow_html=True)

    # ── Dados brutos ────────────────────────────────────────
    with st.expander("📋 Ver dados de falha utilizados"):
        df_comp = df[df["componente"] == componente_sel][["tempo_falha_horas"]].reset_index(drop=True)
        df_comp.index += 1
        df_comp.columns = ["Tempo até Falha (h)"]
        st.dataframe(df_comp, use_container_width=True)


# ════════════════════════════════════════════════════════════
# ABA 2: DEMANDA & PROBABILIDADES
# ════════════════════════════════════════════════════════════
with aba2:
    st.subheader(f"Distribuição de Demanda — {componente_sel}")

    st.markdown(f"""
    <div class="explain-box">
    <b>O que estamos fazendo aqui?</b><br>
    Usando os parâmetros Weibull, estimamos quantas falhas (= quantas peças) devemos esperar
    durante o horizonte de planejamento + lead time. Modelamos isso com uma
    <b>distribuição de Poisson</b> (λ = {res['lambda_demanda']:.3f} falhas esperadas).
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b = st.columns([1, 2])

    with col_a:
        st.metric(
            "λ — Falhas Esperadas", f"{res['lambda_demanda']:.3f}",
            help=(
                "Número **esperado de falhas** (= peças demandadas) durante o período de exposição "
                "(horizonte + lead time).\n\n"
                "Calculado pela aproximação do processo de renovação Weibull:\n"
                "λ = (T / η)^β\n\n"
                "É o parâmetro da distribuição de Poisson usada para modelar a demanda. "
                "λ alto → componente falha com frequência no período; λ baixo → falhas raras."
            ),
        )
        st.metric(
            "Horizonte de Planejamento", f"{res['horizonte_horas']:,.0f} h",
            delta=f"{res['horizonte_horas']/8760*12:.1f} meses",
            help=(
                "Período de tempo coberto pelo plano de estoque, em horas.\n\n"
                "Define até quando você quer garantir disponibilidade de peças sem precisar "
                "de um novo ciclo de compra. Normalmente corresponde a 12 meses (8 760 h)."
            ),
        )
        st.metric(
            "Lead Time", f"{res['lead_time_horas']:,.0f} h",
            delta=f"{res['lead_time_horas']/24:.1f} dias",
            help=(
                "Tempo de **reposição do fornecedor**, em horas.\n\n"
                "É o intervalo entre fazer o pedido e receber a peça. Durante esse período "
                "você fica sem cobertura se o estoque zerar — por isso o lead time entra no "
                "cálculo de λ. Lead times maiores exigem estoques maiores."
            ),
        )

        st.markdown(f"""
        <div class="formula-box">
        λ = (T_horizonte + T_leadtime) / η)^β<br>
        λ = ({res['horizonte_horas']:.0f} + {res['lead_time_horas']:.0f}) / {res['eta']:,.0f})^{res['beta']}<br>
        λ = {res['lambda_demanda']:.4f}
        </div>
        """, unsafe_allow_html=True)

    with col_b:
        dist = res["distribuicao"]
        quantidades = dist["quantidades"][:10]
        prob_exata = [p * 100 for p in dist["prob_exata"][:10]]
        prob_acum = [p * 100 for p in dist["prob_acumulada"][:10]]

        fig2 = make_subplots(specs=[[{"secondary_y": True}]])

        fig2.add_trace(go.Bar(
            x=quantidades, y=prob_exata,
            name="P(D = k) — Prob. exata",
            marker_color="#64ffda",
            opacity=0.75,
        ), secondary_y=False)

        fig2.add_trace(go.Scatter(
            x=quantidades, y=prob_acum,
            name="P(D ≤ k) — Nível de Serviço",
            mode="lines+markers",
            line=dict(color="#ff6b6b", width=2),
            marker=dict(size=7),
        ), secondary_y=True)

        # Linha do nível de serviço alvo
        fig2.add_hline(
            y=nivel_servico * 100, line_dash="dot", line_color="#ffd700",
            annotation_text=f"Alvo {nivel_servico*100:.0f}%",
            secondary_y=True,
        )

        fig2.update_layout(
            height=380, template="plotly_dark",
            paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
            title="Distribuição de Probabilidade da Demanda",
            font=dict(color="#e6f1ff"),
            legend=dict(x=0.5, y=1.15, orientation="h",
                        font=dict(color="#e6f1ff"), bgcolor="rgba(30,33,48,0.8)"),
        )
        fig2.update_xaxes(title_text="Quantidade de Peças (k)")
        fig2.update_yaxes(title_text="Probabilidade Exata (%)", secondary_y=False)
        fig2.update_yaxes(title_text="Nível de Serviço Acumulado (%)", secondary_y=True)

        st.plotly_chart(fig2, use_container_width=True)

    # Tabela de probabilidades
    with st.expander("📋 Ver tabela de probabilidades completa"):
        df_prob = pd.DataFrame({
            "Qtde (k)": quantidades,
            "P(D = k) %": [f"{p:.3f}%" for p in prob_exata],
            "P(D ≤ k) % — Nível de Serviço": [f"{p:.2f}%" for p in prob_acum],
        })
        st.dataframe(df_prob, use_container_width=True)


# ════════════════════════════════════════════════════════════
# ABA 3: MODELO DE CUSTO
# ════════════════════════════════════════════════════════════
with aba3:
    st.subheader(f"Otimização de Custo — {componente_sel}")

    st.markdown(f"""
    <div class="explain-box">
    <b>O que estamos fazendo aqui?</b><br>
    Para cada quantidade Q (0 a 15 peças), calculamos o <b>custo de manter</b> o estoque
    (holding cost) e o <b>custo esperado de falta</b> (shortage cost). A <b>soma dos dois</b>
    é o custo total esperado. O ponto mínimo dessa curva é o Q ótimo pelo critério de custo.
    </div>
    """, unsafe_allow_html=True)

    resultado_custo = res["resultado_custo"]
    tabela_custo = pd.DataFrame(resultado_custo["resultados"])

    # Gráfico de custo
    fig3 = go.Figure()

    fig3.add_trace(go.Scatter(
        x=tabela_custo["quantidade"], y=tabela_custo["custo_holding"],
        name="Custo de Manutenção (Ch)",
        mode="lines+markers", line=dict(color="#64ffda", width=2),
    ))
    fig3.add_trace(go.Scatter(
        x=tabela_custo["quantidade"], y=tabela_custo["custo_falta"],
        name="Custo de Falta (Cs)",
        mode="lines+markers", line=dict(color="#ff6b6b", width=2),
    ))
    fig3.add_trace(go.Scatter(
        x=tabela_custo["quantidade"], y=tabela_custo["custo_total"],
        name="Custo Total (CT)",
        mode="lines+markers",
        line=dict(color="#ffd700", width=3),
        marker=dict(size=8),
    ))

    # Marca o ponto ótimo
    q_ot = resultado_custo["q_otimo"]
    ct_ot = resultado_custo["custo_total_otimo"]
    fig3.add_vline(
        x=q_ot, line_dash="dash", line_color="#a78bfa",
        annotation_text=f"Q*={q_ot} (R$ {ct_ot:,.0f})",
        annotation_font_color="#a78bfa",
    )

    fig3.update_layout(
        height=420, template="plotly_dark",
        paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
        title="Custo Total Esperado por Quantidade em Estoque",
        xaxis_title="Quantidade (Q)",
        yaxis_title="Custo Esperado (R$)",
        font=dict(color="#e6f1ff"),
        legend=dict(x=0.6, y=0.9,
                    font=dict(color="#e6f1ff"), bgcolor="rgba(30,33,48,0.8)"),
    )

    st.plotly_chart(fig3, use_container_width=True)

    # Métricas do ponto ótimo
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(
            "Q* — Quantidade Ótima (custo)", f"{q_ot} peças",
            help=(
                "Quantidade de peças que **minimiza o custo total esperado** CT(Q) = Ch(Q) + Cs(Q).\n\n"
                "É o ponto de equilíbrio entre o custo de manter peças sobrando (holding) "
                "e o custo de não ter peças quando precisar (falta). "
                "Abaixo deste Q o risco de parada domina; acima, o custo de estoque domina."
            ),
        )
    with c2:
        st.metric(
            "Custo de Manutenção em Q*", f"R$ {resultado_custo['custo_holding_otimo']:,.0f}",
            help=(
                "**Custo de manter Q* peças em estoque** durante o horizonte de planejamento.\n\n"
                "Calculado por: Ch = Q × valor_peça × taxa_holding × (horizonte / 8 760)\n\n"
                "Inclui capital imobilizado, armazenagem, risco de obsolescência e seguros. "
                f"A taxa de holding configurada é {taxa_holding*100:.0f}% ao ano."
            ),
        )
    with c3:
        st.metric(
            "Custo de Falta em Q*", f"R$ {resultado_custo['custo_falta_otimo']:,.0f}",
            help=(
                "**Custo esperado de paradas de produção** quando a demanda supera Q*.\n\n"
                "Calculado por: Cs = Σ P(D=k) × max(0, k−Q) × custo_parada/h × lead_time\n\n"
                "Representa o valor médio das paradas ponderado pela probabilidade de cada "
                "cenário de demanda. Quando D > Q*, cada peça faltante gera uma parada que dura "
                "todo o lead time."
            ),
        )

    st.markdown(f"""
    <div class="formula-box">
    CT(Q) = Ch(Q) + Cs(Q)<br>
    Ch(Q) = Q × R$ {res['custo_peca']:,.0f} × {taxa_holding*100:.0f}% × (horizonte/8760)<br>
    Cs(Q) = Σ P(D=k) × max(0, k-Q) × R$ {res['custo_parada_hora']:,.0f}/h × {res['lead_time_horas']:.0f}h
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📋 Ver tabela completa de custos"):
        df_tabela = tabela_custo.copy()
        df_tabela.columns = ["Quantidade", "Custo Holding (R$)", "Custo Falta (R$)", "Custo Total (R$)"]
        df_tabela = df_tabela.style.format("R$ {:,.2f}", subset=["Custo Holding (R$)", "Custo Falta (R$)", "Custo Total (R$)"])
        st.dataframe(df_tabela, use_container_width=True)


# ════════════════════════════════════════════════════════════
# ABA 4: RECOMENDAÇÃO FINAL
# ════════════════════════════════════════════════════════════
with aba4:
    st.subheader("✅ Recomendação Final — Todos os Componentes")

    st.markdown(f"""
    <div class="explain-box">
    <b>Como chegamos na recomendação?</b><br>
    Para cada componente, calculamos dois Q's independentes:<br>
    • <b>Q (Confiabilidade)</b>: menor Q que atinge {nivel_servico*100:.0f}% de nível de serviço<br>
    • <b>Q (Custo)</b>: Q que minimiza o custo total esperado<br>
    • <b>Q Recomendado = max(Q_confiab, Q_custo)</b> — satisfaz ambos os critérios
    </div>
    """, unsafe_allow_html=True)

    # Cards por componente
    cols = st.columns(len(resultados))
    for i, r in enumerate(resultados):
        with cols[i]:
            cor = "#64ffda" if r["nivel_servico_real"] >= nivel_servico * 100 else "#ff6b6b"
            st.markdown(f"""
            <div class="metric-card" style="border-color:{cor};">
                <div class="metric-label">{r['nome']}</div>
                <div class="metric-value" style="color:{cor};">{r['q_recomendado']} peças</div>
                <div class="metric-sub">NS: {r['nivel_servico_real']}% | MTTF: {r['mttf']:,.0f}h</div>
                <div class="metric-sub">Q Conf: {r['q_confiabilidade']} | Q Custo: {r['q_custo']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # Tabela resumo completa
    st.subheader("📋 Tabela Resumo Completa")
    st.dataframe(tabela_resumo, use_container_width=True, hide_index=True)

    # Botão de download
    csv = tabela_resumo.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Baixar Tabela como CSV",
        data=csv,
        file_name="recomendacao_sobressalentes.csv",
        mime="text/csv",
    )

    st.divider()
    st.markdown("""
    **Legenda de decisão:**
    - 🟢 Nível de serviço ≥ alvo configurado
    - 🔴 Nível de serviço abaixo do alvo (revisar parâmetros de custo ou aumentar NS alvo)

    > **Próximos passos sugeridos:** calibre os custos de parada com dados reais da sua planta,
    > ajuste o nível de serviço alvo por criticidade do equipamento, e revise periodicamente
    > à medida que novos dados de falha forem coletados.
    """)


# ════════════════════════════════════════════════════════════
# ABA 5: METODOLOGIA
# ════════════════════════════════════════════════════════════
with aba5:
    st.subheader("📚 Metodologia — Como os Cálculos São Feitos")

    st.markdown("""
    <div class="explain-box">
    Este dashboard segue um <b>pipeline de quatro etapas</b> para recomendar o estoque
    ideal de sobressalentes, combinando análise de confiabilidade (Weibull) com
    otimização econômica (modelo de custo). Cada etapa é detalhada abaixo.
    </div>
    """, unsafe_allow_html=True)

    # ── Pipeline visual (Plotly) ─────────────────────────────────────────
    def _caixa(fig, cx, cy, w, h, texto, fill, font_color, borda):
        fig.add_shape(type="rect",
            x0=cx-w/2, y0=cy-h/2, x1=cx+w/2, y1=cy+h/2,
            fillcolor=fill, line=dict(color=borda, width=2))
        fig.add_annotation(x=cx, y=cy, text=texto,
            showarrow=False, align="center",
            xanchor="center", yanchor="middle",
            font=dict(color=font_color, size=11, family="Arial"))

    def _seta(fig, ax, ay, x, y):
        fig.add_annotation(
            ax=ax, ay=ay, x=x, y=y,
            axref="x", ayref="y", xref="x", yref="y",
            showarrow=True, arrowhead=3, arrowsize=1.2,
            arrowwidth=2, arrowcolor="#64748b", text="")

    fig_pipe = go.Figure()

    _caixa(fig_pipe, 0.50, 0.94, 0.40, 0.07,
           "🗂  Dados de Falha (CSV)",
           "#3b82f6", "#ffffff", "#1d4ed8")

    _caixa(fig_pipe, 0.50, 0.78, 0.75, 0.09,
           "<b>Etapa 1 — Ajuste de Weibull (MLE)</b><br>"
           "β (parâmetro de forma)  ·  η (vida característica)  ·  MTTF",
           "#dbeafe", "#1e3a8a", "#93c5fd")

    _caixa(fig_pipe, 0.50, 0.62, 0.75, 0.09,
           "<b>Etapa 2 — Demanda Esperada</b><br>"
           "λ = (T / η)^β   →   Distribuição de Poisson  P(D = k)",
           "#dcfce7", "#14532d", "#86efac")

    _caixa(fig_pipe, 0.21, 0.43, 0.36, 0.12,
           "<b>Etapa 3a — Confiabilidade</b><br>"
           "Q_NS = min Q tal que<br>P(D ≤ Q) ≥ Nível de Serviço Alvo",
           "#fef9c3", "#713f12", "#fde047")

    _caixa(fig_pipe, 0.79, 0.43, 0.36, 0.12,
           "<b>Etapa 3b — Custo</b><br>"
           "CT(Q) = Ch(Q) + Cs(Q)<br>"
           "Q_custo = argmin CT(Q)",
           "#fff7ed", "#7c2d12", "#fdba74")

    _caixa(fig_pipe, 0.50, 0.22, 0.75, 0.09,
           "<b>Etapa 4 — Decisão Final</b><br>"
           "Q_recomendado = max( Q_NS ,  Q_custo )",
           "#f3e8ff", "#581c87", "#d8b4fe")

    _caixa(fig_pipe, 0.50, 0.06, 0.48, 0.07,
           "✅  Estoque Recomendado por Componente",
           "#22c55e", "#ffffff", "#15803d")

    for ax, ay, x, y in [
        (0.50, 0.905, 0.50, 0.825),
        (0.50, 0.735, 0.50, 0.665),
        (0.37, 0.575, 0.21, 0.490),
        (0.63, 0.575, 0.79, 0.490),
        (0.21, 0.370, 0.36, 0.265),
        (0.79, 0.370, 0.64, 0.265),
        (0.50, 0.175, 0.50, 0.095),
    ]:
        _seta(fig_pipe, ax, ay, x, y)

    fig_pipe.update_layout(
        height=620,
        paper_bgcolor="#f8fafc", plot_bgcolor="#f8fafc",
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(visible=False, range=[0, 1], fixedrange=True),
        yaxis=dict(visible=False, range=[0, 1], fixedrange=True),
    )
    st.plotly_chart(fig_pipe, use_container_width=True)

    st.divider()

    # ── ETAPA 1 ─────────────────────────────────────────────────────────
    with st.expander("ETAPA 1 — Ajuste da Distribuição de Weibull", expanded=True):
        st.markdown("""
        ### O que é a Distribuição de Weibull?

        A Weibull é a distribuição mais utilizada em engenharia de confiabilidade porque é
        **flexível**: com apenas dois parâmetros ela consegue representar os três regimes
        clássicos de falha.
        """)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **Parâmetros:**
            | Parâmetro | Nome | Significado |
            |---|---|---|
            | β (beta) | Forma | *Como* as falhas ocorrem no tempo |
            | η (eta) | Escala / Vida Característica | *Quando* 63,2% dos componentes falharam |
            """)
        with col2:
            st.markdown("""
            **Interpretação de β:**
            | Valor | Regime | Exemplo |
            |---|---|---|
            | β < 1 | Mortalidade infantil | Defeitos de fabricação |
            | β ≈ 1 | Falhas aleatórias | Eventos externos |
            | β > 1 | Desgaste | Rolamentos, selos |
            """)

        st.markdown("### Ajuste por Máxima Verossimilhança (MLE)")
        st.markdown("""
        <div class="explain-box">
        O MLE encontra os valores de β e η que <b>maximizam a probabilidade</b> de
        termos observado exatamente os tempos de falha registrados. Em termos práticos,
        é o ajuste estatisticamente mais eficiente para amostras pequenas.
        A implementação usa <code>scipy.stats.weibull_min.fit(dados, floc=0)</code>,
        que fixa o parâmetro de localização em zero (Weibull de 2 parâmetros).
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### Fórmulas Principais")
        st.markdown("""
        <div class="formula-box">
        <b>Função de Confiabilidade</b> — probabilidade de sobreviver até o tempo t:<br>
        &nbsp;&nbsp;R(t) = exp( -(t / η)^β )<br><br>
        <b>Função de Taxa de Falha (Hazard)</b> — taxa instantânea de falha no tempo t:<br>
        &nbsp;&nbsp;h(t) = (β / η) × (t / η)^(β−1)<br><br>
        <b>MTTF — Tempo Médio até a Falha</b>:<br>
        &nbsp;&nbsp;MTTF = η × Γ(1 + 1/β)<br>
        &nbsp;&nbsp;onde Γ é a função Gamma de Euler
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        **Exemplo de leitura:** `R(1000) = 0,85` significa que há **85% de probabilidade**
        de o componente ainda estar funcionando após 1 000 horas de operação.
        """)

    # ── ETAPA 2 ─────────────────────────────────────────────────────────
    with st.expander("ETAPA 2 — Estimativa da Demanda de Peças (Distribuição Poisson)"):
        st.markdown("""
        ### Pergunta Central
        > *Quantas falhas — e portanto, quantas peças — devo esperar durante o
        > horizonte de planejamento mais o lead time de reposição?*

        ### Período de Exposição ao Risco

        O período que realmente importa para o estoque não é só o horizonte de
        planejamento: é necessário incluir também o **lead time**, pois durante
        o tempo de espera pelo fornecedor você estará completamente sem cobertura.
        """)

        st.markdown("""
        <div class="formula-box">
        T_exposição = horizonte_planejamento + lead_time
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        ### Número Esperado de Falhas (λ)

        Usamos a **aproximação Weibull para o processo de renovação**, que estima
        o número médio de falhas (renovações) em um intervalo `[0, T]`:
        """)

        st.markdown("""
        <div class="formula-box">
        λ = E[N(T)] = (T_exposição / η)^β
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="explain-box">
        Esta fórmula é exata quando β = 1 (distribuição exponencial) e é uma
        <b>aproximação conservadora</b> para β ≠ 1. Ela superestima levemente
        a demanda para β &gt; 1 (desgaste), o que é intencional: preferimos
        ter uma peça sobrando a faltar.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        ### Distribuição de Probabilidade da Demanda

        Com λ em mãos, modelamos o **número de falhas no período** como uma
        variável aleatória de Poisson:
        """)

        st.markdown("""
        <div class="formula-box">
        P(D = k) = (λ^k × e^(−λ)) / k!<br><br>
        P(D ≤ k) = Σ P(D = j)  para j = 0, 1, ..., k  ← Nível de Serviço com Q = k peças
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        **Interpretação:** se você mantém **Q peças** em estoque, a probabilidade de
        não ter falta durante o período é `P(D ≤ Q)` — esse é o seu **nível de serviço**.
        """)

    # ── ETAPA 3a ────────────────────────────────────────────────────────
    with st.expander("ETAPA 3a — Quantidade por Nível de Serviço (Abordagem de Confiabilidade)"):
        st.markdown("""
        ### Lógica

        Definido o **nível de serviço alvo** (ex.: 95%), a abordagem de confiabilidade
        encontra a **menor quantidade Q** tal que a probabilidade de não faltar peça
        seja igual ou superior ao alvo:
        """)

        st.markdown("""
        <div class="formula-box">
        Q_confiabilidade = min { Q : P(D ≤ Q) ≥ NS_alvo }
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        O algoritmo percorre Q = 0, 1, 2, ... em ordem crescente e retorna o
        primeiro valor que ultrapassa o limiar.

        **Vantagem:** garante um piso mínimo de disponibilidade operacional independente
        de qualquer premissa de custo.

        **Limitação:** ignora completamente os custos — pode recomendar um estoque
        economicamente inviável se o componente for barato mas raramente falhar.
        """)

    # ── ETAPA 3b ────────────────────────────────────────────────────────
    with st.expander("ETAPA 3b — Quantidade por Otimização de Custo (Abordagem Econômica)"):
        st.markdown("""
        ### Os Dois Custos em Conflito

        Manter estoque sempre envolve um **trade-off**:
        aumentar Q reduz o risco de falta, mas aumenta o custo de imobilização.
        """)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **Custo de Manutenção (Ch)**
            *"Custo de ter peças demais"*
            - Capital imobilizado
            - Armazenagem
            - Risco de obsolescência
            """)
        with col2:
            st.markdown("""
            **Custo de Falta (Cs)**
            *"Custo de ter peças de menos"*
            - Produção parada
            - Aguarda lead time sem cobertura
            - Penalidades contratuais
            """)

        st.markdown("### Fórmulas de Custo")
        st.markdown("""
        <div class="formula-box">
        <b>Custo de Manutenção:</b><br>
        Ch(Q) = Q × custo_peça × taxa_holding × (horizonte / 8 760)<br><br>
        &nbsp;&nbsp;taxa_holding: custo anual de manter 1 R$ em estoque (tipicamente 20–30%)<br>
        &nbsp;&nbsp;O fator horizonte/8 760 converte de anual para o período de planejamento<br><br>
        <b>Custo Esperado de Falta:</b><br>
        Cs(Q) = Σ P(D=k) × max(0, k−Q) × custo_parada/h × lead_time<br>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;k=0..∞<br><br>
        &nbsp;&nbsp;max(0, k−Q): número de falhas sem cobertura quando ocorrem k falhas e há Q peças<br><br>
        <b>Custo Total:</b><br>
        CT(Q) = Ch(Q) + Cs(Q)<br><br>
        <b>Quantidade Ótima:</b><br>
        Q* = argmin CT(Q)
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="explain-box">
        <b>Exemplo intuitivo:</b> se Q = 2 e ocorrem 4 falhas no período, há uma
        falta de 2 peças. Cada peça faltante gera uma parada de produção que dura
        todo o lead_time (tempo de espera pelo fornecedor). O custo desse evento
        é ponderado pela probabilidade de ocorrer exatamente 4 falhas — P(D = 4).
        </div>
        """, unsafe_allow_html=True)

    # ── ETAPA 4 ─────────────────────────────────────────────────────────
    with st.expander("ETAPA 4 — Decisão Final: Combinando os Dois Critérios"):
        st.markdown("""
        ### Regra de Decisão
        """)
        st.markdown("""
        <div class="formula-box">
        Q_recomendado = max( Q_confiabilidade , Q_custo )
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        ### Por que o máximo?

        Cada abordagem protege contra um risco diferente:

        | Situação | Q_custo sugere | Problema |
        |---|---|---|
        | Peça barata, falha rara | 0 ou 1 | Operacionalmente inaceitável |
        | Custo de parada muito alto | 5+ | Pode exceder o NS necessário |

        Tomar o **máximo dos dois** garante que a recomendação final satisfaz
        **simultaneamente** o critério operacional (nível de serviço) e o critério
        econômico (custo mínimo). É uma política conservadora — mas segura.

        ### Quando rever a recomendação?
        - Se `Q_confiabilidade >> Q_custo`: o custo de parada está subestimado ou o
          nível de serviço alvo é muito agressivo para este componente.
        - Se `Q_custo >> Q_confiabilidade`: o custo de parada é muito alto em relação
          ao custo da peça — revise se o lead_time ou custo_parada estão corretos.
        """)

    # ── Formato do CSV ───────────────────────────────────────────────────
    with st.expander("Formato do Arquivo CSV de Entrada"):
        st.markdown("""
        O arquivo CSV deve conter **uma linha por registro de falha** com as seguintes colunas:

        | Coluna | Tipo | Descrição |
        |---|---|---|
        | `componente` | texto | Nome do componente (agrupa as falhas) |
        | `tempo_falha_horas` | número | Horas de operação até a falha |
        | `custo_peca` | número | Valor de compra da peça (R$) |
        | `custo_falta_hora` | número | Custo de produção parada por hora (R$/h) |
        | `lead_time_horas` | número | Tempo para receber do fornecedor (horas) |
        | `horizonte_planejamento_horas` | número | Período de planejamento (horas) |

        Componentes com mais de 1 linha de falha terão todos os seus `tempo_falha_horas`
        usados no ajuste Weibull. Os parâmetros de custo são lidos da **primeira linha**
        de cada componente (devem ser iguais em todas as linhas do mesmo componente).
        """)

        st.markdown("""
        <div class="formula-box">
        componente,tempo_falha_horas,custo_peca,custo_falta_hora,lead_time_horas,horizonte_planejamento_horas
        Rolamento_A,1200,850,3200,240,8760
        Rolamento_A,1450,850,3200,240,8760
        Rolamento_A,980,850,3200,240,8760
        Selo_Mecanico,3100,2400,3200,480,8760
        </div>
        """, unsafe_allow_html=True)

    # ── Referências ──────────────────────────────────────────────────────
    with st.expander("Referências Bibliográficas"):
        st.markdown("""
        - **Reliasoft** — *Life Data Analysis Reference* — metodologia Weibull MLE
          [reliawiki.org](https://www.reliawiki.org/index.php/Life_Data_Analysis_Reference)

        - **Nahmias, S. (2009)** — *Production and Operations Analysis*, 6ª ed. McGraw-Hill — modelo de custo de estoque
          [Google Scholar](https://scholar.google.com/scholar?q=Nahmias+Production+and+Operations+Analysis)

        - **Rausand, M. & Høyland, A. (2004)** — *System Reliability Theory*, 2ª ed. Wiley — processos de renovação
          [Google Scholar](https://scholar.google.com/scholar?q=Rausand+Hoyland+System+Reliability+Theory)

        - **scipy.stats.weibull_min** — implementação do ajuste MLE utilizada neste dashboard
          [docs.scipy.org](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.weibull_min.html)

        - **scipy.stats.poisson** — implementação da distribuição de Poisson utilizada no módulo de demanda
          [docs.scipy.org](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.poisson.html)
        """)
