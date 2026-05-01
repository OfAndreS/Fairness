import pandas as pd
import json
import os
from vllm import LLM, SamplingParams

# ---------------------------------------------------------
# 1. Configuração do Motor vLLM (HPC)
# ---------------------------------------------------------
print("A inicializar o motor vLLM...")
llm = LLM(
    model="/mnt/modelo",
    dtype="bfloat16",
    trust_remote_code=True,
    gpu_memory_utilization=0.95,
    max_model_len=8192,
    enable_prefix_caching=True 
)

sampling_params = SamplingParams(
    temperature=0.0, 
    max_tokens=1500
)

# ---------------------------------------------------------
# 2. Carregamento e Preparação dos Dados (CORRIGIDO)
# ---------------------------------------------------------
print("A carregar os dados...")
# Lemos direto do seu arquivo já explodido e rastreável
df_clear = pd.read_csv('SplitPosDatasets.csv')

# Proteção extra: remove a coluna de índice antigo se ela existir
if 'Unnamed: 0' in df_clear.columns:
    df_clear = df_clear.drop(columns=['Unnamed: 0'])

# ---------------------------------------------------------
# 3. Definição dos Prompts (Mantidos Intactos)
# ---------------------------------------------------------
prompt_classificacao = """
Role: You are a Senior Financial Data Architect. 
Task: Classify variables according to STRICT mapping rules.
Context: This is for a banking credit scoring system.

RULES FOR MAPPING (PRIORITY ORDER):
1. SOCIOECONOMIC: Home ownership, number of children/dependents, household size, length of employment, employment status, occupation, family income, income, wealth, parents’ income, social class, education. (STRICT: Employment duration and salary go here, NEVER in Institutional).
2. DEMOGRAPHIC: Age, gender, ethnicity, marital status, family life cycle. (STRICT: NO geographical locations here. NO account age here).
3. VALUES, ATTITUDES and BEHAVIORAL: Socio-motivation/others, attitudes toward debt, parent facilitation, time horizon, perceived financial wellbeing, attitudes toward positive financial behavior, religious practices, consumer behavior, level of expenditure (spending pattern), attitudes toward money/money beliefs and behaviors, attitudes toward risk-taking, attitudes toward credit, compulsive buying, delay of gratification, financial knowledge, loan purpose/intent.
4. INSTITUTIONAL and FINANCIAL: Number of debts, length of relationship with the bank, number of bank accounts, debt to income ratio, total financial assets, payment pattern, credit limit, existing credit commitments, credit score, number of credit cards, credit history in the past, loan amount, taking debt advice, loan duration, account balance. (STRICT: Only banking, credit, and debt metrics. NO demographic or income data).
5. PERSONALITY: Self-control, emotional stability/neuroticism, intelligence (IQ score), locus of control, self-efficacy, agreeableness, optimism, self-esteem, extraversion, conscientiousness, openness to experience, impulsiveness.
6. SITUATIONAL: ONLY adverse life events or life-altering events. (STRICT: NEVER classify dates, system terms, or housing here).
7. EDUCATIONAL: Field of study, GPA (Grade Point Average), year at school. (NOTE: General education level goes to SOCIOECONOMIC).
8. MACROECONOMIC: General economic indicators such as inflation (CPI) or economic growth (GDP).
9. HEALTH-RELATED: Physical health status and mental health indicators.
10. ALTERNATIVE: Social network visiting patterns, posting patterns, usage of photo for posts, major things in people’s lives, qualifications of people within individuals’ network, social network prestige, membership score, retweet behavior, emoticon utilization, posting time, number of followers, friends, the slope of daily calls sent, SMS sending pattern, number of messages, disclosure of social media profile, AND ALL geographical locations (City, State, Zipcode), telemetry, device info, and IP addresses.
11. UNCLASSIFIED: System IDs, Keys, hashes, meaningless strings, generic technical flags, variables that lack semantic meaning, and specific system timestamps/calendar dates (e.g., CreationDate, DefaultDate).

EXAMPLES OF CORRECT MAPPING:
- 'housing_type' -> 'SOCIOECONOMIC' (Not Situational!)
- 'city_of_residence' -> 'ALTERNATIVE' (Not Demographic!)
- 'loan_term_months' -> 'INSTITUTIONAL and FINANCIAL'
- 'months_employed' -> 'SOCIOECONOMIC' (Not Institutional!)
- 'ListingKey' -> 'UNCLASSIFIED'

INPUT VARIABLES: {lote}

OUTPUT: Return ONLY a valid JSON object where keys are variable names and values are the categories.
"""

