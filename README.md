# 🚀 Estimador Técnico IA 

O **Estimador Técnico IA ** é uma ferramenta poderosa desenvolvida em Python e Streamlit, projetada para automatizar e profissionalizar o processo de criação de propostas técnicas e estimativas de esforço para projetos de software. Utilizando o poder da Inteligência Artificial (via OpenRouter/GPT-4o), o sistema analisa documentos de escopo e gera um detalhamento completo de horas, custos, cronograma e riscos.

## ✨ Funcionalidades Principais

*   **📄 Extração Inteligente de Escopo:** Suporte para leitura de arquivos PDF, DOCX e TXT.
*   **🤖 Análise via IAw:** Utiliza modelos avançados para decompor o escopo em atividades técnicas detalhadas.
*   **⚙️ Configuração Dinâmica (YAML):** Permite configurar equipe, senioridade, custos por hora, margens de risco e tabelas de esforço base sem alterar o código.
*   **🛡️ Blindagem de Cálculos:** Realiza o re-cálculo matemático via Python após a sugestão da IA para garantir precisão financeira.
*   **📅 Cronograma Automático:** Sugestão de foco semanal e distribuição de responsabilidades.
*   **📥 Exportação em PDF:** Gera uma proposta profissional pronta para envio, com logo personalizada e tabelas detalhadas.
*   **🛠️ Regra de Manutenção Integrada:** Prioriza automaticamente custos de manutenção (alteração de campos, ajustes simples) quando o escopo indica ajustes em funcionalidades já existentes.

## 🛠️ Tecnologias Utilizadas

*   **[Streamlit](https://streamlit.io/):** Interface web rápida e interativa.
*   **[OpenRouter AI](https://openrouter.ai/):** Integração com modelos de linguagem de última geração.
*   **[ReportLab](https://www.reportlab.com/):** Geração robusta de documentos PDF.
*   **[PyPDF2](https://pypdf2.readthedocs.io/) & [python-docx](https://python-docx.readthedocs.io/):** Extração de texto de documentos.
*   **[PyYAML](https://pyyaml.org/):** Gestão de configurações flexíveis.

## 📋 Pré-requisitos

*   Python 3.9 ou superior.
*   Uma chave de API do [OpenRouter](https://openrouter.ai/).

## 🚀 Como Executar

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/seu-usuario/GeradorEstimativaIA.git
    cd GeradorEstimativaIA
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # Linux/MacOS
    source venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Execute a aplicação:**
    ```bash
    streamlit run main.py
    ```

## ⚙️ Configuração do YAML

O sistema utiliza um template YAML para definir as regras de negócio. Você pode ajustar:

*   **Equipe:** Cargos, senioridade e `custo_hora`.
*   **Regras de Negócio:** Margem de risco e multiplicadores para cenários específicos (ex: legado, falta de documentação).
*   **Tabela de Esforço Base:** Definição de horas padrão para tarefas comuns.
*   **Distribuição de Esforço:** Percentual de participação de cada perfil no projeto.

### ⚠️ Regra de Manutenção (Prioridade Máxima)
O motor de IA está instruído a identificar se a funcionalidade já existe. Se o documento indicar apenas uma alteração ou troca de campo, ele deve obrigatoriamente usar o item `manutencao_alteracao_campo` (2h) e complexidade `muito_baixa` (0.5), evitando cobranças indevidas de novas integrações.

## 📁 Estrutura do Projeto

```text
.
├── main.py              # Aplicação principal Streamlit
├── requirements.txt     # Dependências do projeto
├── README.md            # Documentação
└── (outros arquivos de suporte)
```

## 🤝 Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir Issues ou enviar Pull Requests.

---
Desenvolvido para transformar escopos complexos em propostas comerciais precisas.