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
        console.log('[Frontend] Starting chat...');
        const response = await fetch(`${API_BASE_URL}/chat/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        });
        
        const data = await response.json();
        console.log('[Frontend] Chat started:', data);
        addBotMessage(data.response);
        
    } catch (error) {
        console.error('[Frontend] Error starting chat:', error);
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
        console.log('[Frontend] Sending message:', message);
        const response = await fetch(`${API_BASE_URL}/chat/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                message: message
            })
        });
        
        const data = await response.json();
        
        console.log('===== FULL API RESPONSE =====');
        console.log(JSON.stringify(data, null, 2));
        console.log('=============================');
        
        console.log('[Frontend] Response action:', data.action);
        console.log('[Frontend] Response stage:', data.stage);
        console.log('[Frontend] Response data.pdf_available:', data.data?.pdf_available);
        console.log('[Frontend] Response data.pdf_path:', data.data?.pdf_path);
        console.log('[Frontend] Response data.sanction_result:', data.data?.sanction_result);
        
        hideTyping();
        addBotMessage(data.response);
        
        // Handle special actions
        handleAction(data.action, data.data);
        
    } catch (error) {
        console.error('[Frontend] Error sending message:', error);
        hideTyping();
        addBotMessage('Oops! Something went wrong. Please try again.');
    }
}

function handleAction(action, data) {
    console.log('[Frontend] handleAction called');
    console.log('[Frontend] Action:', action);
    console.log('[Frontend] Data:', JSON.stringify(data, null, 2));
    
    if (action === 'request_document') {
        console.log('[Frontend] Showing upload area');
        uploadArea.style.display = 'flex';
    } else {
        uploadArea.style.display = 'none';
    }
    
    if (action === 'loan_approved') {
        console.log('[Frontend] ✅ LOAN APPROVED ACTION DETECTED!');
        console.log('[Frontend] Checking PDF availability...');
        console.log('[Frontend] pdf_available:', data.pdf_available);
        console.log('[Frontend] pdf_path:', data.pdf_path);
        
        if (data.pdf_available && data.pdf_path) {
            currentPdfPath = data.pdf_path;
            console.log('[Frontend] ✅ PDF path set to:', currentPdfPath);
            console.log('[Frontend] Opening download modal immediately...');
            
            // Show modal immediately without delay
            downloadModal.style.display = 'flex';
            console.log('[Frontend] ✅ Modal displayed! Style:', downloadModal.style.display);
            console.log('[Frontend] Modal element:', downloadModal);
        } else {
            console.error('[Frontend] ❌ PDF not available!');
            console.error('[Frontend] pdf_available:', data.pdf_available);
            console.error('[Frontend] pdf_path:', data.pdf_path);
        }
    } else {
        console.log('[Frontend] Action is not loan_approved, skipping download modal');
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
        console.log('[Frontend] Uploading file:', file.name);
        const response = await fetch(`${API_BASE_URL}/chat/upload`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        console.log('[Frontend] Upload response received');
        console.log('[Frontend] Upload response:', JSON.stringify(data, null, 2));
        
        uploadStatus.textContent = '✓ Uploaded successfully';
        uploadStatus.className = 'upload-status success';
        
        uploadArea.style.display = 'none';
        
        showTyping();
        setTimeout(() => {
            hideTyping();
            addBotMessage(data.response);
            
            console.log('[Frontend] Checking if approval happened after upload...');
            console.log('[Frontend] Data action:', data.action);
            console.log('[Frontend] Data stage:', data.stage);
            
            // If the response after upload shows sanction (approval), handle it
            if (data.action === 'loan_approved' || data.stage === 'completed') {
                console.log('[Frontend] ✅ Loan approved after file upload!');
                console.log('[Frontend] Upload response data object:', JSON.stringify(data.data, null, 2));
                
                // The upload response has a nested data object
                const uploadData = data.data || {};
                
                handleAction('loan_approved', {
                    pdf_available: uploadData.pdf_available || false,
                    pdf_path: uploadData.pdf_path,
                    sanction_result: uploadData.sanction_result
                });
            }
        }, 1000);
        
    } catch (error) {
        console.error('[Frontend] Error uploading file:', error);
        uploadStatus.textContent = '✗ Upload failed';
        uploadStatus.className = 'upload-status';
    }
    
    // Reset file input
    fileInput.value = '';
}

async function resetChat() {
    try {
        console.log('[Frontend] Resetting chat...');
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
        downloadModal.style.display = 'none';
        
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
                userInput.value = customer.phone;
                testModal.style.display = 'none';
                userInput.focus();
                
                // Try to copy to clipboard if available
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    navigator.clipboard.writeText(customer.phone).catch(err => {
                        console.log('Could not copy to clipboard:', err);
                    });
                }
            });
            
            customerList.appendChild(item);
        });
        
        testModal.style.display = 'flex';
        
    } catch (error) {
        console.error('Error fetching test customers:', error);
    }
}

function downloadSanctionLetter() {
    console.log('[Frontend] Download button clicked');
    
    if (!currentPdfPath) {
        console.error('[Frontend] ❌ No PDF path available!');
        alert('PDF not available for download');
        return;
    }
    
    console.log('[Frontend] 🔽 Downloading PDF:', currentPdfPath);
    
    // Extract just the filename
    const filename = currentPdfPath.includes('/') || currentPdfPath.includes('\\')
        ? currentPdfPath.split(/[/\\]/).pop() 
        : currentPdfPath;
    
    console.log('[Frontend] 📄 Filename:', filename);
    
    // Build download URL
    const baseUrl = API_BASE_URL.replace('/api', '');
    const downloadUrl = `${baseUrl}/api/download/${filename}`;
    
    console.log('[Frontend] 🔗 Download URL:', downloadUrl);
    
    // Try opening in new window first
    const win = window.open(downloadUrl, '_blank');
    
    // Fallback: Direct download
    if (!win) {
        console.log('[Frontend] Popup blocked, trying direct download...');
        
        fetch(downloadUrl)
            .then(response => {
                console.log('[Frontend] Response status:', response.status);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.blob();
            })
            .then(blob => {
                console.log('[Frontend] ✅ Blob received, size:', blob.size);
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                console.log('[Frontend] ✅ Download triggered');
            })
            .catch(error => {
                console.error('[Frontend] ❌ Download failed:', error);
                alert(`Failed to download PDF: ${error.message}`);
            });
    } else {
        console.log('[Frontend] ✅ Download window opened');
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