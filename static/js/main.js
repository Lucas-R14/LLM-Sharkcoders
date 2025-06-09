document.addEventListener('DOMContentLoaded', () => {
    const chatContainer = document.getElementById('chatContainer');
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');

    function addMessage(message, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'assistant-message'}`;
        if (isUser) {
            messageDiv.textContent = message;
        } else {
            // Renderiza markdown como HTML
            messageDiv.innerHTML = marked.parse(message);
        }
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    async function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        // Disable input while processing
        userInput.disabled = true;
        sendButton.disabled = true;

        // Add user message to chat
        addMessage(message, true);
        userInput.value = '';

        // Cria um novo elemento para a resposta do assistente
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant-message';
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message }),
            });

            if (!response.body) throw new Error('No response body');
            const reader = response.body.getReader();
            let assistantText = '';
            const decoder = new TextDecoder();
            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                const chunk = decoder.decode(value, { stream: true });
                // Extrai o texto do formato SSE (data: ...\n\n)
                const matches = chunk.match(/data: ([^\n]*)/g);
                if (matches) {
                    for (const match of matches) {
                        const text = match.replace('data: ', '');
                        assistantText += text;
                        messageDiv.innerHTML = marked.parse(assistantText);
                        chatContainer.scrollTop = chatContainer.scrollHeight;
                    }
                }
            }
        } catch (error) {
            messageDiv.textContent = 'Error: Could not connect to the server';
        } finally {
            userInput.disabled = false;
            sendButton.disabled = false;
            userInput.focus();
        }
    }

    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
}); 