import os
import json
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from google import genai

# ---------------------------------------------------------
# CONFIGURAÇÃO DE PÁGINA
# ---------------------------------------------------------
st.set_page_config(
    page_title="GDSS Universal - Sistema de Decisão Coletiva & IA",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# INJEÇÃO DE CSS CUSTOMIZADO (ALTO CONTRASTE E LEGIBILIDADE)
# ---------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    .stApp {
        background-color: #F8FAFC !important;
        color: #0F172A !important;
    }

    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0 !important;
    }

    section[data-testid="stSidebar"] * {
        color: #0F172A !important;
    }

    label, p, span, div {
        color: #1E293B !important;
        font-weight: 500;
    }

    .stTextInput input, .stTextArea textarea {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 2px solid #CBD5E1 !important;
        border-radius: 10px !important;
        font-size: 0.95rem !important;
    }

    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #2563EB !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
    }

    div[role="radiogroup"] label span {
        color: #0F172A !important;
        font-weight: 600 !important;
    }

    .pauta-card {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
        border-radius: 16px;
        padding: 32px;
        color: #FFFFFF !important;
        box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.3);
        margin-bottom: 24px;
    }

    .pauta-card * {
        color: #FFFFFF !important;
    }

    .stButton>button {
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        padding: 12px 24px !important;
        font-size: 1rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2) !important;
    }

    .stButton>button:hover {
        background-color: #1D4ED8 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.3) !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# GERENCIAMENTO 100% SEGURO DA API KEY
# ---------------------------------------------------------


def obter_api_key_segura() -> str:
    """Carrega a API key das variáveis de ambiente ou do st.secrets."""
    env_key = os.getenv("GEMINI_API_KEY")
    if env_key:
        return env_key

    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

    return ""


API_KEY = obter_api_key_segura()

try:
    client = genai.Client(api_key=API_KEY) if API_KEY else None
except Exception:
    client = None

# Mensagem de alerta visual caso a chave não esteja configurada
if not client:
    st.warning("🔑 **API Key não detectada!** Crie o ficheiro `.streamlit/secrets.toml` com a variável `GEMINI_API_KEY` para ativar a Inteligência Artificial.")

if "votos" not in st.session_state:
    st.session_state.votos = []

# MODELOS ATUALIZADOS CONFORME RECOMENDAÇÃO DA API DO GEMINI
MODELOS_IA = ["gemini-3.5-flash-lite", "gemini-3.8-flash"]

# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------
st.sidebar.image("https://images.unsplash.com/photo-1552664730-d307ca884978?q=80&w=600&auto=format&fit=crop",
                 caption="Deliberação & Consenso GDSS", use_container_width=True)
st.sidebar.markdown("## ⚙️ Configuração da Pauta")

pauta_atual = st.sidebar.text_area(
    "Tema / Projeto em Debate:",
    value="Transição do Trabalho Presencial para Modelo Híbrido Obrigatório (2 dias no Escritório / 3 dias Remoto)",
    placeholder="Escreva aqui o tema da deliberação...",
    height=120
)

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Limpar Todos os Votos", use_container_width=True):
    st.session_state.votos = []
    st.rerun()

# ---------------------------------------------------------
# FUNÇÕES DE IA
# ---------------------------------------------------------


def chamar_gemini_com_fallback(prompt: str) -> str:
    if not client:
        raise RuntimeError(
            "Cliente Gemini não inicializado. Configure a API Key no ficheiro .streamlit/secrets.toml.")

    ultimo_erro = None
    for modelo in MODELOS_IA:
        try:
            response = client.models.generate_content(
                model=modelo,
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            ultimo_erro = e
            continue

    raise ultimo_erro


def classificar_objecao_dinamica(comentario: str, pauta: str, opcao_voto: str) -> str:
    if not comentario.strip() or opcao_voto in ["Concordo Totalmente", "Aprovar na Íntegra"]:
        return "Sem objeções relevantes"

    if not client:
        return "Objeção Geral / Não Classificada"

    prompt = f"""
    Você é um analista especialista em mediação num sistema GDSS.
    
    PAUTA: "{pauta}"
    POSIÇÃO: "{opcao_voto}"
    JUSTIFICATIVA: "{comentario}"

    TAREFA:
    Identifique o PRINCIPAL ponto de objeção.
    Responda APENAS com um rótulo curto de categoria (2 a 4 palavras).
    Exemplos: "Custo Orçamentário", "Insegurança Jurídica", "Impacto Operacional", "Risco de Segurança".
    """

    try:
        categoria = chamar_gemini_com_fallback(prompt)
        categoria_limpa = categoria.replace('"', '').replace(
            "'", "").replace(".", "").strip()
        return categoria_limpa if categoria_limpa else "Impacto Operacional"
    except Exception:
        texto = comentario.lower()
        if any(k in texto for k in ["custo", "orçamento", "financeiro", "dinheiro", "investimento"]):
            return "Custo / Orçamento"
        elif any(k in texto for k in ["jurídico", "lei", "direitos", "processo"]):
            return "Insegurança Jurídica"
        elif any(k in texto for k in ["segurança", "dados", "tecnologia"]):
            return "Segurança / Tecnologia"
        elif any(k in texto for k in ["operação", "equipe", "logística"]):
            return "Impacto Operacional"
        else:
            return "Outras Objeções"


def gerar_mediacao_ia(df_votos: pd.DataFrame, pauta: str) -> str:
    if df_votos.empty:
        return "Nenhum voto registrado para gerar mediação."

    resumo_votos = df_votos[["usuario", "opcao",
                             "objecao", "argumento"]].to_dict(orient="records")
    pauta_texto = pauta.strip() if pauta.strip() else "Pauta Geral em Deliberação"

    prompt = f"""
    Você é um mediador imparcial num GDSS.
    
    PAUTA: "{pauta_texto}"
    VOTOS: {json.dumps(resumo_votos, ensure_ascii=False)}

    TAREFA:
    1. Resuma os 2 maiores focos de objeção (Análise de Pareto).
    2. Proponha uma Proposta de Compromisso neutra e viável.
    """

    try:
        return chamar_gemini_com_fallback(prompt)
    except Exception as e:
        st.error(f"⚠ Falha na chamada da IA: {e}")

        df_obj = df_votos[df_votos["objecao"] != "Sem objeções relevantes"]
        top_objecoes = df_obj["objecao"].value_counts().head(
            2).index.tolist() if not df_obj.empty else ["Operação", "Orçamento"]
        obj_str = " e ".join(top_objecoes)

        return f"""
        ### ℹ️ Parecer de Mediação (Modo de Contingência Local)
        
        **1. Principais Pontos de Divergência (Análise de Pareto):**
        * Objeções prioritárias no grupo: **{obj_str}**.
        
        **2. Proposta de Compromisso Recomendada:**
        * **Implantação Piloto:** Período experimental de 90 dias com revisões mensais.
        * **Comitê de Acompanhamento:** Criação de grupo de trabalho com líderes operacionais e técnicos.
        """

# ---------------------------------------------------------
# GRÁFICO DE PARETO ESTILIZADO
# ---------------------------------------------------------


def gerar_grafico_pareto(df_votos: pd.DataFrame):
    if df_votos.empty:
        return None

    df_obj = df_votos[df_votos["objecao"] != "Sem objeções relevantes"]
    if df_obj.empty:
        return None

    contagem = df_obj["objecao"].value_counts().reset_index()
    contagem.columns = ["Objeção", "Frequência"]
    contagem = contagem.sort_values(
        by="Frequência", ascending=False).reset_index(drop=True)

    total = contagem["Frequência"].sum()
    contagem["Percentual_Acumulado"] = (
        contagem["Frequência"].cumsum() / total) * 100

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x=contagem["Objeção"],
            y=contagem["Frequência"],
            name="Quantidade",
            marker=dict(color="#2563EB", cornerradius=6),
            text=contagem["Frequência"],
            textposition="outside",
            textfont=dict(color="#0F172A", size=13, family="Plus Jakarta Sans")
        ),
        secondary_y=False
    )

    fig.add_trace(
        go.Scatter(
            x=contagem["Objeção"],
            y=contagem["Percentual_Acumulado"],
            name="Acumulado (%)",
            mode="lines+markers",
            line=dict(color="#DC2626", width=3),
            marker=dict(size=8, color="#DC2626")
        ),
        secondary_y=True
    )

    fig.add_shape(
        type="line",
        x0=-0.5, x1=len(contagem) - 0.5,
        y0=80, y1=80,
        line=dict(color="#16A34A", width=2, dash="dash"),
        xref="x", yref="y2"
    )

    fig.update_layout(
        title=dict(text="<b>Análise de Pareto:</b> Objeções Relevantes Identificadas",
                   font=dict(size=16, color="#0F172A")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=50, b=20),
        font=dict(color="#334155")
    )

    fig.update_xaxes(showgrid=False, color="#334155")
    fig.update_yaxes(title_text="Quantidade", showgrid=True,
                     gridcolor="#E2E8F0", secondary_y=False, dtick=1)
    fig.update_yaxes(title_text="% Acumulado", range=[
                     0, 105], showgrid=False, secondary_y=True)

    return fig


