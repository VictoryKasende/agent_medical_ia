export const initSearch = () => {
    document.getElementById('search-button').addEventListener('click', showSearchModal);
    document.getElementById('close-search').addEventListener('click', closeSearchModal);
    document.getElementById('searchInput').addEventListener('input', performSearch);
};

const showSearchModal = () => {
    document.getElementById('searchModal').classList.remove('hidden');
    document.getElementById('searchInput').focus();
};

const closeSearchModal = () => {
    document.getElementById('searchModal').classList.add('hidden');
    document.getElementById('searchInput').value = '';
    document.getElementById('searchResults').innerHTML = '';
};

const performSearch = () => {
    const query = document.getElementById('searchInput').value.toLowerCase();
    const resultsContainer = document.getElementById('searchResults');
    resultsContainer.innerHTML = '';

    if (query.trim() === '') return;

    const filtered = chatItems.filter(item =>
        item.messages.some(msg => msg.toLowerCase().includes(query))
    );

    if (filtered.length === 0) {
        resultsContainer.innerHTML = '<p class="text-gray-500">Aucun résultat trouvé.</p>';
        return;
    }

    filtered.forEach(item => {
        const matchedMessage = item.messages.find(msg => msg.toLowerCase().includes(query));
        const resultElement = document.createElement('div');
        resultElement.className = 'cursor-pointer px-3 py-2 rounded hover:bg-gray-100';
        resultElement.innerHTML = `<i class="fas fa-comment text-blue-500 mr-2"></i>${matchedMessage}`;
        resultElement.onclick = () => {
            closeSearchModal();
            loadConversation(item.id);
        };
        resultsContainer.appendChild(resultElement);
    });
};