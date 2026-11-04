from datetime import date
from io import BytesIO
import re
import pandas as pd
import streamlit as st

DATA_REFERENCIA_PADRAO = date(2026, 10, 30)

COL_TAREFA = {
    "processo": "Processo fictício",
    "atividade": "Atividade",
    "responsavel": "Responsável",
    "situacao": "Situação",
    "criado": "Data de criação",
    "prazo_interno": "Prazo previsto (interno)",
    "prazo_fatal": "Prazo fatal (oficial)",
}
COL_COM = {
    "codigo": "Código da comunicação",
    "processo": "Processo fictício",
    "data": "Data do registro",
    "tipo": "Tipo de comunicação",
    "descricao": "Descrição resumida",
}

def normalizar(valor):
    if pd.isna(valor):
        return ""
    texto = str(valor).strip().lower()
    texto = texto.replace("á", "a").replace("à", "a").replace("ã", "a").replace("â", "a")
    texto = texto.replace("é", "e").replace("ê", "e").replace("í", "i")
    texto = texto.replace("ó", "o").replace("õ", "o").replace("ô", "o")
    texto = texto.replace("ú", "u").replace("ç", "c")
    texto = re.sub(r"\s+", " ", texto)
    return texto

def carregar_excel(arquivo, aba_preferida):
    conteudo = arquivo.getvalue()
    xls = pd.ExcelFile(BytesIO(conteudo))
    aba = aba_preferida if aba_preferida in xls.sheet_names else xls.sheet_names[0]
    return pd.read_excel(BytesIO(conteudo), sheet_name=aba)

def preparar_tarefas(df):
    df = df.copy()
    obrigatorias = list(COL_TAREFA.values())
    faltantes = [c for c in obrigatorias if c not in df.columns]
    if faltantes:
        raise ValueError("Relatório de tarefas sem estas colunas obrigatórias: " + ", ".join(faltantes))
    for c in ["Data de criação", "Prazo previsto (interno)", "Prazo fatal (oficial)"]:
        df[c] = pd.to_datetime(df[c], errors="coerce").dt.date
    df["__processo_norm"] = df["Processo fictício"].map(normalizar)
    df["__atividade_norm"] = df["Atividade"].map(normalizar)
    df["__situacao_norm"] = df["Situação"].map(normalizar)
    return df

def preparar_comunicacoes(df):
    df = df.copy()
    obrigatorias = list(COL_COM.values())
    faltantes = [c for c in obrigatorias if c not in df.columns]
    if faltantes:
        raise ValueError("Relatório de comunicações sem estas colunas obrigatórias: " + ", ".join(faltantes))
    df["Data do registro"] = pd.to_datetime(df["Data do registro"], errors="coerce").dt.date
    df["__processo_norm"] = df["Processo fictício"].map(normalizar)
    df["__tipo_norm"] = df["Tipo de comunicação"].map(normalizar)
    df["__descricao_norm"] = df["Descrição resumida"].map(normalizar)
    return df

def eh_repetida(com):
    return "repetido" in com["__descricao_norm"] or "reenvio" in com["__descricao_norm"]

def eh_informativa(com):
    return "informativo" in com["__descricao_norm"] or "certidao informativa" in com["__tipo_norm"]

def termos_esperados(com):
    tipo = com["__tipo_norm"]
    desc = com["__descricao_norm"]
    if "pericia medica judicial" in tipo:
        return ["pericia", "orientacao pericial", "orientacao para pericia", "acompanhamento pericial"]
    if "avaliacao social" in tipo:
        return ["avaliacao social", "orientacao social", "acompanhamento social"]
    if "pericia administrativa" in tipo:
        return ["pericia administrativa", "pericia medica - inss", "orientacao pericial", "acompanhamento pericial"]
    if "intimacao para manifestacao" in tipo:
        return ["manifestacao", "intimacao", "responder intimacao", "providencia processual"]
    if "pericia" in desc:
        return ["pericia", "orientacao pericial", "acompanhamento pericial"]
    if "avaliacao social" in desc:
        return ["avaliacao social", "orientacao social"]
    if "intimacao" in desc or "manifestacao" in desc:
        return ["manifestacao", "intimacao", "providencia processual"]
    return []

def atividade_compativel(atividade, termos):
    a = normalizar(atividade)
    return any(normalizar(t) in a for t in termos)

