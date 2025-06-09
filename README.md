# LLM Chat Web App com Llama 3 (Ollama)

Este projeto é uma aplicação web de chat com IA, utilizando o modelo **Llama 3** rodando localmente via [Ollama](https://ollama.ai/). O frontend é moderno, responsivo e exibe as respostas do modelo em tempo real, com formatação Markdown.

---

## Funcionalidades
- Chat com IA local, sem custos de API
- Respostas em tempo real (streaming)
- Suporte a Markdown nas respostas
- Interface web moderna e responsiva

---

## Requisitos
- **Windows** (também funciona em Mac e Linux)
- **Python 3.8+**
- **Ollama** instalado
- Navegador moderno (Chrome, Edge, Firefox, etc.)

---

## Passo a Passo para rodar o projeto

### 1. Instale o Ollama
- Baixe em: https://ollama.ai/download
- Instale normalmente e abra o Ollama (procure por "Ollama" no menu iniciar e abra o app)

### 2. Baixe o modelo Llama 3
Abra o terminal (Prompt de Comando ou PowerShell) e execute:
```bash
ollama pull llama3
```

### 3. Instale as dependências Python
No terminal, dentro da pasta do projeto, execute:
```bash
python -m pip install -r requirements.txt
```

### 4. Rode o servidor Flask
No terminal, ainda na pasta do projeto, execute:
```bash
python app.py
```

### 5. Acesse o app
Abra o navegador e acesse:
```
http://localhost:5000
```

---

## Estrutura do Projeto
```
LLM/
├── app.py                # Backend Flask
├── requirements.txt      # Dependências Python
├── README.md             # Este arquivo
├── templates/
│   └── index.html        # Frontend HTML
└── static/
    ├── css/
    │   └── style.css     # Estilos
    └── js/
        └── main.js       # Lógica do chat
```

---

## Histórico do Processo
- Inicialmente, tentamos usar modelos pequenos (DistilGPT2, GPT2, BLOOM) via Hugging Face, mas a qualidade das respostas era ruim.
- Testamos também rodar modelos via Ollama, que oferece modelos otimizados para chat local.
- O projeto foi ajustado para usar o **Llama 3** via Ollama, com streaming de resposta e renderização Markdown no frontend.
- O frontend foi melhorado para exibir as respostas em tempo real e com formatação.

---

## Dicas e Observações
- O Ollama precisa estar rodando em segundo plano para o chat funcionar.
- O modelo Llama 3 será baixado apenas na primeira vez (pode demorar alguns minutos).
- O app funciona 100% offline após o download do modelo.
- Se quiser usar outro modelo do Ollama, basta mudar o campo `"model": "llama3"` no `app.py` para o nome do modelo desejado (ex: "phi3", "mistral", etc).

---

## Problemas comuns
- **Erro de conexão com Ollama:** Certifique-se de que o Ollama está aberto e o modelo foi baixado.
- **Porta 11434 ocupada:** O Ollama usa essa porta por padrão. Feche outros apps que possam estar usando.
- **Respostas lentas:** O desempenho depende do seu computador. Modelos maiores exigem mais RAM/CPU.

---

## Créditos
- [Ollama](https://ollama.ai/)
- [Meta Llama 3](https://ai.meta.com/llama/)
- [Marked.js](https://marked.js.org/) para renderização Markdown

---

Se tiver dúvidas, abra uma issue ou entre em contato! 