# ---------------------------------------------------------
# INTERFACE PRINCIPAL
# ---------------------------------------------------------
st.title("🏛️ GDSS Universal - Suporte à Decisão Coletiva")
st.markdown("Sistema Inteligente de Gestão de Debates, Análise de Objeções e Mediação por Inteligência Artificial.")
st.write("")

titulo_pauta = pauta_atual.strip() if pauta_atual.strip(
) else "Defina o tema da pauta na barra lateral."
st.markdown(f"""
<div class="pauta-card">
    <div style="font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.08em; opacity: 0.9;">Pauta em Debate Atual</div>
    <div style="font-size: 1.35rem; font-weight: 700; margin-top: 6px;">{titulo_pauta}</div>
</div>
""", unsafe_allow_html=True)

col_form, col_dash = st.columns([1, 2], gap="large")

with col_form:
    st.markdown("### 🗳️ Registrar Posição")
    with st.form("form_politico", clear_on_submit=True):
        nome = st.text_input("Nome / Representante:",
                             placeholder="Ex: Dra. Helena (Consultoria)")
        opcao = st.radio(
            "Sua posição sobre o projeto:",
            ["Aprovar na Íntegra", "Aprovar com Emendas", "Rejeitar Projeto"]
        )
        comentario = st.text_area("Justificativa / Comentários Livres:",
                                  placeholder="Explique os motivos da sua decisão...")

        btn_voto = st.form_submit_button(
            "Submeter Voto", use_container_width=True)

        if btn_voto and nome:
            if not pauta_atual.strip():
                st.warning("⚠ Defina o tema da pauta antes de submeter.")
            else:
                with st.spinner("🤖 Processando voto e categorizando argumento..."):
                    categoria_ia = classificar_objecao_dinamica(
                        comentario, pauta_atual, opcao)
                    st.session_state.votos.append({
                        "usuario": nome,
                        "opcao": opcao,
                        "objecao": categoria_ia,
                        "argumento": comentario
                    })
                    st.success(
                        f"Voto registrado! Categoria: **{categoria_ia}**")
                    st.rerun()

