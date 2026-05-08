document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatHistory = document.getElementById('chat-history');

    let messageHistory = [];

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const text = userInput.value.trim();
        if (!text) return;

        appendMessage('user', text);
        messageHistory.push({ role: 'user', text: text });
        userInput.value = '';

        const modelMessageDiv = createMessageDiv('model');
        const indicator = document.createElement('div');
        indicator.className = 'thinking-indicator';
        indicator.textContent = 'Routing coordinates...';
        modelMessageDiv.appendChild(indicator);
        chatHistory.appendChild(modelMessageDiv);
        scrollToBottom();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ history: messageHistory })
            });

            if (!response.ok) throw new Error('Network response was not ok');

            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let fullResponse = '';

            modelMessageDiv.innerHTML = ''; 

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                fullResponse += chunk;
                
                modelMessageDiv.innerHTML = marked.parse(fullResponse);
                scrollToBottom();
            }

            messageHistory.push({ role: 'model', text: fullResponse });

        } catch (error) {
            console.error('Error fetching chat:', error);
            modelMessageDiv.innerHTML = '<p style="color: red;">Sorry, there was an error communicating with the server.</p>';
        }
    });

    function appendMessage(role, text) {
        const div = createMessageDiv(role);
        if(role === 'model') {
            div.innerHTML = marked.parse(text);
        } else {
            const p = document.createElement('p');
            p.textContent = text;
            div.appendChild(p);
        }
        chatHistory.appendChild(div);
        scrollToBottom();
    }

    function createMessageDiv(role) {
        const div = document.createElement('div');
        div.className = `message ${role} markdown-body`;
        return div;
    }

    function scrollToBottom() {
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
});
