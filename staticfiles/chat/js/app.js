import { initChat } from './modules/chat.js';
import { initConversations } from './modules/conversations.js';
import { initSearch } from './modules/search.js';
import { initUI } from './modules/ui.js';

document.addEventListener('DOMContentLoaded', () => {
    initUI();
    initChat();
    initConversations();
    initSearch();
});