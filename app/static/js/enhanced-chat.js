// Enhanced Chat JavaScript with AI Services Integration
class EnhancedChat {
    constructor() {
        this.currentMode = 'text';
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.currentSession = null;
        this.servicesStatus = {};
        
        this.initializeElements();
        this.setupEventListeners();
        this.checkServicesStatus();
        
        // Check services status every 30 seconds
        setInterval(() => this.checkServicesStatus(), 30000);
    }
    
    initializeElements() {
        this.chatBox = document.getElementById('chat-box');
        this.chatForm = document.getElementById('chat-form');
        this.userInput = document.getElementById('user-input');
        this.imagePrompt = document.getElementById('image-prompt');
        this.audioControls = document.getElementById('audio-controls');
        this.imageMode = document.getElementById('image-mode');
        this.recordBtn = document.getElementById('record-btn');
        this.recordingStatus = document.getElementById('recording-status');
        this.loading = document.getElementById('loading');
        this.loadingText = document.getElementById('loading-text');
        this.sendBtn = document.getElementById('send-btn');
    }
    
    setupEventListeners() {
        this.chatForm.addEventListener('submit', (e) => this.handleSubmit(e));
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case '1':
                        e.preventDefault();
                        this.setMode('text');
                        break;
                    case '2':
                        e.preventDefault();
                        this.setMode('audio');
                        break;
                    case '3':
                        e.preventDefault();
                        this.setMode('image');
                        break;
                }
            }
        });
    }
    
    async checkServicesStatus() {
        try {
            const response = await fetch('/api/services/status');
            const data = await response.json();
            this.servicesStatus = data.services;
            this.updateStatusIndicators();
        } catch (error) {
            console.error('Error checking services status:', error);
        }
    }
    
    updateStatusIndicators() {
        Object.keys(this.servicesStatus).forEach(service => {
            const statusDot = document.getElementById(`status-${service}`);
            if (statusDot) {
                if (this.servicesStatus[service]) {
                    statusDot.classList.add('online');
                } else {
                    statusDot.classList.remove('online');
                }
            }
        });
    }
    
    setMode(mode) {
        this.currentMode = mode;
        
        // Update button states
        document.querySelectorAll('.tool-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.getElementById(`${mode}-mode-btn`).classList.add('active');
        
        // Show/hide controls
        this.audioControls.classList.toggle('active', mode === 'audio');
        this.imageMode.classList.toggle('active', mode === 'image');
        
        // Update placeholder and focus
        switch(mode) {
            case 'text':
                this.userInput.placeholder = 'Digite sua mensagem aqui...';
                this.userInput.focus();
                break;
            case 'audio':
                this.userInput.placeholder = 'Grave um áudio ou digite aqui...';
                break;
            case 'image':
                this.imagePrompt.placeholder = 'Descreva a imagem que quer gerar...';
                this.imagePrompt.focus();
                break;
        }
    }
    
    async handleSubmit(e) {
        e.preventDefault();
        
        if (this.currentMode === 'image') {
            await this.generateImage();
            return;
        }
        
        const message = this.userInput.value.trim();
        if (!message) return;
        
        this.addMessage('user', message);
        this.userInput.value = '';
        this.showLoading('Processando resposta...');
        
        try {
            await this.sendMessage(message);
        } catch (error) {
            this.addMessage('ai', 'Desculpe, ocorreu um erro ao processar sua mensagem.');
            console.error('Error sending message:', error);
        } finally {
            this.hideLoading();
        }
    }
    
    async sendMessage(message) {
        const response = await fetch('/api/chat/single', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                model: 'llama3',
                provider: 'ollama',
                session_id: this.currentSession
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to send message');
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let aiMessage = '';
        let messageElement = null;
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        
                        if (data.type === 'session_info') {
                            this.currentSession = data.session_id;
                        } else if (data.type === 'content') {
                            if (!messageElement) {
                                messageElement = this.addMessage('ai', '');
                            }
                            aiMessage += data.content;
                            this.updateMessage(messageElement, aiMessage);
                        } else if (data.type === 'complete') {
                            // Streaming complete
                            break;
                        } else if (data.type === 'error') {
                            throw new Error(data.error);
                        }
                    } catch (parseError) {
                        console.error('Error parsing SSE data:', parseError);
                    }
                }
            }
        }
    }
    
    async toggleRecording() {
        if (!this.isRecording) {
            await this.startRecording();
        } else {
            this.stopRecording();
        }
    }
    
    async startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];
            
            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };
            
            this.mediaRecorder.onstop = () => {
                this.processRecording();
            };
            
            this.mediaRecorder.start();
            this.isRecording = true;
            this.recordBtn.classList.add('recording');
            this.recordingStatus.textContent = 'Gravando... Clique para parar';
            
        } catch (error) {
            console.error('Error starting recording:', error);
            alert('Erro ao acessar o microfone. Verifique as permissões.');
        }
    }
    
    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            this.recordBtn.classList.remove('recording');
            this.recordingStatus.textContent = 'Processando áudio...';
            
            // Stop all tracks
            if (this.mediaRecorder.stream) {
                this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
            }
        }
    }
    
    async processRecording() {
        if (this.audioChunks.length === 0) return;
        
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.wav');
        
        this.showLoading('Transcrevendo áudio...');
        
        try {
            const response = await fetch('/api/audio/transcribe', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.transcription) {
                this.userInput.value = data.transcription;
                this.recordingStatus.textContent = 'Transcrição concluída!';
                
                // Show audio playback
                const audioUrl = URL.createObjectURL(audioBlob);
                const audioPlayback = document.getElementById('audio-playback');
                audioPlayback.src = audioUrl;
                audioPlayback.style.display = 'block';
                
                setTimeout(() => {
                    this.recordingStatus.textContent = 'Clique para gravar';
                    audioPlayback.style.display = 'none';
                }, 5000);
            } else {
                throw new Error('Falha na transcrição');
            }
        } catch (error) {
            console.error('Error transcribing audio:', error);
            this.recordingStatus.textContent = 'Erro na transcrição';
            setTimeout(() => {
                this.recordingStatus.textContent = 'Clique para gravar';
            }, 3000);
        } finally {
            this.hideLoading();
        }
    }
    
    async generateImage() {
        const prompt = this.imagePrompt.value.trim();
        if (!prompt) {
            alert('Por favor, descreva a imagem que deseja gerar.');
            return;
        }
        
        this.addMessage('user', `🎨 Gerar imagem: "${prompt}"`);
        this.imagePrompt.value = '';
        this.showLoading('Gerando imagem... Isso pode levar alguns minutos.');
        
        try {
            const response = await fetch('/api/image/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ prompt: prompt })
            });
            
            const data = await response.json();
            
            if (data.success && data.images && data.images.length > 0) {
                const imageData = data.images[0];
                const imageUrl = `data:image/png;base64,${imageData}`;
                
                this.addImageMessage(imageUrl, prompt, data.cost);
            } else {
                throw new Error('Falha na geração da imagem');
            }
        } catch (error) {
            console.error('Error generating image:', error);
            this.addMessage('ai', 'Desculpe, não foi possível gerar a imagem. Verifique se o serviço Stable Diffusion está ativo.');
        } finally {
            this.hideLoading();
        }
    }
    
    addMessage(sender, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}`;
        
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'chat-bubble';
        bubbleDiv.innerHTML = this.formatMessage(content);
        
        messageDiv.appendChild(bubbleDiv);
        this.chatBox.appendChild(messageDiv);
        this.scrollToBottom();
        
        return bubbleDiv;
    }
    
    addImageMessage(imageUrl, prompt, cost) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message ai';
        
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'chat-bubble';
        
        const img = document.createElement('img');
        img.src = imageUrl;
        img.className = 'image-preview';
        img.alt = prompt;
        
        const caption = document.createElement('p');
        caption.innerHTML = `<strong>Imagem gerada:</strong> ${prompt}<br><small>Custo: $${cost.toFixed(3)}</small>`;
        
        bubbleDiv.appendChild(img);
        bubbleDiv.appendChild(caption);
        messageDiv.appendChild(bubbleDiv);
        this.chatBox.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    updateMessage(element, content) {
        element.innerHTML = this.formatMessage(content);
        this.scrollToBottom();
    }
    
    formatMessage(content) {
        // Basic markdown formatting
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }
    
    showLoading(text = 'Processando...') {
        this.loadingText.textContent = text;
        this.loading.classList.add('active');
        this.sendBtn.disabled = true;
    }
    
    hideLoading() {
        this.loading.classList.remove('active');
        this.sendBtn.disabled = false;
    }
    
    scrollToBottom() {
        this.chatBox.scrollTop = this.chatBox.scrollHeight;
    }
    
    clearChat() {
        if (confirm('Tem certeza que deseja limpar o chat?')) {
            // Keep only the welcome message
            const welcomeMessage = this.chatBox.querySelector('.chat-message.ai');
            this.chatBox.innerHTML = '';
            this.chatBox.appendChild(welcomeMessage);
            this.currentSession = null;
        }
    }
}

// Global functions for HTML onclick handlers
function setMode(mode) {
    if (window.chatApp) {
        window.chatApp.setMode(mode);
    }
}

function toggleRecording() {
    if (window.chatApp) {
        window.chatApp.toggleRecording();
    }
}

function generateImage() {
    if (window.chatApp) {
        window.chatApp.generateImage();
    }
}

function clearChat() {
    if (window.chatApp) {
        window.chatApp.clearChat();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chatApp = new EnhancedChat();
    console.log('Enhanced Chat initialized with AI services integration');
});