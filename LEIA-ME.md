# Conferência de comunicações e tarefas — Desafio de Estágio em TI

## O que é
Protótipo em Python + Streamlit para relacionar um relatório de tarefas e um relatório de comunicações processuais fictícias, destacar situações para conferência humana e exportar resultados para Excel.

## Requisitos
- Python 3.10 ou mais recente
- VS Code (opcional, mas recomendado)
- Os dois relatórios Excel com as mesmas colunas/estrutura do desafio

## Como executar no Windows
1. Extraia a pasta ZIP.
2. Abra a pasta no VS Code.
3. Abra o terminal integrado: **Terminal > Novo Terminal**.
4. Crie um ambiente virtual:
   ```powershell
   py -m venv .venv
   ```
5. Ative-o:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   Se o PowerShell bloquear a ativação, abra um terminal Command Prompt no VS Code e use:
   ```cmd
   .venv\Scripts\activate.bat
   ```
6. Instale as bibliotecas:
   ```powershell
   python -m pip install -r requirements.txt
   ```
7. Inicie o aplicativo:
   ```powershell
   python -m streamlit run app.py
   ```
8. O navegador abrirá a tela do programa. Envie o Relatório A e o Relatório B na barra lateral.
9. Confira os filtros e clique em **Baixar análise em Excel** para exportar o resultado.

## Como usar novas exportações
Substitua os arquivos na tela por novos arquivos `.xlsx` que mantenham os nomes das colunas esperadas. O programa usa a aba `TAREFAS` quando disponível e a aba `COMUNICACOES` quando disponível; se não encontrar esses nomes, tenta a primeira aba. A estrutura das colunas obrigatórias deve permanecer igual.

## Regras e limitações
- A data de referência inicial é 30/10/2026, conforme o desafio. Pode ser alterada na barra lateral.
- O cruzamento inicial usa `Processo fictício`, e a relação entre comunicação e tarefa é estimada por palavras do tipo de comunicação e da atividade.
- Os resultados são heurísticos: podem existir falsos positivos ou falsos negativos, especialmente quando as atividades têm descrições inesperadas.
- Registro repetido e movimento informativo são tratados separadamente para evitar criar alertas automáticos desnecessários.
- Tarefas concluídas/canceladas não contam como pendências abertas.
- Prazo interno vencido é alerta operacional, não prova de perda de prazo judicial.
- O programa não acessa Projuris, Google Drive, sistemas internos ou serviços de IA.
- Toda sugestão deve ser validada por uma pessoa autorizada antes de qualquer providência.

## Como apresentar
Explique que o protótipo prioriza transparência: cada resultado mostra a classificação, a justificativa e as tarefas consideradas. A regra de correspondência pode ser melhorada após validação da Controladoria com exemplos autorizados.
