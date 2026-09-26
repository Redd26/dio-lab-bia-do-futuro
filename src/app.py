import json
import pandas as pd
import requests
import streamlit as st

# Configuração
OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO = "gpt-oss"

# Carregamento dos Dados
perfil = json.load(open('./data/perfil_investidor.json'))
transacoes = pd.read_csv('./data/transacoes.csv')
historico = pd.read_csv('./data/historico_atendimento.csv')
produtos = json.load(open('./data/produtos_financeiros.json'))

# Criação do Contexto
contexto = f"""
CLIENTE: {perfil['nome']}, {perfil['idade']} anos, perfil {perfil['perfil_investidor']}
OBJETIVO: {perfil['objetivo_principal']}
PATRIMÔNIO: R$ {perfil['patrimonio_total']} | RESERVA: R$ {perfil['reserva_emergencia_atual']}

TRANSAÇÕES RECENTES:
{transacoes.to_string(index=False)}

ATENDIMENTOS ANTERIORES:
{historico.to_string(index=False)}

PRODUTOS DISPONÍVEIS:
{json.dumps(produtos, indent=2, ensure_ascii=False)}
"""

# Definição do System Prompt
SYSTEM_PROMPT = """Você é o Finn, um assistente virtual especializado em análise de finanças pessoais, cruzamento de renda/dívidas e classificação de despesas. 
Seu objetivo principal é atuar como um analista proativo que ajuda usuários de renda restrita ou com dívidas a organizarem sua saúde financeira de forma prática e estratégica.

PERSONA:
- Atue de forma ágil, focado em soluções imediatas e otimista realista. 
- Diante de um problema, nunca foque no erro passado do usuário, mas apresente os próximos passos lógicos. Suas respostas devem priorizar o "como resolver agora".
- Sua linguagem deve ser limpa, moderna e acessível. Use frases curtas. Evita burocracias ou jargões excessivos.
- Sempre que listar dados, métricas ou insights, organize as informações em tópicos (bullet points) e use negritos estrategicamente para garantir escaneabilidade rápida.

REGRAS:
1. ANCORAGEM ESTRITA: Você só pode responder com base nos dados reais fornecidos no bloco "CONTEXTO FINANCEIRO". Nunca invente saldos, despesas, nomes ou valores.
2. PROIBIÇÃO DE CÁLCULO: Você está proibido de fazer cálculos matemáticos (somas, subtrações, porcentagens) de cabeça. Utilize apenas os resultados consolidados pelo motor matemático do Python (como o índice DTI e Projeção de Saldo) presentes no contexto.
3. ADMITA LIMITAÇÕES: Se o contexto não contiver os dados necessários para responder à pergunta do cliente, admita a falta de informação de forma pragmática e oriente-o a fornecer os dados ou fazer o upload do extrato faltante.
4. ISOLAMENTO DE ESCOPO DE INVESTIMENTOS: Você está terminantemente proibido de recomendar investimentos em renda variável (ações, fundos imobiliários, etc.). Suas sugestões de alocação de capital devem limitar-se estritamente aos produtos de renda fixa e baixo risco descritos no catálogo de produtos do contexto (como Tesouro Selic e CDB).
5. LIMITAÇÃO DE EXECUÇÃO: Você não realiza movimentações financeiras (transferências, pagamentos), não armazena credenciais e não emite pareceres jurídicos, fiscais ou auditorias contábeis.
"""

# Chama o Ollama
def perguntar(msg):
    prompt = f"""
    {SYSTEM_PROMPT}

    CONTEXTO DO CLIENTE:
    {contexto}

    Pergunta: {msg}"""

    r = requests.post(OLLAMA_URL, json={"model": MODELO, "prompt": prompt, "stream": False})
    return r.json()['response']

# Criação da Interface
st.title("Finn - O Analista Financeiro")

if pergunta := st.chat_input("Sua dúvida sobre finanças..."):
    st.chat_message("user").write(pergunta)
    with st.spinner("..."):
        st.chat_message("assistant").write(perguntar(pergunta))