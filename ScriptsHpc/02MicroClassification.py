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

# Mantemos a temperatura baixa para precisão, mas permitimos a "escolha" de novos termos
sampling_params = SamplingParams(
    temperature=0.0, 
    max_tokens=2500
)

# 1. Carregamento inicial das bases
df_alvo = pd.read_csv('MacroTaxonomyClassification.csv')
ficheiro_ref = 'PosArticleVars.csv'

# Parâmetro de segurança para evitar estouro de tokens
MAX_EXEMPLOS_POR_CATEGORIA = 50

# Função para carregar o vocabulário atualizado do disco (com limpeza em tempo real)
def carregar_vocabulario_atualizado():
    df_ref = pd.read_csv(ficheiro_ref)
    vocab = {}
    grupos = df_ref['Grupo de Variáveis'].unique()
    for grupo in grupos:
        conceitos = df_ref[df_ref['Grupo de Variáveis'] == grupo]['Nome das variáveis'].dropna().unique().tolist()
        
        # SOLUÇÃO 1: Limpeza e conversão on-the-fly para snake_case
        conceitos_limpos = [str(c).strip().lower().replace(' ', '_').replace('.', '') for c in conceitos]
        
        # Removemos possíveis duplicatas criadas pela limpeza (ex: 'Age' e 'age' viram 'age')
        conceitos_unicos = list(dict.fromkeys(conceitos_limpos))
        
        vocab[grupo] = conceitos_unicos[-MAX_EXEMPLOS_POR_CATEGORIA:] 
    return vocab

# 2. Construção do Prompt com Compactação e Abstração Temporal
def construir_mensagem_lote(lote_variaveis, vocab_atual):
    prompt = (
            "System Role: You are an advanced AI expert in data engineering and schema matching.\n"
            "Objective: Map raw database column names to a predefined vocabulary OR suggest a new canonical concept if no fit exists.\n\n"
            "Strict Execution Rules:\n"
            "1. Priority Mapping: Try to map each raw variable to an existing concept listed under its macro-category.\n"
            "2. New Concept Creation: You MUST create a new 'conceito_padronizado' in lowercase snake_case if no existing concept is semantically ideal OR if there is a mismatch in the metric type. Never map a 'count' to an 'amount', a 'ratio' to a 'duration', or a 'balance' to a 'delinquency'.\n"
            "3. Consistency: If you create a new concept, ensure it is reusable for similar variables.\n"
            "4. Temporal Abstraction (CRITICAL): Canonical concepts MUST be time-agnostic. Strip away specific timeframes, durations, or windows (e.g., '30d', '12m', 'last_6_months') from the 'conceito_padronizado'. For example, both 'inq_last_12m' and 'inq_last_6m' should map to 'credit_inquiry_count'.\n"
            "5. Output Format: Respond STRICTLY with a JSON array. No markdown, no text.\n\n"
            "ALLOWED VOCABULARY:\n"
        )
    
    # Compactação: Formato mais denso para economizar tokens
    for cat, conceitos in vocab_atual.items():
        prompt += f"[{cat}]: {','.join(conceitos)}\n"
        
    prompt += "\nInput Data (ID | Original Variable | Macro Category):\n"
    for item in lote_variaveis:
        prompt += f"{item['id']}|{item['Col']}|{item['Col_Standardized']}\n"
        
    prompt += (
        "\nExpected JSON Structure:\n"
        "[\n"
        "  {\n"
        "    \"id\": \"dataset_id\",\n"
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

# 3. Execução com Ciclo de Retroalimentação e Batch Sizing Dinâmico
variaveis_para_processar = df_alvo[['id', 'Col', 'Col_Standardized']].to_dict('records')
resultados_finais = []
tamanho_lote_inicial = 5
ficheiro_saida = 'MicroTaxonomyClassification_UR.csv'

print(f"A iniciar processamento evolutivo de {len(variaveis_para_processar)} variáveis...")

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
                    # Garantir que mesmo que o modelo falhe e envie algo sujo, limpamos antes de gravar no CSV
                    conceito_limpo = str(item['conceito_padronizado']).strip().lower().replace(' ', '_').replace('.', '')
                    item['conceito_padronizado'] = conceito_limpo # Atualiza no JSON de saída
                    
                    nova_linha = {
                        'Nome das variáveis': conceito_limpo,
                        'Grupo de Variáveis': item['macro_categoria']
                    }
                    novas_entradas_ref.append(nova_linha)
            
            if novas_entradas_ref:
                df_temp = pd.DataFrame(novas_entradas_ref).drop_duplicates()
                df_current_ref = pd.read_csv(ficheiro_ref)
                
                # Normalizar a referência atual para evitar duplicatas ocultas
                df_current_ref['Nome das variáveis'] = df_current_ref['Nome das variáveis'].astype(str).str.strip().str.lower().str.replace(' ', '_').str.replace('.', '')
                
                df_temp = df_temp[~df_temp['Nome das variáveis'].isin(df_current_ref['Nome das variáveis'])]
                
                if not df_temp.empty:
                    df_temp.to_csv(ficheiro_ref, mode='a', header=False, index=False)
            
            resultados_finais.extend(novos_dados)
            
            df_resultados = pd.DataFrame(resultados_finais)
            
            # Reorganizamos a estrutura para deixar o CSV elegante e legível
            colunas_ideais = ['id', 'variavel_original', 'conceito_padronizado', 'macro_categoria', 'nova_instancia', 'justificativa']
            colunas_finais = [c for c in colunas_ideais if c in df_resultados.columns]
            df_resultados = df_resultados[colunas_finais]
            
            df_resultados.to_csv(ficheiro_saida, index=False, encoding='utf-8')
                
            idx += tamanho_atual 
            pbar.update(tamanho_atual) 
            
        except Exception as e:
            print(f"\nErro com lote de tamanho {tamanho_atual}. Causado por: {str(e)[:50]}... Tentando reduzir o lote.")
            tamanho_atual = tamanho_atual // 2 
            
    if not sucesso_lote:
        print(f"\nFalha crítica: Não foi possível processar a variável no índice {idx}. Saltando...")
        idx += 1
        pbar.update(1)

pbar.close()
print(f"\nProcessamento concluído. Os resultados foram guardados em '{ficheiro_saida}'.")
