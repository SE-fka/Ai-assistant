<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" type="image/x-icon" href="/static/logo.jpg">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <title>AI Assistant</title>
    <style>
        /* Basic CSS Reset */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f6fa;
            min-height: 100vh;
            padding: 0;
            overflow: hidden;
        }

        .container {
            max-width: 100%;
            height: 100vh;
            margin: 0;
            background: white;
            border-radius: 0;
            box-shadow: none;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }

        /* Updated Header like Figma */
        .header {
            background: white;
            color: #2c3e50;
            padding: 12px 24px;
            border-bottom: 1px solid #e1e8ed;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }

        .header-left {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 700;
            font-size: 1.4em;
            color: #2c3e50;
        }

        .logo-icon {
            font-size: 1.6em;
        }

        .header-right {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .user-menu {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px 12px;
            border-radius: 20px;
            background: #f8f9fa;
            cursor: pointer;
            transition: background-color 0.2s;
        }

        .user-menu:hover {
            background: #e9ecef;
        }

        .user-avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea, #764ba2);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 14px;
        }

        .user-info {
            display: flex;
            flex-direction: column;
        }

        .username {
            font-weight: 600;
            font-size: 0.9em;
            color: #2c3e50;
        }

        .user-role {
            font-size: 0.75em;
            color: #6c757d;
        }

        .dropdown-menu {
            position: absolute;
            top: 60px;
            right: 24px;
            background: white;
            border: 1px solid #e1e8ed;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            padding: 8px 0;
            min-width: 180px;
            z-index: 1000;
            display: none;
        }

        .dropdown-menu.show {
            display: block;
        }

        .dropdown-item {
            padding: 10px 16px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            color: #2c3e50;
            text-decoration: none;
            transition: background-color 0.2s;
        }

        .dropdown-item:hover {
            background: #f8f9fa;
        }

        .dropdown-divider {
            height: 1px;
            background: #e1e8ed;
            margin: 4px 0;
        }

        .main-content {
            display: flex;
            flex: 1;
            overflow: hidden;
        }

        .sidebar {
            width: 320px;
            background: #f8f9fa;
            border-right: 1px solid #e9ecef;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .sidebar-header {
            padding: 20px;
            border-bottom: 1px solid #e9ecef;
        }

        .sidebar-title {
            font-size: 1.2em;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 16px;
        }

        .new-chat-btn {
            width: 100%;
            padding: 12px 16px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            transition: all 0.3s;
        }

        .new-chat-btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }

        .chat-history-section {
            flex: 1;
            padding: 0 20px 20px 20px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }

        .section-title {
            font-size: 0.9em;
            font-weight: 600;
            color: #6c757d;
            margin: 20px 0 12px 0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .session-list {
            flex: 1;
            overflow-y: auto;
        }

        .session-item {
            padding: 12px;
            margin-bottom: 8px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
            border: 1px solid transparent;
            position: relative;
        }

        .session-item:hover {
            background: white;
            border-color: #e9ecef;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }

        .session-item.active {
            background: white;
            border-color: #667eea;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.15);
        }

        .session-title {
            font-weight: 500;
            font-size: 0.9em;
            color: #2c3e50;
            margin-bottom: 4px;
            line-height: 1.4;
            padding-right: 30px;
        }

        .session-meta {
            display: flex;
            justify-content: space-between;
            font-size: 0.75em;
            color: #6c757d;
        }

        .session-actions {
            position: absolute;
            top: 8px;
            right: 8px;
            opacity: 0;
            transition: opacity 0.2s;
        }

        .session-item:hover .session-actions {
            opacity: 1;
        }

        .delete-btn {
            background: none;
            border: none;
            color: #dc3545;
            cursor: pointer;
            padding: 4px;
            border-radius: 4px;
            font-size: 14px;
            transition: background-color 0.2s;
        }

        .delete-btn:hover {
            background: rgba(220, 53, 69, 0.1);
        }

        .clear-all-btn {
            width: 100%;
            padding: 10px 16px;
            background: #dc3545;
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            transition: all 0.3s;
            margin-top: 10px;
        }

        .clear-all-btn:hover {
            background: #c82333;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(220, 53, 69, 0.3);
        }

        .chat-area {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            background: white;
        }

        .chat-messages {
            flex: 1;
            padding: 24px;
            overflow-y: auto;
            background: white;
        }

        .message {
            margin-bottom: 20px;
            padding: 16px 20px;
            border-radius: 12px;
            max-width: 80%;
            line-height: 1.6;
            word-wrap: break-word;
            clear: both;
            margin-left: auto;
        }

        .user-message {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            margin-right: 130px;
            border-bottom-left-radius: 4px;
        }

        .bot-message {
            background: #f8f9fa;
            color: #2c3e50;
            margin-right: auto;
            border-bottom-right-radius: 4px;
            border: 1px solid #e9ecef;
        }

        .message-header {
            font-weight: 600;
            margin-bottom: 8px;
            font-size: 0.85em;
            opacity: 0.9;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .message-header .avatar {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
            font-weight: 600;
        }

        .user-message .avatar {
            background: rgba(255, 255, 255, 0.3);
        }

        .bot-message .avatar {
            background: #667eea;
            color: white;
        }

        .documents-used {
            background: #e3f2fd;
            border-left: 3px solid #2196f3;
            padding: 10px 12px;
            margin-top: 10px;
            border-radius: 6px;
            font-size: 0.8em;
            color: #1565c0;
        }

        .documents-used strong {
            color: #0d47a1;
        }

        .chat-input-container {
            padding: 20px 24px;
            border-top: 1px solid #e9ecef;
            background: white;
        }

        .input-group {
            display: flex;
            gap: 12px;
            align-items: flex-end;
        }

        .input-group input {
            flex: 1;
            padding: 14px 18px;
            border: 2px solid #e9ecef;
            border-radius: 12px;
            font-size: 15px;
            outline: none;
            transition: border-color 0.3s;
            font-family: inherit;
            resize: none;
            min-height: 50px;
            max-height: 120px;
        }

        .input-group input:focus {
            border-color: #667eea;
        }

        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 12px;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 600;
            font-family: inherit;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
        }

        .btn-primary {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }

        .btn-primary:hover:not(:disabled) {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }

        .btn-primary:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .typing-indicator {
            display: none;
            padding: 16px 20px;
            background: #f8f9fa;
            border-radius: 12px;
            margin-bottom: 20px;
            margin-left: 160px;
            max-width: 75%;
            border: 1px solid #e9ecef;
        }

        .typing-dots {
            display: flex;
            gap: 4px;
            align-items: center;
        }

        .typing-dots span {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #6c757d;
            animation: typing 1.4s infinite ease-in-out;
        }

        .typing-dots .text {
            margin-left: 10px;
            color: #6c757d;
            font-size: 0.85em;
        }

        .typing-dots span:nth-child(1) {
            animation-delay: -0.32s;
        }

        .typing-dots span:nth-child(2) {
            animation-delay: -0.16s;
        }

        @keyframes typing {

            0%,
            80%,
            100% {
                transform: scale(0.8);
                opacity: 0.5;
            }

            40% {
                transform: scale(1);
                opacity: 1;
            }
        }

        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: #6c757d;
        }

        .empty-state .icon {
            font-size: 3em;
            margin-bottom: 12px;
            opacity: 0.5;
        }

        .empty-state p {
            margin-bottom: 8px;
        }

        .welcome-message {
            text-align: center;
            max-width: 600px;
            margin: 0 auto;
            padding: 40px 20px;
        }

        .welcome-title {
            font-size: 1.8em;
            font-weight: 700;
            color: #2c3e50;
            margin-bottom: 16px;
        }

        .welcome-subtitle {
            font-size: 1.1em;
            color: #6c757d;
            line-height: 1.6;
            margin-bottom: 24px;
        }

        /* Confirmation Modal */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(5px);
            z-index: 2000;
            align-items: center;
            justify-content: center;
        }

        .modal.active {
            display: flex;
        }

        .modal-content {
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
            max-width: 400px;
            width: 90%;
        }

        .modal-header {
            margin-bottom: 16px;
        }

        .modal-title {
            font-size: 1.2em;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 8px;
        }

        .modal-message {
            color: #6c757d;
            line-height: 1.5;
        }

        .modal-actions {
            display: flex;
            gap: 12px;
            justify-content: flex-end;
            margin-top: 20px;
        }

        .btn-cancel {
            background: #6c757d;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
        }

        .btn-cancel:hover {
            background: #5a6268;
        }

        .btn-confirm {
            background: #dc3545;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
        }

        .btn-confirm:hover {
            background: #c82333;
        }

        @media (max-width: 768px) {
            .main-content {
                flex-direction: column;
            }

            .sidebar {
                width: 100%;
                max-height: 40vh;
            }

            .message {
                max-width: 85%;
            }

            .header {
                padding: 12px 16px;
            }

            .username {
                display: none;
            }
        }
    </style>
    <style>
        .chat-input-container {
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 10px;
            background-color: #f8f9fa;
            border-top: 1px solid #dee2e6;
            position: relative;
        }

        .input-group {
            display: flex;
            width: 100%;
            max-width: 600px;
            /* Limit the maximum width */
            max-width: 80%;
            margin: 0 auto;
        }

        textarea {
            flex: 1;
            padding: 10px;
            border: 1px solid #ced4da;
            border-radius: 5px;
            font-size: 16px;
            resize: none;
            /* Disable resizing */
            box-shadow: 1px 1px 5px rgba(0, 0, 0, 0.1);
            transition: border-color 0.3s, box-shadow 0.3s;
        }

        textarea:focus {
            border-color: #007bff;
            box-shadow: 0 0 5px rgba(0, 123, 255, 0.5);
            outline: none;
            /* Remove the default outline */
        }

        button {
            margin-left: 10px;
            padding: 10px 15px;
            border: none;
            border-radius: 5px;
            background-color: #007bff;
            color: #ffffff;
            font-size: 16px;
            cursor: pointer;
            transition: background-color 0.3s, transform 0.1s;
        }

        button:hover {
            background-color: #0056b3;
        }

        button:active {
            transform: scale(0.95);
            /* Button press effect */
        }

        @media (max-width: 600px) {
            .input-group {
                flex-direction: column;
                /* Stack elements on smaller screens */
            }

            textarea {
                margin-bottom: 10px;
                /* Space between textarea and button */
            }
        }
    </style>