def classificar(comunicacoes, tarefas, data_ref):
    resultados = []
    for _, com in comunicacoes.iterrows():
        processo = com["Processo fictício"]
        cod_com = com["Código da comunicação"]
        tipo = com["Tipo de comunicação"]
        descricao = com["Descrição resumida"]
        data_reg = com["Data do registro"]
        proc_norm = com["__processo_norm"]
        do_processo = tarefas[tarefas["__processo_norm"] == proc_norm].copy()
        tarefas_abertas = do_processo[~do_processo["__situacao_norm"].str.contains(r"concluida|cancelada", regex=True, na=False)]
        termos = termos_esperados(com)
        candidatas = tarefas_abertas[tarefas_abertas["Atividade"].apply(lambda x: atividade_compativel(x, termos))] if termos else tarefas_abertas.iloc[0:0]
        tarefas_fechadas_compativeis = do_processo[
            do_processo["__situacao_norm"].str.contains(r"concluida|cancelada", regex=True, na=False)
            & do_processo["Atividade"].apply(lambda x: atividade_compativel(x, termos))
        ] if termos else do_processo.iloc[0:0]

        if eh_repetida(com):
            status = "Registro repetido — revisar agrupamento"
            motivo = "A descrição indica reenvio/registro repetido. Não conte automaticamente como uma nova demanda; confira a comunicação original."
            prioridade = "Baixa"
        elif eh_informativa(com):
            status = "Informativa — sem alerta automático"
            motivo = "A descrição classifica o movimento como informativo e diz que ele não necessariamente exige tarefa."
            prioridade = "Baixa"
        elif candidatas.empty and do_processo.empty:
            status = "Processo não localizado nas tarefas"
            motivo = "Não há tarefa com este identificador de processo no recorte fornecido. Isso é um alerta de conferência, não prova de falha."
            prioridade = "Alta"
        elif not candidatas.empty:
            vencidas = candidatas[candidatas["Prazo previsto (interno)"].apply(lambda d: isinstance(d, date) and d < data_ref)]
            situacoes_confirmar = candidatas[candidatas["__situacao_norm"].str.contains("confirmar", na=False)]
            if not vencidas.empty:
                status = "Tarefa compatível encontrada — prazo interno vencido"
                motivo = "Foi encontrada atividade potencialmente relacionada, mas o prazo interno está anterior à data de referência. Verifique a situação com a equipe; isso não comprova perda de prazo oficial."
                prioridade = "Alta"
            elif not situacoes_confirmar.empty:
                status = "Tarefa compatível encontrada — situação a confirmar"
                motivo = "Existe atividade potencialmente relacionada, mas sua situação está marcada como 'A confirmar'. Requer conferência humana."
                prioridade = "Média"
            else:
                status = "Possível acompanhamento encontrado"
                motivo = "Foi encontrada tarefa aberta no mesmo processo com atividade compatível com o tipo de comunicação. A correspondência precisa ser confirmada por uma pessoa."
                prioridade = "Média"
        elif not tarefas_fechadas_compativeis.empty:
            status = "Só há tarefa compatível concluída/cancelada"
            motivo = "A atividade relacionada encontrada está concluída ou cancelada; não foi localizada atividade compatível aberta. Confira se é necessário novo acompanhamento."
            prioridade = "Média"
        elif do_processo.empty:
            status = "Processo não localizado nas tarefas"
            motivo = "Não há tarefa com este identificador de processo no recorte fornecido. Isso é um alerta de conferência, não prova de falha."
            prioridade = "Alta"
        else:
            status = "Tarefas no processo, mas sem correspondência clara"
            motivo = "Há tarefas para o processo, porém as descrições não correspondem claramente ao tipo de comunicação. Confira manualmente antes de concluir que falta acompanhamento."
            prioridade = "Média"

        tarefas_ref = candidatas if not candidatas.empty else (tarefas_fechadas_compativeis if not tarefas_fechadas_compativeis.empty else do_processo)
        codigos = "; ".join(str(x) for x in tarefas_ref["Código da tarefa"].head(5).tolist()) if not tarefas_ref.empty else "Nenhuma"
        atividades = "; ".join(str(x) for x in tarefas_ref["Atividade"].head(5).tolist()) if not tarefas_ref.empty else "Nenhuma localizada"
        prazos = "; ".join(d.strftime("%d/%m/%Y") if isinstance(d, date) else "Sem data" for d in tarefas_ref["Prazo previsto (interno)"].head(5).tolist()) if not tarefas_ref.empty else "—"

        resultados.append({
            "Código da comunicação": cod_com,
            "Processo fictício": processo,
            "Data do registro": data_reg,
            "Tipo de comunicação": tipo,
            "Resultado da análise": status,
            "Prioridade sugerida": prioridade,
            "Justificativa": motivo,
            "Tarefas relacionadas para conferência": codigos,
            "Atividades consideradas": atividades,
            "Prazo interno relacionado": prazos,
        })
    return pd.DataFrame(resultados)

