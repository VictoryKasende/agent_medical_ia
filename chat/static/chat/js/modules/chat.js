import { sendMessage, pollForResult } from '../utils/api.js';
import { addMessage, showTypingIndicator, removeTypingIndicator } from '../modules/ui.js';
import { autoResizeTextarea } from '../utils/dom.js';

let activeConversationId = null;

export const initChat = () => {
    const textarea = document.getElementById('user-input');
    textarea.addEventListener('input', () => autoResizeTextarea(textarea));
    
    document.getElementById('send-button').addEventListener('click', handleSendMessage);
    textarea.addEventListener('keypress', handleKeyPress);
};

const handleSendMessage = async () => {
    const input = document.getElementById('user-input');
    const message = input.value.trim();
    if (!message) return;
    
    addMessage(message, 'user');
    input.value = '';
    autoResizeTextarea(input);
    showTypingIndicator();

    try {
        const response = await sendMessage(message, activeConversationId);
        const data = await response.json();

        if (data.status === "done") {
            removeTypingIndicator();
            addMessage(data.response, 'bot');
        } else if (data.status === "pending") {
            pollForResult(data.cache_key);
        }
    } catch (error) {
        removeTypingIndicator();
        addMessage("Une erreur est survenue. Veuillez réessayer.", 'bot');
    }
};

const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        handleSendMessage();
    }
};