prompt_reflexao = """
Role: You are a Zero-Tolerance Quality Auditor for Data Engineering.
Task: Fix common logical errors in the following JSON classification.

AUDIT CHECKLIST (FIX IF WRONG):
1. Is any geographical location, IP address, or device info in 'DEMOGRAPHIC'? -> MOVE TO 'ALTERNATIVE'.
2. Is 'housing', 'property', 'income', 'salary', or 'employment' in 'INSTITUTIONAL and FINANCIAL'? -> MOVE TO 'SOCIOECONOMIC'.
3. Are raw system dates, timestamps, IDs, or Keys (e.g., 'DateOfBirth', 'ListingKey', 'LoanID') in ANY category other than 'UNCLASSIFIED'? -> MOVE TO 'UNCLASSIFIED'.
4. Is 'SITUATIONAL' being used for anything other than major life tragedies? -> IF SO, REASSIGN IT.
5. Is loan 'purpose', 'intent', or 'motive' in 'INSTITUTIONAL and FINANCIAL'? -> MOVE TO 'VALUES, ATTITUDES and BEHAVIORAL'.
6. Is 'age', 'gender', or 'marital status' in 'SOCIOECONOMIC'? -> MOVE TO 'DEMOGRAPHIC'.

Return ONLY the corrected JSON object. No explanations.
JSON TO AUDIT: {json_original}
"""

def extrair_json_dict(texto):
    texto_limpo = texto.strip()
    inicio = texto_limpo.find('{')
    fim = texto_limpo.rfind('}') + 1
    if inicio != -1 and fim != -1:
        return json.loads(texto_limpo[inicio:fim])
    raise ValueError("Nenhum objeto JSON válido encontrado na resposta.")

# ---------------------------------------------------------
# 4. Construção dos Lotes COM CONTEXTO (CORRIGIDO)
# ---------------------------------------------------------
# Agrupamos as variáveis por dataset. O modelo recebe tudo de uma vez.
datasets_agrupados = df_clear.groupby('id')['Col'].apply(list).to_dict()

lotes_de_variaveis = list(datasets_agrupados.values())
ids_dos_lotes = list(datasets_agrupados.keys()) # Mantemos o rastreio da origem

# ---------------------------------------------------------
# 5. Passagem 1: Classificação Inicial
# ---------------------------------------------------------
print(f"\nA processar Passagem 1 ({len(lotes_de_variaveis)} datasets identificados)...")
mensagens_classificacao = []

for lote_atual in lotes_de_variaveis:
    prompt_formatado = prompt_classificacao.format(lote=lote_atual)
    mensagens_classificacao.append([{"role": "user", "content": prompt_formatado}])

resultados_classificacao = llm.chat(
    messages=mensagens_classificacao, 
    sampling_params=sampling_params, 
    use_tqdm=True
)

# ---------------------------------------------------------
# 6. Preparação e Passagem 2: Auditoria (CORRIGIDO)
# ---------------------------------------------------------
print("\nA preparar e processar Passagem 2 (Reflexão)...")
mensagens_reflexao = []
ids_aprovados_para_reflexao = []

# Agora zipamos com os IDs para não nos perdermos
for id_dataset, output in zip(ids_dos_lotes, resultados_classificacao):
    resp_texto = output.outputs[0].text
    try:
        json_preliminar = extrair_json_dict(resp_texto)
        prompt_ref_formatado = prompt_reflexao.format(json_original=json.dumps(json_preliminar))
        
        mensagens_reflexao.append([{"role": "user", "content": prompt_ref_formatado}])
        ids_aprovados_para_reflexao.append(id_dataset)
    except Exception as e:
        print(f"Erro no dataset {id_dataset} (Passagem 1): {str(e)[:50]}")

resultados_reflexao = llm.chat(
    messages=mensagens_reflexao, 
    sampling_params=sampling_params, 
    use_tqdm=True
)

# ---------------------------------------------------------
# 7. Atualização do Dicionário e Exportação (CORRIGIDO)
# ---------------------------------------------------------
print("\nA consolidar os resultados finais...")
registros_finais = []

for id_dataset, output in zip(ids_aprovados_para_reflexao, resultados_reflexao):
    resp_texto = output.outputs[0].text
    try:
        json_final = extrair_json_dict(resp_texto)
        # Reconstruímos a relação ID -> Variável -> Categoria com a nomenclatura exata
        for variavel, categoria in json_final.items():
            registros_finais.append({
                'id': id_dataset,
                'Col': variavel,
                'Col_Standardized': categoria # Nomenclatura compatível com os gráficos!
            })
    except Exception as e:
        print(f"Erro no dataset {id_dataset} (Passagem 2): {str(e)[:50]}")

# Transformamos em DataFrame
df_classificacoes_llm = pd.DataFrame(registros_finais)

# Cruzamento final 100% seguro (Left Join usando ID e Col) 
# Isso garante que as 896 linhas originais sejam mantidas
df_final_mapeado = pd.merge(
    df_clear, 
    df_classificacoes_llm, 
    on=['id', 'Col'], 
    how='left'
)

caminho_saida = 'MacroTaxonomyClassification_UR.csv'
df_final_mapeado.to_csv(caminho_saida, index=False)
print(f"\nProcessamento concluído com sucesso!")
