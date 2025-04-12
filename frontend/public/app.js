// Configuration
const API_URL = 'http://localhost:8000';
const WS_URL = 'ws://localhost:8000/ws';
const WS_AUTH_URL = 'ws://localhost:8000/ws/'; // Base URL for authenticated WebSocket

// DOM Elements
const authForms = document.getElementById('auth-forms');
const mainContent = document.getElementById('main-content');
const userInfo = document.getElementById('user-info');
const usernameDisplay = document.getElementById('username');
const logoutBtn = document.getElementById('logout-btn');
const loginForm = document.getElementById('login');
const registerForm = document.getElementById('register');
const loginError = document.getElementById('login-error');
const registerError = document.getElementById('register-error');
const postForm = document.getElementById('post-form');
const messagesContainer = document.getElementById('messages-container');
const messageTemplate = document.getElementById('message-template');
const tabBtns = document.querySelectorAll('.tab-btn');
const authFormContainers = document.querySelectorAll('.auth-form');
const filterTagInput = document.getElementById('filter-tag');
const applyFilterBtn = document.getElementById('apply-filter');
const clearFilterBtn = document.getElementById('clear-filter');
const sortNewestBtn = document.getElementById('sort-newest');
const sortOldestBtn = document.getElementById('sort-oldest');
const sortLikesBtn = document.getElementById('sort-likes');

// State
let currentUser = null;
let currentTag = null;
let socket = null;
let messages = [];
let currentSortMethod = 'newest'; // Default sort method

// Initialize the application
function init() {
    // Check if user is logged in
    const token = localStorage.getItem('token');
    if (token) {
        // Validate token and get user info
        fetchCurrentUser(token);
    } else {
        showAuthForms();
    }

    // Set up event listeners
    setupEventListeners();
}

// Event Listeners
function setupEventListeners() {
    // Tab switching
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.dataset.tab;
            
            // Update active tab button
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Show corresponding form
            authFormContainers.forEach(form => {
                form.classList.remove('active');
                if (form.id === `${tabId}-form`) {
                    form.classList.add('active');
                }
            });
        });
    });

    // Login form
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;
        
        try {
            await login(username, password);
        } catch (error) {
            loginError.textContent = error.message || 'Login failed';
        }
    });

    // Register form
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('register-username').value;
        const email = document.getElementById('register-email').value;
        const password = document.getElementById('register-password').value;
        
        try {
            await register(username, email, password);
        } catch (error) {
            registerError.textContent = error.message || 'Registration failed';
        }
    });

    // Logout button
    logoutBtn.addEventListener('click', logout);

    // Post form
    postForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const content = document.getElementById('post-content').value;
        const tagsInput = document.getElementById('post-tags').value;
        const tags = tagsInput ? tagsInput.split(',').map(tag => tag.trim()) : [];
        
        try {
            await createPost(content, tags);
            document.getElementById('post-content').value = '';
            document.getElementById('post-tags').value = '';
        } catch (error) {
            console.error('Error creating post:', error);
            alert('Failed to create post');
        }
    });

    // Tag filter
    applyFilterBtn.addEventListener('click', () => {
        const tag = filterTagInput.value.trim();
        if (tag) {
            currentTag = tag;
            fetchMessages();
        }
    });

    clearFilterBtn.addEventListener('click', () => {
        filterTagInput.value = '';
        currentTag = null;
        fetchMessages();
    });
    
    // Sort buttons
    sortNewestBtn.addEventListener('click', () => {
        setActiveSortMethod('newest');
    });
    
    sortOldestBtn.addEventListener('click', () => {
        setActiveSortMethod('oldest');
    });
    
    sortLikesBtn.addEventListener('click', () => {
        setActiveSortMethod('likes');
    });
}

// API Functions
async function fetchWithAuth(url, options = {}) {
    const token = localStorage.getItem('token');
    if (!token) {
        throw new Error('No authentication token');
    }
    
    const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers
    };
    
    const response = await fetch(url, {
        ...options,
        headers
    });
    
    if (response.status === 401) {
        // Token expired or invalid
        logout();
        throw new Error('Session expired. Please login again.');
    }
    
    return response;
}

