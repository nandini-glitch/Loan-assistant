// Configuration
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:5002/api'
    : 'https://loan-assistant-backend.onrender.com';  // Replace with your actual backend URL
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
    console.log('[Frontend] 🚀 Application starting...');
    console.log('[Frontend] API Base URL:', API_BASE_URL);
    console.log('[Frontend] Session ID:', sessionId);
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
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
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
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        console.log('\n===== FULL API RESPONSE (/chat/message) =====');
        console.log(JSON.stringify(data, null, 2));
        console.log('=============================================\n');
        
        hideTyping();
        addBotMessage(data.response);
        
        // Process action
        processApiResponse(data);
        
    } catch (error) {
        console.error('[Frontend] Error sending message:', error);
        hideTyping();
        addBotMessage('Oops! Something went wrong. Please try again.');
    }
}

/**
 * ✅ UNIFIED function to process ALL API responses
 */
function processApiResponse(data) {
    console.log('\n[Frontend] ===== processApiResponse =====');
    console.log('[Frontend] Action:', data.action);
    console.log('[Frontend] Stage:', data.stage);
    
    // Extract PDF info from BOTH possible locations
    const pdfAvailable = data.pdf_available || data.data?.pdf_available || false;
    const pdfPath = data.pdf_path || data.data?.pdf_path || null;
    
    console.log('[Frontend] PDF Available (computed):', pdfAvailable);
    console.log('[Frontend] PDF Path (computed):', pdfPath);
    
    // Handle document upload request
    if (data.action === 'request_document') {
        console.log('[Frontend] 📄 Showing upload area');
        uploadArea.style.display = 'flex';
    } else {
        uploadArea.style.display = 'none';
    }
    
    // Handle loan approval
    if (data.action === 'loan_approved' || (data.stage === 'completed' && pdfAvailable)) {
        console.log('[Frontend] 🎉 LOAN APPROVED!');
        
        if (pdfAvailable && pdfPath) {
            currentPdfPath = pdfPath;
            console.log('[Frontend] ✅ PDF path set:', currentPdfPath);
            console.log('[Frontend] 🎊 Opening download modal...');
            
            // Show modal
            downloadModal.style.display = 'flex';
            console.log('[Frontend] ✅ Modal display set to:', downloadModal.style.display);
        } else {
            console.error('[Frontend] ❌ PDF info missing!');
            console.error('[Frontend]   - pdfAvailable:', pdfAvailable);
            console.error('[Frontend]   - pdfPath:', pdfPath);
            addBotMessage('⚠️ Loan approved, but sanction letter generation failed. Please contact support.');
        }
    }
    
    console.log('[Frontend] =========================================\n');
}

async function handleFileUpload() {
    const file = fileInput.files[0];
    if (!file) {
        console.log('[Frontend] No file selected');
        return;
    }
    
    console.log('\n[Frontend] ===== FILE UPLOAD START =====');
    console.log('[Frontend] File:', file.name);
    console.log('[Frontend] Size:', file.size, 'bytes');
    console.log('[Frontend] Type:', file.type);
    console.log('[Frontend] Session ID:', sessionId);
    console.log('[Frontend] ================================\n');
    
    // Validate file
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'];
    if (!allowedTypes.includes(file.type)) {
        console.error('[Frontend] Invalid file type:', file.type);
        uploadStatus.textContent = '✗ Invalid file type. Please upload PDF, JPG, or PNG';
        uploadStatus.className = 'upload-status error';
        fileInput.value = '';
        return;
    }
    
    const maxSize = 5 * 1024 * 1024; // 5MB
    if (file.size > maxSize) {
        console.error('[Frontend] File too large:', file.size);
        uploadStatus.textContent = '✗ File too large. Maximum 5MB';
        uploadStatus.className = 'upload-status error';
        fileInput.value = '';
        return;
    }
    
    uploadStatus.textContent = 'Uploading...';
    uploadStatus.className = 'upload-status uploading';
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', sessionId);
    
    // Log FormData contents
    console.log('[Frontend] FormData contents:');
    for (let pair of formData.entries()) {
        console.log(`  ${pair[0]}:`, pair[1]);
    }
    
    try {
        console.log('[Frontend] 📤 Uploading to:', `${API_BASE_URL}/chat/upload`);
        console.log('[Frontend] Request method: POST');
        console.log('[Frontend] Sending FormData with file and session_id');
        
        const response = await fetch(`${API_BASE_URL}/chat/upload`, {
            method: 'POST',
            mode: 'cors',
            body: formData
        });
        
        console.log('[Frontend] Upload response received');
        console.log('[Frontend] Response status:', response.status);
        console.log('[Frontend] Response ok:', response.ok);
        console.log('[Frontend] Response headers:', {
            contentType: response.headers.get('content-type'),
            contentLength: response.headers.get('content-length')
        });
        
        if (!response.ok) {
            let errorText = 'Unknown error';
            try {
                errorText = await response.text();
                console.error('[Frontend] Error response body:', errorText);
            } catch (e) {
                console.error('[Frontend] Could not read error response:', e);
            }
            throw new Error(`Upload failed: HTTP ${response.status} - ${errorText}`);
        }
        
        const responseText = await response.text();
        console.log('[Frontend] Raw response text length:', responseText.length);
        console.log('[Frontend] Raw response preview:', responseText.substring(0, 200));
        
        let data;
        try {
            data = JSON.parse(responseText);
        } catch (parseError) {
            console.error('[Frontend] JSON parse error:', parseError);
            console.error('[Frontend] Response was:', responseText);
            throw new Error('Invalid JSON response from server');
        }
        
        console.log('\n===== FULL API RESPONSE (/chat/upload) =====');
        console.log(JSON.stringify(data, null, 2));
        console.log('============================================\n');
        
        uploadStatus.textContent = '✓ Uploaded successfully';
        uploadStatus.className = 'upload-status success';
        uploadArea.style.display = 'none';
        
        showTyping();
        setTimeout(() => {
            hideTyping();
            addBotMessage(data.response);
            
            // Process the upload response
            processApiResponse(data);
            
        }, 1000);
        
    } catch (error) {
        console.error('\n[Frontend] ===== UPLOAD ERROR =====');
        console.error('[Frontend] Error name:', error.name);
        console.error('[Frontend] Error message:', error.message);
        console.error('[Frontend] Error stack:', error.stack);
        
        // Check if it's a network error
        if (error.message.includes('Load failed') || error.name === 'TypeError') {
            console.error('[Frontend] ❌ NETWORK ERROR - Backend might not be running or CORS issue');
            uploadStatus.textContent = '✗ Cannot connect to server. Is the backend running?';
            addBotMessage('⚠️ Cannot connect to server. Please ensure the backend is running on http://localhost:5002');
        } else {
            uploadStatus.textContent = '✗ Upload failed: ' + error.message;
            addBotMessage('⚠️ Upload failed. Please try again.');
        }
        
        uploadStatus.className = 'upload-status error';
        console.error('[Frontend] ===================================\n');
        
    } finally {
        fileInput.value = '';
        console.log('[Frontend] File input cleared');
    }
}

