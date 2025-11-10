
import streamlit as st
import requests
import os
import google.generativeai as genai 

st.title("Assistente Interativo de Consulta Legislativa")
st.caption("Foco em Projetos de Lei (PLs) Federais")

try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("Erro: A chave 'GEMINI_API_KEY' não foi encontrada nos Secrets do Streamlit. Verifique a Aula 11!")
    st.stop()

MODEL_NAME = "gemini-1.5-flash"
model = genai.GenerativeModel(MODEL_NAME)

CAMARA_API_URL = "https://dadosabertos.camara.leg.br/api/v2"

def buscar_pl(sigla, numero, ano):
    """
    Busca um PL pelo tipo, número e ano, encontra seu ID único,
    e só então busca os detalhes completos.
    """
    
    search_url = f"{CAMARA_API_URL}/proposicoes"
    params = {
        'siglaTipo': sigla,
        'numero': numero,
        'ano': ano,
        'ordem': 'DESC',
        'ordenarPor': 'id'
    }
    st.info(f"Buscando {sigla} {numero}/{ano} na API da Câmara...")
    search_response = requests.get(search_url, params=params)
    
    if search_response.status_code != 200 or not search_response.json()['dados']:
        st.error(f"Nenhuma proposição encontrada para {sigla} {numero}/{ano}. Verifique os dados.")
        return None, None

    id_proposicao = search_response.json()['dados'][0]['id']
    st.success(f"Proposição encontrada! (ID interno: {id_proposicao})")

    details_url = f"{CAMARA_API_URL}/proposicoes/{id_proposicao}"
    details_response = requests.get(details_url)
    
    if details_response.status_code == 200:
        dados = details_response.json()['dados']
        
        texto_pl = dados.get('urlInteiroTeor')
        if not texto_pl:
            texto_pl = dados.get('ementa', 'Texto integral não disponível.')
            st.warning("Texto integral (urlInteiroTeor) não disponível. Usando a Ementa para a análise.")
            
        return dados, texto_pl
    else:
        st.error(f"Erro ao buscar detalhes do ID {id_proposicao}.")
        return None, None


def gerar_resumo_executivo(texto_pl, dados_pl):
    """Gera o resumo de 2-3 parágrafos usando o Gemini."""
    
    ficha = (
        f"Tipo: {dados_pl.get('siglaTipo')} - {dados_pl.get('numero')}/{dados_pl.get('ano')}\n"
        f"Ementa: {dados_pl.get('ementa')}"
    )
    
    prompt_resumo = f"""Crie um resumo executivo de 2 a 3 parágrafos do Projeto de Lei (PL) a seguir, destacando o tema, o objetivo e as principais propostas.

--- Ficha Técnica ---
{ficha}

--- Texto do PL ---
{texto_pl}
"""

    response = model.generate_content(prompt_resumo)
    return response.text

def responder_pergunta(texto_pl, dados_pl, pergunta):
    """Responde a uma pergunta específica do usuário."""
    
    prompt_pergunta = f"""Responda diretamente e de forma contextualizada à pergunta do usuário, utilizando APENAS o texto do Projeto de Lei fornecido. Se a informação não estiver no texto, diga que não pode responder com base nele.

--- Pergunta ---
{pergunta}

--- Texto do PL ---
{texto_pl}
"""
    
    response = model.generate_content(prompt_pergunta)
    return response.text


st.subheader("1. Identifique a Proposição")
col1, col2, col3 = st.columns(3)
with col1:
    sigla_input = st.text_input("Sigla", placeholder="PL", value="PL")
with col2:
    numero_input = st.text_input("Número", placeholder="2338")
with col3:
    ano_input = st.text_input("Ano", placeholder="2023")

st.subheader("2. Faça sua Pergunta (Opcional)")
pergunta_usuario = st.text_input(
    "Faça uma pergunta sobre o PL (ex: 'Quem é o autor do PL?'):",
    placeholder="Quais são os principais temas deste Projeto de Lei?"
)

if st.button("Consultar PL e Processar"):
    
    if not numero_input or not ano_input:
        st.warning("Por favor, preencha pelo menos o Número e o Ano da proposição.")
        st.stop()

    with st.spinner(f"Buscando e processando {sigla_input} {numero_input}/{ano_input}..."):
        
        dados_pl, texto_pl = buscar_pl(sigla_input.upper(), numero_input, ano_input)

        if dados_pl:
            
            st.subheader("Ficha Técnica Estruturada")
            ficha_tecnica_data = {
                "Tipo de Proposição": f"{dados_pl.get('siglaTipo')} - {dados_pl.get('numero')}/{dados_pl.get('ano')}",
                "Ementa (Resumo Oficial)": dados_pl.get('ementa'),
                "Situação Atual": dados_pl.get('situacao', {}).get('descricao', 'N/A'),
                "Link (Inteiro Teor)": dados_pl.get('urlInteiroTeor', 'Não disponível')
            }
            st.table(ficha_tecnica_data) 

            st.subheader("Resumo Executivo (Análise Gemini)")
            resumo = gerar_resumo_executivo(texto_pl, dados_pl)
            st.markdown(resumo)
            
            if pergunta_usuario:
                st.subheader(f"Resposta à Pergunta: '{pergunta_usuario}'")
                resposta = responder_pergunta(texto_pl, dados_pl, pergunta_usuario)
                st.markdown(resposta)