async function login(username, password) {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await fetch(`${API_URL}/token`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: formData
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Login failed');
    }
    
    const data = await response.json();
    localStorage.setItem('token', data.access_token);
    
    // Get user info
    await fetchCurrentUser(data.access_token);
}

async function register(username, email, password) {
    const response = await fetch(`${API_URL}/users/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, email, password })
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Registration failed');
    }
    
    // Login after successful registration
    await login(username, password);
}

async function fetchCurrentUser(token) {
    try {
        const response = await fetch(`${API_URL}/users/me`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to get user info');
        }
        
        currentUser = await response.json();
        usernameDisplay.textContent = currentUser.username;
        
        // Show main content
        showMainContent();
        
        // Connect to WebSocket with the new token
        resetWebSocketConnection();
        
        // Fetch messages
        fetchMessages();
    } catch (error) {
        console.error('Error fetching user:', error);
        logout();
    }
}

async function fetchMessages() {
    try {
        let url = `${API_URL}/messages/`;
        if (currentTag) {
            url += `?tag=${encodeURIComponent(currentTag)}`;
        }
        
        const response = await fetchWithAuth(url);
        
        if (!response.ok) {
            throw new Error('Failed to fetch messages');
        }
        
        messages = await response.json();
        
        // Apply the current sort method
        sortMessages();
        
        // Render the sorted messages
        renderMessages();
    } catch (error) {
        console.error('Error fetching messages:', error);
    }
}

async function createPost(content, tags) {
    const response = await fetchWithAuth(`${API_URL}/messages/`, {
        method: 'POST',
        body: JSON.stringify({ content, tags })
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create post');
    }
    
    // We don't need to fetch messages here anymore
    // The new message will be received via WebSocket and added to the feed
    console.log('Post created successfully, waiting for WebSocket update');
    
    // Show a temporary message to the user
    const statusElement = document.createElement('div');
    statusElement.className = 'status-message';
    statusElement.textContent = 'Message posted! It will appear in the feed shortly.';
    document.querySelector('.post-form').appendChild(statusElement);
    
    // Remove the status message after a few seconds
    setTimeout(() => {
        statusElement.remove();
    }, 3000);
}

async function likeMessage(messageId) {
    try {
        const response = await fetchWithAuth(`${API_URL}/messages/${messageId}/like`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error('Failed to like message');
        }
        
        // Update the message in the UI
        const messageElement = document.querySelector(`.message[data-id="${messageId}"]`);
        if (messageElement) {
            const likeBtn = messageElement.querySelector('.like-btn');
            const likeCount = messageElement.querySelector('.like-count');
            
            likeBtn.classList.add('liked');
            likeCount.textContent = parseInt(likeCount.textContent) + 1;
        }
    } catch (error) {
        console.error('Error liking message:', error);
    }
}

async function unlikeMessage(messageId) {
    try {
        const response = await fetchWithAuth(`${API_URL}/messages/${messageId}/like`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Failed to unlike message');
        }
        
        // Update the message in the UI
        const messageElement = document.querySelector(`.message[data-id="${messageId}"]`);
        if (messageElement) {
            const likeBtn = messageElement.querySelector('.like-btn');
            const likeCount = messageElement.querySelector('.like-count');
            
            likeBtn.classList.remove('liked');
            likeCount.textContent = Math.max(0, parseInt(likeCount.textContent) - 1);
        }
    } catch (error) {
        console.error('Error unliking message:', error);
    }
}

// WebSocket Functions
function connectWebSocket() {
    if (socket) {
        console.log('Closing existing socket before creating a new one');
        socket.close();
    }
    
    // Get the authentication token
    const token = localStorage.getItem('token');
    
    // Choose the appropriate WebSocket URL based on whether we have a token
    const wsUrl = token ? `${WS_AUTH_URL}${token}` : WS_URL;
    
    console.log('Connecting to WebSocket at:', wsUrl);
    
    try {
        socket = new WebSocket(wsUrl);
        console.log('WebSocket object created:', socket);
    } catch (error) {
        console.error('Error creating WebSocket:', error);
        return;
    }
    
    socket.onopen = () => {
        console.log('WebSocket connected successfully');
    };
    
    socket.onmessage = (event) => {
        console.log('WebSocket message received:', event.data);
        try {
            const data = JSON.parse(event.data);
            console.log('Parsed WebSocket data:', data);
            handleWebSocketMessage(data);
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    };
    
    socket.onclose = (event) => {
        console.log('WebSocket disconnected with code:', event.code);
        
        // Show a notification to the user
        const statusElement = document.createElement('div');
        statusElement.className = 'status-message error';
        statusElement.textContent = 'Connection lost. Reconnecting...';
        document.body.appendChild(statusElement);
        
        // Remove the notification after a few seconds
        setTimeout(() => {
            if (statusElement.parentNode) {
                statusElement.remove();
            }
        }, 3000);
        
        // Try to reconnect after a delay, with exponential backoff
        // Start with 2 seconds, then 4, 8, etc. up to 30 seconds
        const reconnectDelay = Math.min(30000, (socket.reconnectAttempts || 1) * 2000);
        console.log(`Will attempt to reconnect in ${reconnectDelay/1000} seconds`);
        
        setTimeout(() => {
            if (currentUser) {
                // Increment reconnect attempts for exponential backoff
                socket.reconnectAttempts = (socket.reconnectAttempts || 1) * 2;
                connectWebSocket();
            }
        }, reconnectDelay);
    };
    
    socket.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
}

function handleWebSocketMessage(message) {
    console.log('Handling WebSocket message of type:', message.type);
    
    switch (message.type) {
        case 'new_message':
            console.log('New message received:', message.data);
            
            // Check if the message already exists in our feed
            const messageExists = messages.some(m => m.id === message.data.id);
            
            // Add new message to the feed if it's not filtered by tag and doesn't already exist
            if (!messageExists && (!currentTag || message.data.tags.some(tag => tag.name === currentTag))) {
                // Add the new message to the array
                messages.push(message.data);
                
                // Apply the current sort method
                sortMessages();
                
                // Re-render the messages
                renderMessages();
                
                // Add a visual indicator for new messages
                const newMessageElement = document.querySelector(`.message[data-id="${message.data.id}"]`);
                if (newMessageElement) {
                    newMessageElement.classList.add('new-message');
                    // Remove the highlight after a few seconds
                    setTimeout(() => {
                        newMessageElement.classList.remove('new-message');
                    }, 3000);
                }
                
                console.log('Message feed updated');
            } else if (messageExists) {
                console.log('Message already exists in feed, not adding duplicate');
            } else {
                console.log('Message filtered out due to tag filter');
            }
            break;
        case 'new_like':
            console.log('New like received:', message.data);
            // Update like count for the message
            const messageId = message.data.message_id;
            const messageElement = document.querySelector(`.message[data-id="${messageId}"]`);
            
            if (messageElement) {
                const likeCount = messageElement.querySelector('.like-count');
                
                // Update the like count with the new value from the server
                likeCount.textContent = message.data.like_count;
                
                // Add a brief highlight effect to the like count
                likeCount.classList.add('like-updated');
                setTimeout(() => {
                    likeCount.classList.remove('like-updated');
                }, 1500);
                
                console.log('Like count updated for message:', messageId);
                
                // Also update our local messages array to keep it in sync
                const messageIndex = messages.findIndex(m => m.id === messageId);
                if (messageIndex !== -1) {
                    messages[messageIndex].like_count = message.data.like_count;
                }
            } else {
                console.log('Message element not found for ID:', messageId);
                
                // If we don't have this message in the DOM yet, we might need to refresh
                // This could happen if the message was posted while we were filtered by a different tag
                if (currentTag === null) {
                    // Only refresh if we're not currently filtered, to avoid disrupting the user
                    fetchMessages();
                }
            }
            break;
        default:
            console.log('Unknown message type:', message.type);
    }
}

// UI Functions
function showAuthForms() {
    authForms.classList.remove('hidden');
    mainContent.classList.add('hidden');
    userInfo.classList.add('hidden');
}

function showMainContent() {
    authForms.classList.add('hidden');
    mainContent.classList.remove('hidden');
    userInfo.classList.remove('hidden');
}
function resetWebSocketConnection() {
    // Close existing connection if any
    if (socket) {
        console.log('Closing existing WebSocket connection');
        socket.close();
        socket = null;
    }
    
    // If user is logged in, establish a new connection
    if (currentUser) {
        console.log('Establishing new WebSocket connection');
        connectWebSocket();
    }
}

function logout() {
    localStorage.removeItem('token');
    currentUser = null;
    
    // Close WebSocket connection
    if (socket) {
        console.log('Closing WebSocket connection on logout');
        socket.close();
        socket = null;
    }
    
    showAuthForms();
    
    // Show logout message
    const statusElement = document.createElement('div');
    statusElement.className = 'status-message';
    statusElement.textContent = 'You have been logged out.';
    document.body.appendChild(statusElement);
    
    // Remove the message after a few seconds
    setTimeout(() => {
        if (statusElement.parentNode) {
            statusElement.remove();
        }
    }, 3000);
}

function renderMessages() {
    messagesContainer.innerHTML = '';
    
    messages.forEach(message => {
        const messageElement = document.importNode(messageTemplate.content, true);
        const messageDiv = messageElement.querySelector('.message');
        
        // Set message ID as data attribute
        messageDiv.dataset.id = message.id;
        
        // Set message content
        messageElement.querySelector('.username').textContent = message.username;
        messageElement.querySelector('.timestamp').textContent = formatDate(message.created_at);
        messageElement.querySelector('.message-content').textContent = message.content;
        
        // Set tags
        const tagsContainer = messageElement.querySelector('.message-tags');
        message.tags.forEach(tag => {
            const tagElement = document.createElement('span');
            tagElement.classList.add('tag');
            tagElement.textContent = tag.name;
            tagElement.addEventListener('click', () => {
                filterTagInput.value = tag.name;
                currentTag = tag.name;
                fetchMessages();
            });
            tagsContainer.appendChild(tagElement);
        });
        
        // Set like count
        const likeCount = messageElement.querySelector('.like-count');
        likeCount.textContent = message.like_count;
        
        // Set up like button
        const likeBtn = messageElement.querySelector('.like-btn');
        likeBtn.addEventListener('click', () => {
            if (likeBtn.classList.contains('liked')) {
                unlikeMessage(message.id);
            } else {
                likeMessage(message.id);
            }
        });
        
        messagesContainer.appendChild(messageElement);
    });
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

// Sorting functions
function setActiveSortMethod(method) {
    // Update the current sort method
    currentSortMethod = method;
    
    // Update the active button styling
    sortNewestBtn.classList.toggle('active', method === 'newest');
    sortOldestBtn.classList.toggle('active', method === 'oldest');
    sortLikesBtn.classList.toggle('active', method === 'likes');
    
    // Sort and re-render the messages
    sortMessages();
    renderMessages();
}

function sortMessages() {
    if (!messages || messages.length === 0) return;
    
    switch (currentSortMethod) {
        case 'newest':
            // Sort by created_at date, newest first
            messages.sort((a, b) => {
                const dateA = new Date(a.created_at);
                const dateB = new Date(b.created_at);
                return dateB - dateA; // Descending order (newest first)
            });
            break;
            
        case 'oldest':
            // Sort by created_at date, oldest first
            messages.sort((a, b) => {
                const dateA = new Date(a.created_at);
                const dateB = new Date(b.created_at);
                return dateA - dateB; // Ascending order (oldest first)
            });
            break;
            
        case 'likes':
            // Sort by like_count, most likes first
            messages.sort((a, b) => {
                return b.like_count - a.like_count; // Descending order (most likes first)
            });
            break;
            
        default:
            // Default to newest first
            messages.sort((a, b) => {
                const dateA = new Date(a.created_at);
                const dateB = new Date(b.created_at);
                return dateB - dateA;
            });
    }
}

// Initialize the application
init();