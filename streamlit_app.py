import streamlit as st 
import requests 
import os 
from google import genai 

st.title("⚖️ JusBot: Assistente Legislativo")
st.caption("Seu guia interativo para Projetos de Lei Federais (PLs)")

try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=GEMINI_API_KEY)
except KeyError:
    st.error("Erro: A chave 'GEMINI_API_KEY' não foi encontrada nos Secrets do Streamlit. Verifique a Aula 11!")
    st.stop()

MODEL_NAME = "gemini-2.5-flash" 

CAMARA_API_URL = "https://dadosabertos.camara.leg.br/api/v2"

def buscar_pl_por_id(id_proposicao):
    """Faz a requisição para obter os detalhes de uma Proposição."""
    url = f"{CAMARA_API_URL}/proposicoes/{id_proposicao}"
    st.info(f"Fazendo requisição: {url}") 
    
    resposta = requests.get(url) 

    if resposta.status_code == 200:
        dados = resposta.json()['dados']
        
        texto_pl = dados.get('urlInteiroTeor')
        if not texto_pl:
            texto_pl = dados.get('ementa', 'Texto integral não disponível. Usando a Ementa.')
            
        return dados, texto_pl
    else:
        st.error(f"Erro ao buscar PL: {resposta.status_code}. Verifique se o ID é válido.")
        return None, None

def gerar_resumo_executivo(texto_pl, dados_pl):
    """Gera o resumo de 2-3 parágrafos usando o Gemini."""
    
    ficha = (
        f"Tipo: {dados_pl.get('siglaTipo')} - {dados_pl.get('numero')}/{dados_pl.get('ano')}\n"
        f"Ementa: {dados_pl.get('ementa')}"
    )
    
    prompt_resumo = (
        f"Você é um assistente legislativo. Crie um resumo executivo de **2 a 3 parágrafos** "
        f"do Projeto de Lei (PL) a seguir, destacando o tema, o objetivo e as principais propostas.\n\n"
        f"--- Ficha Técnica ---\n{ficha}\n\n"
        f"--- Texto do PL ---\n{texto_pl}"
    )

    response = client.generate_content(MODEL_NAME, prompt_resumo)
    return response.text

def responder_pergunta(texto_pl, dados_pl, pergunta):
    """Responde a uma pergunta específica do usuário."""
    
    prompt_pergunta = (
        f"Você é um assistente legislativo. Responda diretamente e de forma contextualizada "
        f"à pergunta do usuário, utilizando APENAS o texto do Projeto de Lei fornecido. "
        f"Se a informação não estiver no texto, diga que não pode responder com base nele.\n\n"
        ff"--- Pergunta ---\n{pergunta}\n\n"
        f"--- Texto do PL ---\n{texto_pl}"
    )
    
    response = client.generate_content(MODEL_NAME, prompt_pergunta)
    return response.text

pl_input = st.text_input(
    "Insira o ID do PL (ex: '2338') ou o número completo (ex: 'PL 2338/2023'):",
    placeholder="Ex: 2338 ou PL 2338/2023"
)

pergunta_usuario = st.text_input(
    "Faça uma pergunta sobre o PL (ex: 'Quem é o autor do PL?', 'Qual a situação?'):",
    placeholder="Ex: Quais são os principais temas deste Projeto de Lei?"
)

if st.button("Consultar PL e Processar com Gemini"):
    if not pl_input:
        st.warning("Por favor, insira o identificador do PL para iniciar a consulta.")
        st.stop()
      
    id_numerico = pl_input.split('/')[0].split()[-1]
    
    with st.spinner(f"Buscando e processando informações do PL..."):
        
        dados_pl, texto_pl = buscar_pl_por_id(id_numerico)

        if dados_pl:
            st.success(f"Dados do PL {dados_pl.get('siglaTipo')} {dados_pl.get('numero')}/{dados_pl.get('ano')} encontrados!")

            st.subheader("📋 Ficha Técnica Estruturada")
            ficha_tecnica_data = {
                "Tipo de Proposição": f"{dados_pl.get('siglaTipo')} - {dados_pl.get('numero')}/{dados_pl.get('ano')}",
                "Ementa (Resumo Oficial)": dados_pl.get('ementa'),
                "Situação Atual": dados_pl.get('situacao', {}).get('descricao', 'N/A'),
                "Link para o Texto Integral": dados_pl.get('urlInteiroTeor', 'Não disponível')
            }
      
            st.table(ficha_tecnica_data) 

            st.subheader("💡 Resumo Executivo (Análise Gemini)")
            resumo = gerar_resumo_executivo(texto_pl, dados_pl)
            st.markdown(resumo)
            
            if pergunta_usuario:
                st.subheader(f"💬 Resposta à Pergunta: '{pergunta_usuario}'")
                resposta = responder_pergunta(texto_pl, dados_pl, pergunta_usuario)
                st.markdown(resposta)
            else:
                st.info("Digite uma pergunta para obter uma análise específica do Gemini.")
