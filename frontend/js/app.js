// Configuration
const API_BASE_URL = 'http://localhost:5002/api';
let sessionId = 'session_' + Date.now();
let currentPdfPath = null;

// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const resetBtn = document.getElementById('resetBtn');
const testCustomersBtn = document.getElementById('testCustomersBtn');
const typingIndicator = document.getElementById('typingIndicator');
const uploadArea = document.getElementById('uploadArea');
const uploadBtn = document.getElementById('uploadBtn');
const fileInput = document.getElementById('fileInput');
const uploadStatus = document.getElementById('uploadStatus');
const testModal = document.getElementById('testModal');
const closeModal = document.getElementById('closeModal');
const customerList = document.getElementById('customerList');
const downloadModal = document.getElementById('downloadModal');
const closeDownloadModal = document.getElementById('closeDownloadModal');
const downloadBtn = document.getElementById('downloadBtn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    startChat();
    attachEventListeners();
});

function attachEventListeners() {
    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
    
    resetBtn.addEventListener('click', resetChat);
    testCustomersBtn.addEventListener('click', showTestCustomers);
    closeModal.addEventListener('click', () => testModal.style.display = 'none');
    closeDownloadModal.addEventListener('click', () => downloadModal.style.display = 'none');
    
    uploadBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileUpload);
    
    downloadBtn.addEventListener('click', downloadSanctionLetter);
}

async function startChat() {
    try {
        const response = await fetch(`${API_BASE_URL}/chat/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        });
        
        const data = await response.json();
        addBotMessage(data.response);
        
    } catch (error) {
        console.error('Error starting chat:', error);
        addBotMessage('Sorry, I\'m having trouble connecting. Please refresh the page.');
    }
}

async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;
    
    addUserMessage(message);
    userInput.value = '';
    showTyping();
    
    try {
        const response = await fetch(`${API_BASE_URL}/chat/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                message: message
            })
        });
        
        const data = await response.json();
        
        console.log('API Response:', data);
        
        hideTyping();
        addBotMessage(data.response);
        
        // Handle special actions
        handleAction(data.action, data.data);
        
    } catch (error) {
        console.error('Error sending message:', error);
        hideTyping();
        addBotMessage('Oops! Something went wrong. Please try again.');
    }
}

function handleAction(action, data) {
    console.log('Action:', action);
    console.log('Data:', data);
    
    if (action === 'request_document') {
        uploadArea.style.display = 'flex';
    } else {
        uploadArea.style.display = 'none';
    }
    
    if (action === 'loan_approved') {
        console.log('Loan approved! Checking PDF...');
        console.log('PDF Available:', data.pdf_available);
        console.log('PDF Path:', data.pdf_path);
        
        if (data.pdf_available && data.pdf_path) {
            currentPdfPath = data.pdf_path;
            console.log('✅ PDF path set:', currentPdfPath);
            
            setTimeout(() => {
                console.log('Opening download modal...');
                downloadModal.style.display = 'flex';
            }, 1000);
        } else {
            console.error('❌ PDF not available or path missing');
        }
    }
}

