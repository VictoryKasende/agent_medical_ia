import { scrollToBottom } from '../utils/dom.js';

export const initUI = () => {
    // Initialisation des composants UI
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebar-overlay');

    if (mobileMenuButton && sidebar && sidebarOverlay) {
        mobileMenuButton.addEventListener('click', () => {
            sidebar.classList.toggle('sidebar-open');
            sidebarOverlay.classList.toggle('sidebar-overlay-open');
        });

        sidebarOverlay.addEventListener('click', () => {
            sidebar.classList.remove('sidebar-open');
            sidebarOverlay.classList.remove('sidebar-overlay-open');
        });
    }
};

export const addMessage = (text, sender) => {
    const chatContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `flex items-start space-x-3 message ${sender === 'user' ? 'justify-end' : ''}`;

    if (sender === 'user') {
        messageDiv.innerHTML = `
            <div class="bg-blue-600 text-white p-4 rounded-2xl rounded-tr-none max-w-full lg:max-w-2xl">
                <p>${text}</p>
            </div>
            <div class="bg-blue-100 text-blue-800 w-8 h-8 rounded-full flex items-center justify-center shrink-0">
                <i class="fas fa-user"></i>
            </div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="bg-blue-100 text-blue-800 w-8 h-8 rounded-full flex items-center justify-center shrink-0">
                <i class="fas fa-robot"></i>
            </div>
            <div class="bg-blue-100 text-blue-800 p-4 rounded-2xl rounded-tl-none max-w-full lg:max-w-2xl prose prose-sm prose-blue">
                ${marked.parse(text)}
            </div>
        `;
    }

    chatContainer.appendChild(messageDiv);
    scrollToBottom(chatContainer);
};

export const showTypingIndicator = () => {
    const chatContainer = document.getElementById('chat-messages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'flex items-start space-x-3 message';
    typingDiv.id = 'typing-indicator';
    typingDiv.innerHTML = `
        <div class="bg-blue-100 text-blue-800 w-8 h-8 rounded-full flex items-center justify-center shrink-0">
            <i class="fas fa-robot"></i>
        </div>
        <div class="bg-blue-100 text-blue-800 p-3 rounded-2xl rounded-tl-none w-20">
            <div class="flex space-x-1">
                <div class="typing-dot w-2 h-2 bg-blue-600 rounded-full"></div>
                <div class="typing-dot w-2 h-2 bg-blue-600 rounded-full"></div>
                <div class="typing-dot w-2 h-2 bg-blue-600 rounded-full"></div>
            </div>
        </div>
    `;
    chatContainer.appendChild(typingDiv);
    scrollToBottom(chatContainer);
};

export const removeTypingIndicator = () => {
    const typingIndicator = document.getElementById('typing-indicator');
    typingIndicator?.remove();
};

export const hideDeleteModal = () => {
    document.getElementById("delete-modal").classList.add("hidden");
};