with col_dash:
    st.markdown("### 📊 Painel Analítico & Consenso")
    df_votos = pd.DataFrame(st.session_state.votos)

    tab_pareto, tab_mediacao, tab_dados = st.tabs(
        ["Análise de Pareto", "🤖 Mediador IA", "Histórico de Votos"])

    with tab_pareto:
        fig = gerar_grafico_pareto(df_votos)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
            st.info("💡 **Princípio de Pareto (80/20):** Foque a discussão nas objeções à esquerda da linha pontilhada verde para resolver a maioria dos conflitos do grupo.")
        else:
            st.image("https://images.unsplash.com/photo-1531403009284-440f080d1e12?q=80&w=800&auto=format&fit=crop",
                     caption="Aguardando registros de voto para gerar o gráfico.", use_container_width=True)
            st.info(
                "Cadastre os primeiros votos no formulário ao lado para gerar o Painel de Pareto.")

    with tab_mediacao:
        st.subheader("🤖 Parecer Neutro & Proposta de Compromisso")
        if st.button("Gerar Substitutivo com IA", use_container_width=True):
            with st.spinner("🤖 Analisando objeções e construindo proposta neutra..."):
                parecer = gerar_mediacao_ia(df_votos, pauta_atual)
                st.markdown(parecer)

    with tab_dados:
        st.dataframe(df_votos, use_container_width=True)