async function resetChat() {
    try {
        console.log('[Frontend] 🔄 Resetting chat...');
        
        await fetch(`${API_BASE_URL}/chat/reset`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        });
        
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
        
        sessionId = 'session_' + Date.now();
        currentPdfPath = null;
        uploadArea.style.display = 'none';
        downloadModal.style.display = 'none';
        
        startChat();
        console.log('[Frontend] ✅ Chat reset complete');
        
    } catch (error) {
        console.error('[Frontend] Reset error:', error);
    }
}

async function showTestCustomers() {
    try {
        const response = await fetch(`${API_BASE_URL}/customers`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        customerList.innerHTML = '';
        
        if (!data.customers || data.customers.length === 0) {
            customerList.innerHTML = '<p style="padding: 20px; text-align: center;">No test customers available</p>';
            testModal.style.display = 'flex';
            return;
        }
        
        data.customers.forEach(customer => {
            const item = document.createElement('div');
            item.className = 'customer-item';
            item.innerHTML = `
                <div class="customer-info">
                    <h4>${escapeHtml(customer.name)}</h4>
                    <p>${escapeHtml(customer.city)} • Pre-approved: ₹${customer.pre_approved_limit.toLocaleString('en-IN')}</p>
                </div>
                <div class="customer-phone">${escapeHtml(customer.phone)}</div>
            `;
            
            item.addEventListener('click', () => {
                userInput.value = customer.phone;
                testModal.style.display = 'none';
                userInput.focus();
                
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    navigator.clipboard.writeText(customer.phone).catch(() => {});
                }
            });
            
            customerList.appendChild(item);
        });
        
        testModal.style.display = 'flex';
        
    } catch (error) {
        console.error('[Frontend] Error loading test customers:', error);
        alert('Failed to load test customers');
    }
}

function downloadSanctionLetter() {
    console.log('[Frontend] 🔽 Download button clicked');
    
    if (!currentPdfPath) {
        console.error('[Frontend] ❌ No PDF path available!');
        alert('PDF not available for download');
        return;
    }
    
    console.log('[Frontend] 📄 Downloading:', currentPdfPath);
    
    // Extract filename
    const filename = currentPdfPath.includes('/') || currentPdfPath.includes('\\')
        ? currentPdfPath.split(/[/\\]/).pop() 
        : currentPdfPath;
    
    console.log('[Frontend] 📄 Filename:', filename);
    
    const baseUrl = API_BASE_URL.replace('/api', '');
    const downloadUrl = `${baseUrl}/api/download/${encodeURIComponent(filename)}`;
    
    console.log('[Frontend] 🔗 Download URL:', downloadUrl);
    
    // Try popup first
    const win = window.open(downloadUrl, '_blank');
    
    if (!win) {
        console.log('[Frontend] Popup blocked, using direct download...');
        directDownload(downloadUrl, filename);
    } else {
        console.log('[Frontend] ✅ Download window opened');
        downloadModal.style.display = 'none';
    }
}

function directDownload(url, filename) {
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.blob();
        })
        .then(blob => {
            const blobUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = blobUrl;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(blobUrl);
            document.body.removeChild(a);
            console.log('[Frontend] ✅ Download complete');
            downloadModal.style.display = 'none';
        })
        .catch(error => {
            console.error('[Frontend] ❌ Download failed:', error);
            alert(`Failed to download PDF: ${error.message}`);
        });
}

function addUserMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user';
    messageDiv.innerHTML = `<div class="message-content">${escapeHtml(text)}</div>`;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addBotMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot';
    messageDiv.innerHTML = `<div class="message-content">${escapeHtml(text)}</div>`;
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

// Close modals on outside click
window.addEventListener('click', (e) => {
    if (e.target === testModal) testModal.style.display = 'none';
    if (e.target === downloadModal) downloadModal.style.display = 'none';
});

// Close modals on Escape key
window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        if (testModal.style.display === 'flex') testModal.style.display = 'none';
        if (downloadModal.style.display === 'flex') downloadModal.style.display = 'none';
    }
});

console.log('[Frontend] 🚀 App.js loaded successfully');