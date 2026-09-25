# Base de Conhecimento

## Dados Utilizados

| Arquivo | Formato | Para que serve no Finn? |
|---------|---------|---------------------|
| `historico_atendimento.csv` | CSV | Evita repetição de conceitos que o cliente já sanou. |
| `perfil_investidor.json` | JSON | Fornece a renda líquida e as parcelas de dívidas ativas para o cálculo de comprometimento de renda |
| `produtos_financeiros.json` | JSON | Ativos recomendados para aportes de reserva de emergência condizentes com o perfil. |
| `transacoes.csv` | CSV | Auxilia a projetar o saldo de fechamento do mês. |
| [mitulshah/transaction-categorization](https://huggingface.co/datasets/mitulshah/transaction-categorization) | Dataset  | Dicionário de padrões para o script Python cruzar strings e categorizar despesas brutas automaticamente. |
| [Akhil-Theerthala/PersonalFinance_v2](https://huggingface.co/datasets/Akhil-Theerthala/PersonalFinance_v2) | Dataset  | Contribui para o tom de comunicação para ações diretas, prgmáticas e eficientes. |
| [NikitaSirotkin/financial-life-advice](https://huggingface.co/datasets/NikitaSirotkin/financial-life-advice/blob/main/README.md) | Dataset  | Orienta o cliente a resolver problemas de alto endividamento de forma viável. |

---

## Adaptações nos Dados

> Você modificou ou expandiu os dados mockados? Descreva aqui.

perfil_investidor.json - Foram adicionados IDs de contratos de dívidas para bater com as transações e o campo de perfil_risco estrito.

transacoes.csv - As transações foram expandidas para simular um mês completo de gastos.

produtos_financeiros.json - Foram incluídos parâmetros de liquidez para auxiliar o Finn a justificar cada sugestão técnica.

historico_atendimento.csv - O histórico foi ajustado para simular em quais situações o cliente buscou ajuda, para auxiliar na criação da estratégia.

---

## Estratégia de Integração

### Como os dados são carregados?

Os dados são primeiramente lidos para definir a saúde financeira do cliente. Em seguida, o script usa os datasets do Hugging Face para melhorar as buscas locais por similaridades ou classificação.

```python
import os
import json
import pandas as pd
from datasets import load_dataset

# Carrega os dados locais
def carregar_dados_locais():
    caminho_base = "data"
    
    # Perfil e Dívidas
    with open(os.path.join(caminho_base, "perfil_investidor.json"), "r", encoding="utf-8") as f:
        perfil = json.load(f)
        
    # Extrato de Transações
    df_transacoes = pd.read_csv(os.path.join(caminho_base, "transacoes.csv"))
    
    # Catálogo de Produtos
    with open(os.path.join(caminho_base, "produtos_financeiros.json"), "r", encoding="utf-8") as f:
        produtos = json.load(f)
        
    # Histórico de Chats
    df_historico = pd.read_csv(os.path.join(caminho_base, "historico_atendimento.csv"))
    
    return perfil, df_transacoes, produtos, df_historico

# Carrega os datasets
def carregar_datasets_hf():
    # Dataset para ajudar na classificação de despesas
    ds_categorizacao = load_dataset("mitulshah/transaction-categorization", split="train")
    
    # Dataset com boas práticas de aconselhamento financeiro
    ds_conselhos = load_dataset("Akhil-Theerthala/PersonalFinance_v2", split="train")
    
    return ds_categorizacao, ds_conselhos

# Integração principal
def iniciar_base_conhecimento():
    try:
        perfil, transacoes, produtos, historico = carregar_dados_locais()
        ds_cat, ds_cons = carregar_datasets_hf()
        
        # Cria o payload injetado no Ollama
        contexto_agente = {
            "cliente": perfil,
            "total_transacoes_mes": len(transacoes),
            "produtos_disponiveis": produtos
        }
        
        return contexto_agente, transacoes
    except Exception as e:
        print(f"Erro ao integrar base de dados: {e}")
        return None, None
```

### Como os dados são usados no prompt?

Para não ser necessário referenciar os dados de forma bruta eu realizo consultas dinâmicas e em cada mensagem eu injeto eles usando o System Prompt Estático para manter a personalidade do Finn coerente com as regras de segurança e limitações. Então em cada pergunta do cliente, os dados dele são atualizados e o bloco de texto com essas informações são criados e colocados acima da pergunta para que o Ollama se baseie nestas informações atualizadas para gerar as respostas.

```python
import json

def obter_system_prompt():
    return """
    Você é o Finn, um assistente virtual especializado em análise de finanças pessoais.
    Seu tom de voz é o 'Parceiro Proativo e Pragmático': seja ágil, direto ao ponto, otimista e use tópicos (bullet points) para facilitar a leitura.
    
    DIRETRIZES RÍGIDAS DE SEGURANÇA:
    1. Você é proibido de fazer cálculos matemáticos de cabeça. Use APENAS os valores fornecidos no contexto.
    2. Se faltarem dados para responder algo, admita e peça para o usuário fornecer as informações.
    3. Nunca faça recomendações de investimentos em renda variável (ações/fundos). Limite-se às opções de renda fixa do contexto.
    4. Nunca realize transferências ou transações diretamente.
    """

def montar_contexto_dinamico(perfil_cliente, metricas_caixa):
    # Extrai dados do perfil local
    nome = perfil_cliente.get("nome", "Cliente")
    renda = perfil_cliente.get("renda_mensal_liquida", 0.0)
    dividas = perfil_cliente.get("dividas_ativas", [])
    
    # Calcula os valores totais de dívida mensais
    total_divida_mes = sum(d["valor_mensal"] for d in dividas)
    
    # Pega as métricas
    dti = metricas_caixa.get("dti_atual", 0.0)
    status_risco = metricas_caixa.get("status_risco", "Normal")
    projecao_fim_mes = metricas_caixa.get("previsao_fim_mes", "Estável")

    # Estrutura a String de contexto do Ollama antes da pergunta do usuário
    contexto = f"""
    ### CONTEXTO FINANCEIRO REAL DO CLIENTE (NÃO ALUCINE) ###
    - Cliente Atual: {nome}
    - Renda Mensal Líquida: R$ {renda:.2f}
    - Total de Parcelas de Dívidas vindo no mês: R$ {total_divida_mes:.2f}
    - Comprometimento de Renda Atual (DTI): {dti:.1f}% -> Status de Risco: {status_risco}
    - Projeção de Saldo para Fim do Mês: {projecao_fim_mes}
    
    ### PRODUTOS DISPONÍVEIS PARA RECOMENDAÇÃO (RENDA FIXA) ###
    - Tesouro Selic (Liquidez D+1, Aporte mín: R$ 30)
    - CDB Liquidez Diária (Liquidez Imediata, Aporte mín: R$ 100)
    ---------------------------------------------------------
    """
    return contexto

def formatar_payload_ollama(perfil_cliente, metricas_caixa, pergunta_usuario):
    system_rules = obter_system_prompt()
    dados_reais = montar_contexto_dinamico(perfil_cliente, metricas_caixa)
    
    # Junta os dados reais com a pergunta do usuário na mensagem final
    mensagem_usuario_com_contexto = f"{dados_reais}\nPergunta do Cliente: {pergunta_usuario}"
    
    payload = {
        "model": "llama3",
        "messages": [
            {"role": "system", "content": system_rules},
            {"role": "user", "content": message_usuario_com_contexto}
        ],
        "stream": False
    }
    return payload
```

---

## Exemplo de Contexto Montado

O exemplo de formatação dos dados foi pensado para enxugar o uso de tokens e focar nas informações necessárias para alimentar o Ollama de maneira precisa e fácil de ler para encontrar correlações, por conta disso os números entre colchetes **[ ]** na frente das informações foram colocadas para diminuir a chance do agente alucinar e inventar informações que não foram definidas na base de conhecimento. Os cálculos como DTI e Projeção foram colocados logo de início, para que o agente leia os fatos matemáticos antes de dar uma resposta.

```
### CONTEXTO FINANCEIRO REAL DO CLIENTE (NÃO ALUCINE) ###
- Cliente Atual: João Silva [2]
- Idade / Profissão: 32 anos, Analista de Sistemas [2]
- Renda Mensal Líquida: R$ 5000.00 [2]
- Patrimônio Total: R$ 15000.00 (Reserva de Emergência Atual: R$ 10000.00) [2]

### ANÁLISE DE COMPROMETIMENTO DE RENDA ###
- Total de Dívidas Fixas no Mês: R$ 1500.00 [2, 4]
  * [Contrato DIV-001] Empréstimo Bancário: R$ 1000.00 (Vence todo dia 10) [2]
  * [Contrato DIV-002] Financiamento de Notebook: R$ 500.00 (Vence todo dia 22) [2]
- Índice de Comprometimento Atual (DTI): 30.0% -> Status de Risco: Alerta Limite
- Projeção de Saldo para Fim do Mês: Conta em equilíbrio, risco de saldo negativo em caso de novos gastos variáveis.

### HISTÓRICO RECENTE DE TRANSAÇÕES (MÊS ATUAL) ###
- 2025-10-01 | Entrada | Salário Empresa: +R$ 5000.00 [4]
- 2025-10-02 | Saída   | Aluguel e Condomínio: -R$ 1200.00 (Categoria: Moradia) [4]
- 2025-10-03 | Saída   | Supermercado Central: -R$ 450.00 (Categoria: Alimentação) [4]
- 2025-10-10 | Saída   | Débito Empréstimo Parcela 01: -R$ 1000.00 (Vínculo: DIV-001) [4]
- 2025-10-12 | Saída   | Corrida Uber Urbano: -R$ 45.00 (Categoria: Transporte) [4]
- 2025-10-22 | Saída   | Parc 01 Financiamento Notebook: -R$ 500.00 (Vínculo: DIV-002) [4]

### CATÁLOGO DE PRODUTOS PERMITIDOS PARA SUGESTÃO (RENDA FIXA) ###
- Tesouro Selic (Categoria: Renda Fixa | Risco: Baixo | Rentabilidade: 100% da Selic | Liquidez: D+1 | Aporte Mínimo: R$ 30.00) [3]
- CDB Liquidez Diária (Categoria: Renda Fixa | Risco: Baixo | Rentabilidade: 102% do CDI | Liquidez: Imediata | Aporte Mínimo: R$ 100.00) [3]
```