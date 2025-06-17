export const autoResizeTextarea = (textarea) => {
    textarea.style.height = 'auto';
    textarea.style.height = `${textarea.scrollHeight}px`;
};

export const scrollToBottom = (element) => {
    element.scrollTop = element.scrollHeight;
};