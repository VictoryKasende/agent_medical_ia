import { fetchConversation, createConversation, deleteConversation } from '../utils/api.js';
import { addMessage } from './ui.js';

let selectedConversationId = null;

export const initConversations = () => {
    document.querySelectorAll('#chat-history > div').forEach(item => {
        item.addEventListener('click', () => loadConversation(item.dataset.conversationId));
    });

    document.getElementById('new-chat-button').addEventListener('click', handleNewChat);
    document.getElementById('confirm-delete').addEventListener('click', handleDeleteConversation);
    document.getElementById('cancel-delete').addEventListener('click', hideDeleteModal);
};

const loadConversation = async (conversationId) => {
    activeConversationId = conversationId;
    try {
        const data = await fetchConversation(conversationId);
        if (data.success) {
            document.getElementById('chat-messages').innerHTML = '';
            data.messages.forEach(msg => addMessage(msg.content, msg.role));
        }
    } catch (error) {
        console.error("Failed to load conversation:", error);
    }
};

const handleNewChat = async () => {
    try {
        const response = await createConversation();
        const data = await response.json();

        if (data.success) {
            activeConversationId = data.conversation_id;
            document.getElementById('chat-messages').innerHTML = `
                <div class="flex items-start space-x-3 message mb-6">
                    <div class="bg-blue-100 text-blue-800 w-8 h-8 rounded-full flex items-center justify-center shrink-0">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="bg-blue-100 text-blue-800 p-4 rounded-2xl rounded-tl-none max-w-full lg:max-w-3xl">
                        <p class="font-medium">Nouvelle discussion</p>
                        <p class="mt-1">Comment puis-je vous aider aujourd'hui?</p>
                    </div>
                </div>
            `;
        }
    } catch (error) {
        console.error("Failed to create new conversation:", error);
    }
};

const handleDeleteConversation = async () => {
    if (!selectedConversationId) return;
    
    try {
        const response = await deleteConversation(selectedConversationId);
        const data = await response.json();
        
        if (data.success) {
            window.location.reload();
        }
    } catch (error) {
        console.error("Failed to delete conversation:", error);
    } finally {
        hideDeleteModal();
    }
};