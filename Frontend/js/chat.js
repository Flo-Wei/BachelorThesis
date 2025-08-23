/**
 * Chat Interface JavaScript
 * Handles real-time messaging and session management
 */

// State management
let currentSessionId = null;
let userSessions = [];
let isWaitingForResponse = false;

// DOM elements
let sessionsList, chatTitle, chatMessages, messageInput, sendButton;
let connectionStatus, typingIndicator, newChatBtn, userAvatar, userName;
let clearChatBtn, exportChatBtn;

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    if (!AuthUtils.requireAuth()) return;
    
    initializeElements();
    initializePage();
    setupEventListeners();
    checkConnectionStatus();
});

function initializeElements() {
    sessionsList = document.getElementById('sessionsList');
    chatTitle = document.getElementById('chatTitle');
    chatMessages = document.getElementById('chatMessages');
    messageInput = document.getElementById('messageInput');
    sendButton = document.getElementById('sendButton');
    connectionStatus = document.getElementById('connectionStatus');
    typingIndicator = document.getElementById('typingIndicator');
    newChatBtn = document.getElementById('newChatBtn');
    userAvatar = document.getElementById('userAvatar');
    userName = document.getElementById('userName');
    clearChatBtn = document.getElementById('clearChatBtn');
    exportChatBtn = document.getElementById('exportChatBtn');
}

function initializePage() {
    const user = api.getCurrentUser();
    if (user) {
        userAvatar.textContent = user.username[0].toUpperCase();
        userName.textContent = user.username;
    }

    loadUserSessions();
}

function setupEventListeners() {
    // Chat input and sending
    messageInput.addEventListener('keypress', handleKeyPress);
    messageInput.addEventListener('input', autoResizeTextarea);
    sendButton.addEventListener('click', sendMessage);
    
    // Chat actions
    newChatBtn.addEventListener('click', createNewChat);
    clearChatBtn.addEventListener('click', clearCurrentChat);
    exportChatBtn.addEventListener('click', exportChat);

    // Auto-resize textarea
    autoResizeTextarea();
}

function handleKeyPress(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

function autoResizeTextarea() {
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
}

async function checkConnectionStatus() {
    try {
        await api.healthCheck();
        updateConnectionStatus('connected', 'Connected to server');
        enableChat();
    } catch (error) {
        updateConnectionStatus('disconnected', 'Server unavailable');
        disableChat();
    }
}

function updateConnectionStatus(status, message) {
    connectionStatus.className = `connection-status status-${status}`;
    connectionStatus.textContent = message;
}

function enableChat() {
    messageInput.disabled = false;
    sendButton.disabled = false;
    messageInput.placeholder = 'Message AI Assistant...';
}

function disableChat() {
    messageInput.disabled = true;
    sendButton.disabled = true;
    messageInput.placeholder = 'Server unavailable...';
}

async function loadUserSessions() {
    const user = api.getCurrentUser();
    if (!user) return;

    try {
        userSessions = await api.getUserSessions(user.user_id);
        renderSessionsList();
        
        // If no sessions exist, create a new one
        if (userSessions.length === 0) {
            await createNewChat();
        } else {
            // Select the most recent session
            selectSession(userSessions[0].session_id);
        }
        
    } catch (error) {
        console.error('Error loading sessions:', error);
        showSystemMessage('Failed to load chat sessions', 'error');
    }
}

function renderSessionsList() {
    const sessionsHTML = userSessions.map(session => {
        const isActive = session.session_id === currentSessionId;
        const sessionName = session.session_name || 'New Chat';
        
        return `
            <button class="session-item ${isActive ? 'active' : ''}" 
                    data-session-id="${session.session_id}"
                    onclick="selectSession(${session.session_id})">
                <div class="session-title">${sessionName}</div>
                <div class="session-preview">Session from ${UIUtils.formatTimeAgo(session.created_at)}</div>
            </button>
        `;
    }).join('');

    sessionsList.innerHTML = sessionsHTML;
}

async function selectSession(sessionId) {
    currentSessionId = sessionId;
    
    // Update UI to show selected session
    document.querySelectorAll('.session-item').forEach(item => {
        item.classList.remove('active');
        if (parseInt(item.dataset.sessionId) === sessionId) {
            item.classList.add('active');
        }
    });

    // Update chat title
    const session = userSessions.find(s => s.session_id === sessionId);
    if (session) {
        chatTitle.textContent = session.session_name || 'New Chat';
    }

    // Load messages for this session
    await loadSessionMessages();
}

async function loadSessionMessages() {
    if (!currentSessionId) return;

    try {
        const messages = await api.getSessionMessages(currentSessionId);
        
        // Clear current messages
        chatMessages.innerHTML = '';
        
        if (messages.length === 0) {
            showWelcomeMessage();
        } else {
            // Render all messages
            messages.forEach(message => {
                displayMessage(message.message_content, message.role, message.timestamp);
            });
        }
        
        scrollToBottom();
        
    } catch (error) {
        console.error('Error loading messages:', error);
        showSystemMessage('Failed to load chat history', 'error');
    }
}

function showWelcomeMessage() {
    const welcomeMessage = document.createElement('div');
    welcomeMessage.className = 'message bot';
    welcomeMessage.innerHTML = `
        <div>Hello! I'm your AI assistant. How can I help you today?</div>
        <div class="message-time">Just now</div>
    `;
    chatMessages.appendChild(welcomeMessage);
}

function displayMessage(content, role, timestamp = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role === 'USER' ? 'user' : 'bot'}`;
    
    const timeStr = timestamp ? UIUtils.formatTimeAgo(timestamp) : 'Just now';
    
    messageDiv.innerHTML = `
        <div>${content}</div>
        <div class="message-time">${timeStr}</div>
    `;
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function showSystemMessage(content, type = 'info') {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message system ${type}`;
    messageDiv.innerHTML = `<div><em>${content}</em></div>`;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message || isWaitingForResponse) return;

    const user = api.getCurrentUser();
    if (!user) return;

    try {
        // Disable input while processing
        isWaitingForResponse = true;
        messageInput.disabled = true;
        sendButton.disabled = true;
        
        // Display user message immediately
        displayMessage(message, 'USER');
        
        // Clear input
        messageInput.value = '';
        autoResizeTextarea();
        
        // Show typing indicator
        showTypingIndicator();
        
        // Send to API
        const response = await api.sendMessage(user.user_id, message, currentSessionId);
        
        // If this was a new session, update our current session
        if (!currentSessionId) {
            currentSessionId = response.session_id;
            
            // Reload sessions list to include the new session
            await loadUserSessions();
        }
        
        // Hide typing indicator
        hideTypingIndicator();
        
        // Display assistant response
        displayMessage(response.assistant_response.message_content, 'ASSISTANT');
        
    } catch (error) {
        hideTypingIndicator();
        console.error('Error sending message:', error);
        showSystemMessage(`Error: ${error.message}`, 'error');
    } finally {
        // Re-enable input
        isWaitingForResponse = false;
        messageInput.disabled = false;
        sendButton.disabled = false;
        messageInput.focus();
    }
}

