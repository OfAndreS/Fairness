import pandas as pd
import json
import os
from tqdm import tqdm
from vllm import LLM, SamplingParams

# Inicialização do motor vLLM com Automatic Prefix Caching ativado
llm = LLM(
    model="/mnt/modelo",
    dtype="bfloat16",
    trust_remote_code=True,
    gpu_memory_utilization=0.95,  
    max_model_len=8192,
    enable_prefix_caching=True 
)

# Mantemos a temperatura baixa para precisão absoluta
sampling_params = SamplingParams(
    temperature=0.0, 
    max_tokens=2500
)

# 1. Carregamento inicial das bases com os caminhos do repositório
df_alvo = pd.read_csv('Data/Classification/SplitMacroTC.csv')
ficheiro_ref = 'Data/PosProcessed/PosArticleVars.csv'
ficheiro_saida = 'Data/Classification/MicroTaxonomyClassification.csv'

# Parâmetro de segurança para o contexto do prompt
MAX_EXEMPLOS_POR_CATEGORIA = 12

def carregar_vocabulario_atualizado():
    df_ref = pd.read_csv(ficheiro_ref)
    vocab = {}
    grupos = df_ref['Grupo de Variáveis'].unique()
    for grupo in grupos:
        conceitos = df_ref[df_ref['Grupo de Variáveis'] == grupo]['Nome das variáveis'].dropna().unique().tolist()
        conceitos_limpos = [str(c).strip().lower().replace(' ', '_').replace('.', '') for c in conceitos]
        conceitos_unicos = list(dict.fromkeys(conceitos_limpos))
        vocab[grupo] = conceitos_unicos[-MAX_EXEMPLOS_POR_CATEGORIA:] 
    return vocab

# 2. Construção do Prompt com as Regras de Unificação (Alteração Principal)
def construir_mensagem_lote(lote_variaveis, vocab_atual):
    prompt = (
        "System Role: You are an advanced AI expert in data engineering and schema matching.\n"
        "Objective: Map raw database column names to a predefined vocabulary OR suggest a new canonical concept if no fit exists.\n\n"
        "Strict Execution Rules:\n"
        "1. Priority Mapping: Try to map each raw variable to an existing concept in the ALLOWED VOCABULARY.\n"
        "2. Canonical Unification (CRITICAL):\n"
        "   - Use 'loan_term_duration' for any duration/tenure/repayment period of a loan.\n"
        "   - Use 'loan_original_amount' for any requested, sanctioned, or initial principal amount.\n"
        "   - Use 'credit_line_count' (singular) for any count of credit lines or accounts.\n"
        "   - Use 'default_indicator' for any status/flag/indicator of non-payment or default.\n"
        "   - Use 'borrower_location_state' instead of 'residential_state'.\n"
        "3. Temporal Abstraction: Canonical concepts MUST be time-agnostic. Strip away specific timeframes (e.g., '30d', '12m') from the concept name.\n"
        "4. New Concept Creation: Create a new 'conceito_padronizado' in lowercase snake_case ONLY if no existing concept is semantically ideal.\n"
        "5. Output Format: Respond STRICTLY with a JSON array. No text, no markdown.\n\n"
        "ALLOWED VOCABULARY:\n"
    )
    
    for cat, conceitos in vocab_atual.items():
        prompt += f"[{cat}]: {','.join(conceitos)}\n"
        
    prompt += "\nInput Data (Original Variable | Macro Category):\n"
    for item in lote_variaveis:
        prompt += f"{item['Col']}|{item['Col_Standardized']}\n"
        
    prompt += (
        "\nExpected JSON Structure:\n"
        "[\n"
        "  {\n"
        "    \"variavel_original\": \"name\",\n"
        "    \"conceito_padronizado\": \"canonical_name\",\n"
        "    \"macro_categoria\": \"CATEGORY\",\n"
        "    \"nova_instancia\": true/false,\n"
        "    \"justificativa\": \"reason\"\n"
        "  }\n"
        "]\n\n"
        "JSON:\n["
    )
    return [{"role": "user", "content": prompt}]

def processar_inferencia_lote(lote, vocab_atual):
    mensagens = construir_mensagem_lote(lote, vocab_atual)
    outputs = llm.chat(messages=mensagens, sampling_params=sampling_params, use_tqdm=False)
    resposta = outputs[0].outputs[0].text.strip()
    
    if not resposta.startswith('['): resposta = '[' + resposta
    inicio_json = resposta.find('[')
    fim_json = resposta.rfind(']') + 1
    
    if inicio_json != -1:
        return json.loads(resposta[inicio_json:fim_json])
    return []

# 3. Execução com Ciclo de Retroalimentação
variaveis_para_processar = df_alvo[['Col', 'Col_Standardized']].to_dict('records')
resultados_finais = []
tamanho_lote_inicial = 5

print(f"Iniciando processamento com regras de unificação para {len(variaveis_para_processar)} variáveis...")

idx = 0
pbar = tqdm(total=len(variaveis_para_processar), desc="Processando variáveis")

while idx < len(variaveis_para_processar):
    tamanho_atual = tamanho_lote_inicial
    sucesso_lote = False
    
    while tamanho_atual > 0 and not sucesso_lote:
        lote = variaveis_para_processar[idx:idx + tamanho_atual]
        vocab_atual = carregar_vocabulario_atualizado()
        
        try:
            novos_dados = processar_inferencia_lote(lote, vocab_atual)
            sucesso_lote = True 
            
            novas_entradas_ref = []
            for item in novos_dados:
                if item.get('nova_instancia') is True:
                    # Limpeza forçada para garantir snake_case e remover redundâncias óbvias
                    conceito_limpo = str(item['conceito_padronizado']).strip().lower().replace(' ', '_').replace('.', '').replace('_rate_rate', '_rate')
                    item['conceito_padronizado'] = conceito_limpo 
                    
                    nova_linha = {
                        'Nome das variáveis': conceito_limpo,
                        'Grupo de Variáveis': item['macro_categoria']
                    }
                    novas_entradas_ref.append(nova_linha)
            
            if novas_entradas_ref:
                df_temp = pd.DataFrame(novas_entradas_ref).drop_duplicates()
                df_current_ref = pd.read_csv(ficheiro_ref)
                
                # Normalização para comparação
                df_current_ref['Nome das variáveis'] = df_current_ref['Nome das variáveis'].astype(str).str.strip().str.lower().str.replace(' ', '_')
                
                df_temp = df_temp[~df_temp['Nome das variáveis'].isin(df_current_ref['Nome das variáveis'])]
                
                if not df_temp.empty:
                    df_temp.to_csv(ficheiro_ref, mode='a', header=False, index=False)
            
            resultados_finais.extend(novos_dados)
            pd.DataFrame(resultados_finais).to_csv(ficheiro_saida, index=False, encoding='utf-8')
                
            idx += tamanho_atual 
            pbar.update(tamanho_atual) 
            
        except Exception as e:
            print(f"\nErro no lote. Reduzindo tamanho: {str(e)[:50]}")
            tamanho_atual = tamanho_atual // 2 
            
    if not sucesso_lote:
        idx += 1
        pbar.update(1)

pbar.close()
print(f"\nProcessamento concluído. Verifique '{ficheiro_saida}'.")