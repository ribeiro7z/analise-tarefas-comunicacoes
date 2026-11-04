# Explicação da solução — Desafio em TI

**Ferramentas utilizadas:** Python, Streamlit, pandas e openpyxl. O Python realiza a leitura e análise dos dados; o Streamlit oferece uma interface simples para carregar os relatórios, visualizar alertas e exportar os resultados em Excel.

**Funcionamento:** a solução importa os relatórios de tarefas e comunicações, relaciona os registros pelo campo “Processo fictício” e procura atividades potencialmente compatíveis com o tipo de comunicação. Considera a situação da tarefa, o prazo interno e as descrições que indicam registro repetido ou movimento informativo. Cada resultado inclui uma justificativa e as tarefas que devem ser conferidas. É possível substituir os arquivos por novas exportações com a mesma estrutura.

**Limitações:** o cruzamento de atividades é baseado em regras e palavras-chave, portanto não compreende todo o contexto e pode gerar alertas que precisam ser corrigidos por uma pessoa. Ausência de tarefa no recorte não comprova falha, e prazo interno vencido não comprova perda de prazo oficial. O protótipo usa apenas os arquivos fictícios fornecidos e não se conecta a sistemas do escritório.

**Uso responsável de IA:** uma etapa futura poderia usar Claude ou outra IA para sugerir se a descrição de uma tarefa parece relacionada à comunicação, sempre exibindo a justificativa e mantendo a decisão final com a equipe. Antes de usar IA, seria necessário obter autorização, minimizar os dados enviados, remover identificadores pessoais quando possível e não enviar informações de clientes a serviços externos sem aprovação. Os resultados deveriam ser validados por uma pessoa.

**Melhoria tecnológica sugerida:** criar uma fila de alertas priorizada por prazo interno, tipo de comunicação e responsável, com registro da revisão humana e possibilidade de ajustar as regras com a Controladoria.
