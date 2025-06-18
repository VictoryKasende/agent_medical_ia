import { getCookie } from './helpers.js';

export const fetchConversation = async (conversationId) => {
    const response = await fetch(`/get-conversation/${conversationId}/`);
    return await response.json();
};

export const sendMessage = async (message, conversationId) => {
    return await fetch('/analyse/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ message, conversation_id: conversationId })
    });
};

export const createConversation = async () => {
    return await fetch("/conversation/", {
        method: "POST",
        headers: {
            "X-CSRFToken": getCookie('csrftoken'),
            "Content-Type": "application/json"
        }
    });
};

export const deleteConversation = async (conversationId) => {
    return await fetch(`/conversation/${conversationId}/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    });
};

export const pollForResult = async (cacheKey) => {
    const response = await fetch(`/diagnostic-result/?cache_key=${encodeURIComponent(cacheKey)}`, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    });
    
    if (!response.ok) {
        throw new Error("Erreur lors de la récupération du résultat");
    }
    
    return await response.json();
};