</head>

<body>
    <div class="container">
        <!-- Updated Header -->
        <div class="header">
            <div class="header-left">
                <div class="logo">
                    <span class="logo-icon"> <img src="/static/logo.jpg" alt="AI Assistant Logo"
                            style="width: 40px; height: auto; border-radius: 50%;"></span>
                    <span>AI Assistant</span>
                </div>
            </div>
            <div class="header-right">
                <div class="user-menu" id="user-menu">
                    <div class="user-avatar" id="user-avatar">G</div>
                    <div class="user-info">
                        <div class="username" id="username">Guest</div>
                        <div class="user-role" id="user-role">User</div>
                    </div>
                    &nbsp;&nbsp;
                </div>
            </div>

            <!-- Dropdown Menu -->
            <div class="dropdown-menu" id="dropdown-menu">
                <div class="dropdown-item">
                    <span>👤</span>
                    <span>Profile</span>
                </div>
                <div class="dropdown-content">
                    <a href="/dashboard" class="dropdown-item">
                        <span>⚙️</span>
                        <span>dashboard</span>
                    </a>
                </div>
                <div class="dropdown-divider"></div>
                <div class="dropdown-item" onclick="logout()">
                    <i class="fas fa-sign-out-alt" style="margin-left: 8px;"></i>
                    <span> Sign Out</span>
                </div>
            </div>
        </div>

        <div class="main-content">
            <div class="sidebar">
                <div class="sidebar-header">
                    <button class="new-chat-btn" onclick="createNewChat()">
                        <span>+</span>
                        <span>New Chat</span>
                    </button>
                </div>

                <div class="chat-history-section">
                    <div class="section-title">Recent Chats</div>
                    <div class="session-list" id="session-list">
                        <div class="empty-state">
                            <div class="icon">💬</div>
                            <p>No chat history yet</p>
                            <p style="font-size: 0.9em;">Start a new conversation!</p>
                        </div>
                    </div>

                    <!-- Clear All Button -->
                    <button class="clear-all-btn" onclick="showClearAllConfirmation()">
                        <span>🗑️</span>
                        <span>Clear All Chats</span>
                    </button>
                </div>
            </div>

            <div class="chat-area">
                <div class="chat-messages" id="chat-messages">
                    <div class="welcome-message">
                        <div class="welcome-title">Welcome to AI Assistant! 👋</div>
                        <div class="welcome-subtitle">
                            I'm here to help you search through documents and answer questions.
                            Start a new conversation or continue from your chat history.
                        </div>
                    </div>
                </div>

                <div class="typing-indicator" id="typing-indicator">
                    <div class="typing-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                        <div class="text">AI is thinking...</div>
                    </div>
                </div>
                <form>
                    <div class="chat-input-container">

                        <div class="input-group">
                            <textarea id="user-input" placeholder="Ask me anything..."
                                onkeypress="handleKeyPress(event)" rows="4" required></textarea>
                            <button class="btn btn-primary" id="send-button" onclick="sendMessage()">
                                <span>Send</span>
                                <span>↗</span>
                            </button>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <!-- Confirmation Modal -->
    <div class="modal" id="confirmation-modal">
        <div class="modal-content">
            <div class="modal-header">
                <div class="modal-title" id="modal-title">Confirm Deletion</div>
                <div class="modal-message" id="modal-message">Are you sure you want to delete this chat?</div>
            </div>
            <div class="modal-actions">
                <button class="btn-cancel" onclick="hideModal()">Cancel</button>
                <button class="btn-confirm" id="confirm-button">Delete</button>
            </div>
        </div>
    </div>

    <script>
        function adjustTextareaHeight() {
            const textarea = document.getElementById("user-input");
            textarea.style.height = 'auto'; // Reset height to auto to measure scrollHeight

            // Set the maximum height (e.g., 200px)
            const maxHeight = 200;
            const newHeight = Math.min(textarea.scrollHeight, maxHeight); // Limit height to maxHeight

            textarea.style.height = newHeight + 'px'; // Set the height
        }
        // Add an event listener to the textarea for input adjustment
        document.getElementById("user-input").addEventListener("input", adjustTextareaHeight);

        // Load user from localStorage on page load
        document.addEventListener('DOMContentLoaded', function () {
            const savedUser = localStorage.getItem('currentUser');
            if (savedUser) {
                updateUserInfo(JSON.parse(savedUser));
            }
        });

        // Enhanced update function that saves to localStorage
        function updateUserInfo(user) {
            if (!user) {
                localStorage.removeItem('currentUser');
                document.getElementById("username").textContent = "Please Login";
                document.getElementById("user-role").textContent = "Guest";
                document.getElementById("user-avatar").textContent = "?";
                return;
            }

            // Save user to localStorage
            localStorage.setItem('currentUser', JSON.stringify(user));

            // Update display
            document.getElementById("username").textContent = user.username;
            document.getElementById("user-role").textContent = user.role;
            document.getElementById("user-avatar").textContent = user.username.charAt(0).toUpperCase();
        }

        // Example: Update user after successful login
        function loginUser(credentials) {
            // Your login API call
            fetch('/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(credentials)
            })
                .then(response => response.json())
                .then(user => {
                    updateUserInfo(user);
                });
        }
    </script>

    <script>
        // Application state variables
        let currentSessionId = null;
        let currentUser = null;
        let authToken = null;
        let isProcessing = false;
        let currentPage = 0;
        const pageSize = 10;
        let totalSessions = 0;
        let pendingDeleteSessionId = null;

        // Check authentication on page load
        function checkAuthentication() {
            const savedToken = localStorage.getItem('authToken');
            const savedUser = localStorage.getItem('currentUser');

            if (!savedToken || !savedUser) {
                window.location.href = '/';
                return false;
            }

            authToken = savedToken;
            currentUser = JSON.parse(savedUser);

            // Update UI with user info
            document.getElementById('username').textContent = currentUser.username;
            document.getElementById('user-avatar').textContent = currentUser.username.charAt(0).toUpperCase();

            return true;
        }

        // Add authorization header to all requests
        function getAuthHeaders() {
            return {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            };
        }

        // Modal functions
        function showModal(title, message, confirmCallback) {
            document.getElementById('modal-title').textContent = title;
            document.getElementById('modal-message').textContent = message;
            document.getElementById('confirmation-modal').classList.add('active');

            // Set up confirm button
            const confirmBtn = document.getElementById('confirm-button');
            confirmBtn.onclick = confirmCallback;
        }

        function hideModal() {
            document.getElementById('confirmation-modal').classList.remove('active');
            pendingDeleteSessionId = null;
        }

        // Show delete confirmation for single chat
        function showDeleteConfirmation(sessionId, sessionTitle) {
            pendingDeleteSessionId = sessionId;
            const title = sessionTitle || 'this chat';
            showModal(
                'Delete Chat',
                `Are you sure you want to delete "${title}"? This action cannot be undone.`,
                confirmDeleteSession
            );
        }

        // Show clear all confirmation
        function showClearAllConfirmation() {
            showModal(
                'Clear All Chats',
                'Are you sure you want to delete ALL chat sessions? This action cannot be undone.',
                confirmClearAllSessions
            );
        }

        // Handle Enter key press
        function handleKeyPress(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }

        // Add message to chat
        function addMessage(content, isUser = false, documents = []) {
            const messagesContainer = document.getElementById('chat-messages');

            // Remove welcome message if it's the first user message
            const welcomeMessage = messagesContainer.querySelector('.welcome-message');
            if (welcomeMessage && isUser) {
                welcomeMessage.remove();
            }

            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;

            let messageContent = '';
            if (isUser) {
                messageContent = `
                    <div class="message-header">
                        <div class="avatar">👤</div>
                        ${currentUser.username}
                    </div>
                    ${content}
                `;
            } else {
                const formattedContent = content.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>');
                messageContent = `
                    <div class="message-header">
                        <div class="avatar">AI</div>
                        AI Assistant
                    </div>
                    <p>${formattedContent}</p>
                `;
            }

            if (documents && documents.length > 0) {
                messageContent += `
                    <div class="documents-used">
                        <strong>Based on:</strong> ${documents.join(', ')}
                    </div>
                `;
            }

            messageDiv.innerHTML = messageContent;
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        // Show/hide typing indicator
        function showTypingIndicator() {
            document.getElementById('typing-indicator').style.display = 'block';
            document.getElementById('chat-messages').scrollTop = document.getElementById('chat-messages').scrollHeight;
        }

        function hideTypingIndicator() {
            document.getElementById('typing-indicator').style.display = 'none';
        }

        // Enable/disable send button
        function setSendButtonDisabled(disabled) {
            const sendButton = document.getElementById('send-button');
            const userInput = document.getElementById('user-input');

            sendButton.disabled = disabled;
            userInput.disabled = disabled;

            if (disabled) {
                sendButton.style.opacity = '0.6';
                userInput.style.opacity = '0.8';
            } else {
                sendButton.style.opacity = '1';
                userInput.style.opacity = '1';
                userInput.focus();
            }
        }

        // Main function to send message
        async function sendMessage() {
            if (isProcessing) return;

            const input = document.getElementById('user-input');
            const message = input.value.trim();

            if (!message) return;

            // Set processing state
            isProcessing = true;
            setSendButtonDisabled(true);

            // Add user message
            addMessage(message, true);
            input.value = '';

            // Show typing indicator
            showTypingIndicator();

            try {
                await sendChatMessage(message);
                // Refresh chat history after sending message
                loadChatHistory();
            } catch (error) {
                console.error('Error sending message:', error);
                hideTypingIndicator();
                addMessage('Sorry, there was an error processing your request. Please try again.');
            } finally {
                // Reset processing state
                isProcessing = false;
                setSendButtonDisabled(false);
            }
        }

        // Send message to backend
        async function sendChatMessage(message) {
            try {
                if (!currentSessionId) {
                    currentSessionId = 'session_' + Date.now();
                }

                const response = await fetch('/document-chat', {
                    method: 'POST',
                    headers: getAuthHeaders(),
                    body: JSON.stringify({
                        content: message,
                        session_id: currentSessionId
                    })
                });

                if (response.status === 401) {
                    localStorage.removeItem('authToken');
                    localStorage.removeItem('currentUser');
                    window.location.href = '/';
                    return;
                }

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();

                // Add bot response
                addMessage(data.response, false, data.documents_used || []);
                hideTypingIndicator();

            } catch (error) {
                console.error('Chat error:', error);
                throw error;
            }
        }

        // Load chat history
        async function loadChatHistory() {
            if (!checkAuthentication()) return;

            try {
                const offset = currentPage * pageSize;
                const response = await fetch(`/chat-sessions?limit=${pageSize}&offset=${offset}`, {
                    headers: getAuthHeaders()
                });

                if (!response.ok) {
                    if (response.status === 401) {
                        localStorage.removeItem('authToken');
                        localStorage.removeItem('currentUser');
                        window.location.href = '/';
                        return;
                    }
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();
                displayChatSessions(data);

            } catch (error) {
                console.error('Error loading chat history:', error);
                showEmptyHistoryState();
            }
        }

        // Display chat sessions with delete buttons
        function displayChatSessions(data) {
            const sessionList = document.getElementById('session-list');

            if (!data.sessions || data.sessions.length === 0) {
                showEmptyHistoryState();
                return;
            }

            sessionList.innerHTML = '';

            data.sessions.forEach(session => {
                const sessionItem = document.createElement('div');
                sessionItem.className = `session-item ${session.session_id === currentSessionId ? 'active' : ''}`;
                const lastActivity = session.last_activity || session.created_at || new Date().toISOString();
                const options = {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                };
                const date = new Date(lastActivity).toLocaleDateString('en-US', options);
                const title = session.title || 'New Chat';

                sessionItem.innerHTML = `
                    <div class="session-title">${title}</div>
                    <div class="session-meta">
                        <span>${session.message_count || 0} messages</span>
                        <span>${date}</span>
                    </div>
                    <div class="session-actions">
                        <button class="delete-btn" onclick="event.stopPropagation(); showDeleteConfirmation('${session.session_id}', '${title.replace(/'/g, "\\'")}')">
                            🗑️
                        </button>
                    </div>
                `;

                // Add click event to load session
                sessionItem.onclick = () => loadChatSession(session.session_id);

                sessionList.appendChild(sessionItem);
            });
        }

        // Delete a single chat session
        async function confirmDeleteSession() {
            if (!pendingDeleteSessionId) return;

            try {
                const response = await fetch(`/chat-sessions/${pendingDeleteSessionId}`, {
                    method: 'DELETE',
                    headers: getAuthHeaders()
                });

                if (response.ok) {
                    // If deleted session was current, create new chat
                    if (pendingDeleteSessionId === currentSessionId) {
                        createNewChat();
                    }

                    // Reload chat history
                    loadChatHistory();
                    hideModal();

                    // Show success message
                    addMessage('Chat session deleted successfully.', false);
                } else {
                    throw new Error('Failed to delete chat session');
                }
            } catch (error) {
                console.error('Error deleting chat session:', error);
                addMessage('Error deleting chat session. Please try again.', false);
                hideModal();
            }
        }

        // Clear all chat sessions
        async function confirmClearAllSessions() {
            try {
                const response = await fetch('/chat-sessions', {
                    method: 'DELETE',
                    headers: getAuthHeaders()
                });

                if (response.ok) {
                    // Create new chat session
                    createNewChat();

                    // Reload chat history (should be empty now)
                    loadChatHistory();
                    hideModal();

                    // Show success message
                    addMessage('All chat sessions cleared successfully.', false);
                } else {
                    throw new Error('Failed to clear all chat sessions');
                }
            } catch (error) {
                console.error('Error clearing all chat sessions:', error);
                addMessage('Error clearing all chat sessions. Please try again.', false);
                hideModal();
            }
        }

        // Show empty history state
        function showEmptyHistoryState() {
            const sessionList = document.getElementById('session-list');
            sessionList.innerHTML = `
                <div class="empty-state">
                    <div class="icon">💬</div>
                    <p>No chat history yet</p>
                    <p style="font-size: 0.9em;">Start a new conversation!</p>
                </div>
            `;
        }

        // Load a specific chat session
        async function loadChatSession(sessionId) {
            try {
                const response = await fetch(`/chat-sessions/${sessionId}`, {
                    headers: getAuthHeaders()
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const session = await response.json();
                currentSessionId = sessionId;

                // Clear current messages
                const messagesContainer = document.getElementById('chat-messages');
                messagesContainer.innerHTML = '';

                // Load session messages
                if (session.messages && session.messages.length > 0) {
                    session.messages.forEach(msg => {
                        addMessage(msg.content, msg.role === 'user', msg.documents_used || []);
                    });
                } else {
                    addMessage('No messages in this session yet. Start a new conversation!', false);
                }

                // Refresh chat history to update active state
                loadChatHistory();

            } catch (error) {
                console.error('Error loading chat session:', error);
                addMessage('Error loading chat session. Please try again.', false);
            }
        }

        // Create new chat
        function createNewChat() {
            currentSessionId = 'session_' + Date.now();
            const messagesContainer = document.getElementById('chat-messages');
            messagesContainer.innerHTML = `
                <div class="welcome-message">
                    <div class="welcome-title">New Chat Started! 💫</div>
                    <div class="welcome-subtitle">
                        I'm ready to help you. Ask me anything or upload documents to search through.
                    </div>
                </div>
            `;
            loadChatHistory();
        }

        // Logout function
        function logout() {
            localStorage.removeItem('authToken');
            localStorage.removeItem('currentUser');
            window.location.href = '/';
        }

        // User dropdown menu
        document.getElementById('user-menu').addEventListener('click', function () {
            const dropdown = document.getElementById('dropdown-menu');
            dropdown.classList.toggle('show');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', function (event) {
            const dropdown = document.getElementById('dropdown-menu');
            const userMenu = document.getElementById('user-menu');

            if (!userMenu.contains(event.target) && !dropdown.contains(event.target)) {
                dropdown.classList.remove('show');
            }
        });

        // Close modal when clicking outside
        document.getElementById('confirmation-modal').addEventListener('click', function (event) {
            if (event.target === this) {
                hideModal();
            }
        });

        // Close modal with Escape key
        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape') {
                hideModal();
            }
        });

        // Initialize application
        document.addEventListener('DOMContentLoaded', function () {
            if (!checkAuthentication()) return;

            currentSessionId = 'session_' + Date.now();
            loadChatHistory();
            document.getElementById('user-input').focus();
        });

    </script>
</body>

</html>



 def find_relevant_documents(self, query: str) -> list:
        """Find documents relevant to the query using the database"""
        try:
            # Use the database search function
            relevant_docs = db.search_documents(query, limit=3)
            
            # Format the results to match the expected structure
            formatted_docs = []
            for doc in relevant_docs:
                if doc and 'content' in doc:
                    formatted_docs.append({
                        'path': doc.get('file_path', 'database'),
                        'filename': doc.get('filename', 'Unknown'),
                        'relevance_score': doc.get('relevance_score', 0),
                        'content': doc.get('content', '')  # Limit content size   [:5000]
                    })
            
            return formatted_docs
        except Exception as e:
            print(f"Error searching documents in database: {e}")
            return []
    
    def create_human_friendly_prompt(self, user_query: str, documents: list) -> list:
        """Create a human-friendly prompt that encourages natural, conversational responses"""
        
        document_context = ""
        if documents:
            document_context = "\n\nHere's some information I found that might be helpful:\n"
            for doc in documents:
                # Extract the most relevant sentences (first ~1000 chars usually contains key info)
                content = doc['content']
                # Try to get the most relevant sentences
                sentences = content.split('.')
                key_content = '. '.join(sentences[:10])  # First few sentences
                
                document_context += f"\n**From {doc['filename']}**:\n{key_content}\n---\n"
        
        # Enhanced system prompt for more natural responses
        system_prompt = f"""You are a friendly, knowledgeable assistant having a conversation. Your goal is to be helpful, clear, and engaging.

    PERSONALITY GUIDELINES:
    - Be warm and approachable, like a helpful colleague
    - Use natural conversation flow - not robotic or formulaic
    - Acknowledge the user's question in a friendly way
    - Break information into digestible, conversational chunks
    - Use "I" statements naturally ("I found...", "I think...")
    - When using document info, weave it in naturally without formal citations
    - Use conversational markers like "Actually...", "By the way...", "Interesting point!"
    - Show enthusiasm for helpful topics
    - End with inviting follow-up questions

    TONE & STYLE:
    - Conversational, not academic
    - Use contractions naturally (I'm, you're, that's)
    - Vary sentence length for natural rhythm
    - Use occasional phrases like "You might find it helpful to know..." 
    - If documents conflict or have gaps, acknowledge that naturally
    - Use examples and analogies that make sense in conversation

    {document_context}

    IMPORTANT: Answer in a flowing, natural way as if we're having a conversation. If the documents don't cover everything, fill in gaps with your knowledge but mention when you're doing so."""
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
    
    def create_structured_prompt(self, user_query: str, documents: list) -> list:
        """Create a structured prompt that forces organized responses"""
        
        document_context = ""
        for doc in documents:
            document_context += f"\n\n--- {doc['filename']} ---\n{doc['content']}"  #[:3000]
        
        system_prompt = f"""You are a helpful AI assistant. You provide clear, structured answers based on the provided documents when available.

AVAILABLE DOCUMENTS:{document_context}

RESPONSE GUIDELINES:
1. **Start by referencing the specific document(s)** you're using (if applicable)
2. **Use clear section headers** with markdown (## Header)
3. **Provide bullet points** for lists and steps
4. **Include code examples** where relevant
5. **Mention specific details** from the documents
6. **Keep explanations practical and actionable**

If the documents don't contain the information, provide your best answer based on general knowledge."""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
    
    async def generate_streaming_response(self, user_query: str, relevant_docs: list = None):
        """Generate streaming response with human-friendly conversation flow"""
        try:
            # Check if this is a greeting or casual conversation
            if self.is_casual_conversation(user_query):
                response_text = self.get_casual_response(user_query)
                for char in response_text:
                    yield f"data: {json.dumps({'type': 'content', 'content': char})}\n\n"
                    await asyncio.sleep(0.02)  # Slightly faster for casual chat
                yield f"data: {json.dumps({'type': 'complete', 'documents_used': []})}\n\n"
                return

            # For document queries with no results
            if not relevant_docs:
                # More natural "no docs found" message
                no_docs_messages = [
                    "I don't have specific documents on that, but based on what I know...",
                    "I couldn't find exact matches in my sources. From my understanding...",
                    "Let me share what I know about that topic..."
                ]
                
                intro = random.choice(no_docs_messages)
                for char in intro:
                    yield f"data: {json.dumps({'type': 'content', 'content': char})}\n\n"
                    await asyncio.sleep(0.015)
                
                # Now provide a general answer
                messages = [
                    {"role": "system", "content": "You're a friendly, knowledgeable assistant having a casual conversation. Keep it natural and conversational."},
                    {"role": "user", "content": user_query}
                ]
                
                stream = self.client.chat.completions.create(
                    messages=messages,
                    model=settings.GROQ_MODEL,
                    temperature=0.8,  # Higher for more natural variation
                    max_tokens=1200,
                    stream=True
                )
                
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                
                yield f"data: {json.dumps({'type': 'complete', 'documents_used': []})}\n\n"
                return

            # Use human-friendly prompt for document queries
            messages = self.create_human_friendly_prompt(user_query, relevant_docs)
            doc_names = [doc['filename'] for doc in relevant_docs]
            
            # First, send document info
            yield f"data: {json.dumps({'type': 'documents', 'documents': doc_names})}\n\n"
            
            # Stream the response with natural pacing
            stream = self.client.chat.completions.create(
                messages=messages,
                model=settings.GROQ_MODEL,
                temperature=0.7,
                max_tokens=1500,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                    # Vary delay slightly for more natural typing effect
                    await asyncio.sleep(random.uniform(0.01, 0.03))
            
            yield f"data: {json.dumps({'type': 'complete', 'documents_used': doc_names})}\n\n"
            
        except Exception as e:
            error_msg = f"Oops, I ran into a bit of a hiccup there: {str(e)}. Could you try asking again?"
            for char in error_msg:
                yield f"data: {json.dumps({'type': 'content', 'content': char})}\n\n"
                await asyncio.sleep(0.02)
            yield f"data: {json.dumps({'type': 'complete', 'documents_used': []})}\n\n"  