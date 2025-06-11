document.addEventListener('DOMContentLoaded', function () {
    const chatBox = document.getElementById('chat-box');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');

    function appendMessage(sender, text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message ' + sender;
        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble';
        bubble.textContent = text;
        messageDiv.appendChild(bubble);
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
        return bubble;
    }

    chatForm.addEventListener('submit', function (e) {
        e.preventDefault();
        const message = userInput.value.trim();
        if (!message) return;
        appendMessage('user', message);
        userInput.value = '';

        // Stream response from /api/chat
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        }).then(response => {
            if (!response.body) return;
            const reader = response.body.getReader();
            let aiMessage = '';
            // Cria o balão da IA uma vez
            const aiBubble = appendMessage('ai', '');
            function read() {
                reader.read().then(({ done, value }) => {
                    if (done) {
                        aiBubble.textContent = aiMessage;
                        return;
                    }
                    const chunk = new TextDecoder().decode(value);
                    aiMessage += chunk.replace(/^data: /gm, '');
                    aiBubble.textContent = aiMessage;
                    chatBox.scrollTop = chatBox.scrollHeight;
                    read();
                });
            }
            read();
        });
    });
}); 