function showTypingIndicator() {
    typingIndicator.style.display = 'block';
    scrollToBottom();
}

function hideTypingIndicator() {
    typingIndicator.style.display = 'none';
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function createNewChat() {
    const user = api.getCurrentUser();
    if (!user) return;

    try {
        const session = await api.createSession(user.user_id, 'New Chat');
        
        // Add to sessions list
        userSessions.unshift(session);
        renderSessionsList();
        
        // Select the new session
        selectSession(session.session_id);
        
        // Show welcome message
        chatMessages.innerHTML = '';
        showWelcomeMessage();
        
    } catch (error) {
        console.error('Error creating new chat:', error);
        showSystemMessage('Failed to create new chat', 'error');
    }
}

function clearCurrentChat() {
    if (!currentSessionId) return;
    
    if (confirm('Are you sure you want to clear this chat? This cannot be undone.')) {
        chatMessages.innerHTML = '';
        showWelcomeMessage();
        showSystemMessage('Chat cleared locally. Note: messages are still stored on the server.', 'info');
    }
}

function exportChat() {
    if (!currentSessionId) return;
    
    const messages = Array.from(chatMessages.children).map(msg => {
        if (msg.classList.contains('system')) return null;
        
        const isUser = msg.classList.contains('user');
        const content = msg.querySelector('div:first-child').textContent;
        const time = msg.querySelector('.message-time')?.textContent || '';
        return `[${time}] ${isUser ? 'You' : 'AI'}: ${content}`;
    }).filter(Boolean).join('\n');
    
    const blob = new Blob([messages], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat-${currentSessionId}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Make selectSession global so it can be called from onclick
window.selectSession = selectSession;

// Periodic connection check
setInterval(checkConnectionStatus, 30000);

// Add system message styles
const style = document.createElement('style');
style.textContent = `
    .message.system {
        background: #f0f0f0;
        color: #666;
        border-left: 3px solid #ddd;
        margin: 10px auto;
        max-width: 60%;
        font-style: italic;
    }
    .message.system.error {
        background: #ffeaea;
        border-left-color: #e74c3c;
        color: #c0392b;
    }
    .message.system.info {
        background: #e8f4fd;
        border-left-color: #3498db;
        color: #2980b9;
    }
`;
document.head.appendChild(style);