st.set_page_config(page_title="Conferência de comunicações e tarefas", page_icon="🧾", layout="wide")
st.title("Conferência de comunicações e tarefas")
st.caption("Protótipo para dados fictícios. Os resultados são sugestões para conferência humana, não decisões jurídicas.")

with st.sidebar:
    st.header("1. Arquivos de entrada")
    tarefas_file = st.file_uploader("Relatório A — tarefas (.xlsx)", type=["xlsx"], key="tarefas")
    comunicacoes_file = st.file_uploader("Relatório B — comunicações (.xlsx)", type=["xlsx"], key="comunicacoes")
    st.divider()
    st.header("2. Parâmetros")
    data_ref = st.date_input("Data de referência", value=DATA_REFERENCIA_PADRAO)
    st.caption("O desafio determina 30/10/2026 como data de referência inicial. Ajuste apenas se estiver analisando outro recorte autorizado.")

if not tarefas_file or not comunicacoes_file:
    st.info("Envie os dois arquivos Excel na barra lateral para iniciar a análise.")
    st.markdown("""
    **O que este protótipo faz**
    - Relaciona registros pelo campo **Processo fictício**.
    - Procura atividades potencialmente relacionadas ao tipo de comunicação.
    - Identifica registros repetidos e movimentos informativos.
    - Considera a situação e o prazo interno das tarefas.
    - Permite baixar o resultado em Excel para revisão.
    """)
    st.stop()

try:
    tarefas_brutas = carregar_excel(tarefas_file, "TAREFAS")
    comunicacoes_brutas = carregar_excel(comunicacoes_file, "COMUNICACOES")
    tarefas = preparar_tarefas(tarefas_brutas)
    comunicacoes = preparar_comunicacoes(comunicacoes_brutas)
except Exception as e:
    st.error(f"Não foi possível ler os arquivos: {e}")
    st.stop()

resultados = classificar(comunicacoes, tarefas, data_ref)
total = len(resultados)
sem_correspondencia = resultados["Resultado da análise"].isin([
    "Processo não localizado nas tarefas",
    "Tarefas no processo, mas sem correspondência clara",
    "Só há tarefa compatível concluída/cancelada",
]).sum()
prioridade_alta = (resultados["Prioridade sugerida"] == "Alta").sum()
informativas = resultados["Resultado da análise"].str.startswith("Informativa").sum()
repetidas = resultados["Resultado da análise"].str.startswith("Registro repetido").sum()

st.subheader("Resumo da análise")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Comunicações", total)
c2.metric("Conferir correspondência", int(sem_correspondencia))
c3.metric("Prioridade alta", int(prioridade_alta))
c4.metric("Informativas", int(informativas))
c5.metric("Repetidas", int(repetidas))

st.subheader("Resultados")
filtro = st.multiselect(
    "Filtrar por resultado",
    options=sorted(resultados["Resultado da análise"].unique()),
    default=sorted(resultados["Resultado da análise"].unique()),
)
prioridade = st.multiselect(
    "Filtrar por prioridade",
    options=["Alta", "Média", "Baixa"],
    default=["Alta", "Média", "Baixa"],
)
visiveis = resultados[
    resultados["Resultado da análise"].isin(filtro)
    & resultados["Prioridade sugerida"].isin(prioridade)
].copy()
st.dataframe(visiveis, use_container_width=True, hide_index=True)

output = BytesIO()
with pd.ExcelWriter(output, engine="openpyxl") as writer:
    visiveis.to_excel(writer, sheet_name="Resultados filtrados", index=False)
    resultados.to_excel(writer, sheet_name="Análise completa", index=False)
    pd.DataFrame({
        "Métrica": ["Comunicações analisadas", "Prioridade alta", "Movimentos informativos", "Registros repetidos"],
        "Quantidade": [total, int(prioridade_alta), int(informativas), int(repetidas)]
    }).to_excel(writer, sheet_name="Resumo", index=False)
st.download_button(
    "Baixar análise em Excel",
    data=output.getvalue(),
    file_name="resultado_conferencia.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
st.caption("Importante: a correspondência é heurística, baseada em processo, tipo de comunicação e palavras da atividade. Revise os alertas; ausência no recorte não prova falha.")