async function handleFileUpload() {
    const file = fileInput.files[0];
    if (!file) return;
    
    uploadStatus.textContent = 'Uploading...';
    uploadStatus.className = 'upload-status';
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', sessionId);
    
    try {
        const response = await fetch(`${API_BASE_URL}/chat/upload`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        uploadStatus.textContent = '✓ Uploaded successfully';
        uploadStatus.className = 'upload-status success';
        
        uploadArea.style.display = 'none';
        
        showTyping();
        setTimeout(() => {
            hideTyping();
            addBotMessage(data.response);
            
            // Trigger next step if needed
            if (data.next_step === 'underwriting') {
                setTimeout(() => {
                    sendMessage();
                }, 1000);
            }
        }, 2000);
        
    } catch (error) {
        console.error('Error uploading file:', error);
        uploadStatus.textContent = '✗ Upload failed';
        uploadStatus.className = 'upload-status';
    }
}

async function resetChat() {
    try {
        await fetch(`${API_BASE_URL}/chat/reset`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        });
        
        // Clear chat
        chatMessages.innerHTML = `
            <div class="welcome-banner">
                <h2>Welcome! 👋</h2>
                <p>Get your personal loan approved in minutes</p>
                <div class="features">
                    <div class="feature-item">
                        <span class="feature-icon">⚡</span>
                        <span>Instant Approval</span>
                    </div>
                    <div class="feature-item">
                        <span class="feature-icon">💰</span>
                        <span>Up to ₹20 Lakh</span>
                    </div>
                    <div class="feature-item">
                        <span class="feature-icon">📄</span>
                        <span>Minimal Documentation</span>
                    </div>
                </div>
            </div>
        `;
        
        // Generate new session
        sessionId = 'session_' + Date.now();
        currentPdfPath = null;
        uploadArea.style.display = 'none';
        
        // Restart chat
        startChat();
        
    } catch (error) {
        console.error('Error resetting chat:', error);
    }
}

async function showTestCustomers() {
    try {
        const response = await fetch(`${API_BASE_URL}/customers`);
        const data = await response.json();
        
        customerList.innerHTML = '';
        
        data.customers.forEach(customer => {
            const item = document.createElement('div');
            item.className = 'customer-item';
            item.innerHTML = `
                <div class="customer-info">
                    <h4>${customer.name}</h4>
                    <p>${customer.city} • Pre-approved: ₹${customer.pre_approved_limit.toLocaleString('en-IN')}</p>
                </div>
                <div class="customer-phone">${customer.phone}</div>
            `;
            
            item.addEventListener('click', () => {
                navigator.clipboard.writeText(customer.phone);
                userInput.value = customer.phone;
                testModal.style.display = 'none';
                userInput.focus();
            });
            
            customerList.appendChild(item);
        });
        
        testModal.style.display = 'flex';
        
    } catch (error) {
        console.error('Error fetching test customers:', error);
    }
}

function downloadSanctionLetter() {
    if (!currentPdfPath) {
        console.error('No PDF path available');
        alert('PDF not available for download');
        return;
    }
    
    console.log('🔽 Downloading PDF:', currentPdfPath);
    
    // Extract just the filename
    const filename = currentPdfPath.includes('/') || currentPdfPath.includes('\\')
        ? currentPdfPath.split(/[/\\]/).pop() 
        : currentPdfPath;
    
    console.log('📄 Filename:', filename);
    
    // Build download URL
    const baseUrl = API_BASE_URL.replace('/api', '');
    const downloadUrl = `${baseUrl}/api/download/${filename}`;
    
    console.log('🔗 Download URL:', downloadUrl);
    
    // Try opening in new window first
    const win = window.open(downloadUrl, '_blank');
    
    // Fallback: Direct download
    if (!win) {
        console.log('Popup blocked, trying direct download...');
        
        fetch(downloadUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.blob();
            })
            .then(blob => {
                console.log('✅ Blob received, size:', blob.size);
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                console.log('✅ Download triggered');
            })
            .catch(error => {
                console.error('❌ Download failed:', error);
                alert(`Failed to download PDF: ${error.message}`);
            });
    }
    
    downloadModal.style.display = 'none';
}

function addUserMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user';
    messageDiv.innerHTML = `
        <div class="message-content">${escapeHtml(text)}</div>
    `;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addBotMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot';
    messageDiv.innerHTML = `
        <div class="message-content">${escapeHtml(text)}</div>
    `;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function showTyping() {
    typingIndicator.style.display = 'flex';
    scrollToBottom();
}

function hideTyping() {
    typingIndicator.style.display = 'none';
}

function scrollToBottom() {
    setTimeout(() => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 100);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/\n/g, '<br>');
}

// Close modal on outside click
window.addEventListener('click', (e) => {
    if (e.target === testModal) {
        testModal.style.display = 'none';
    }
    if (e.target === downloadModal) {
        downloadModal.style.display = 'none';
    }
});