// Scroll chat to bottom on load
const chatWindow = document.getElementById('chat-window');
if (chatWindow) chatWindow.scrollTop = chatWindow.scrollHeight;

// Get form elements
const chatForm = document.getElementById('chat-form');
const textarea = chatForm.querySelector('textarea[name="user_message"]');
const sendButton = document.getElementById('send-button');
const sendIcon = document.getElementById('send-icon');
const spinner = document.getElementById('spinner');

// Photo upload elements
const photoBtn = document.getElementById('photoBtn');
const photoInput = document.getElementById('photoInput');
const photoUploadSection = document.getElementById('photoUploadSection');
const photoPreview = document.getElementById('photoPreview');
const plantSelect = document.getElementById('plantSelect');
const plantIdInput = document.getElementById('plantIdInput');

// Photo upload functionality
let selectedPhoto = null;
let isSubmitting = false; // Prevent multiple submissions

photoBtn.addEventListener('click', function() {
    photoInput.click();
});

photoInput.addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        handlePhotoSelect(file);
    }
});

// Handle drag and drop for photos
photoUploadSection.addEventListener('dragover', function(e) {
    e.preventDefault();
    photoUploadSection.classList.add('dragover');
});

photoUploadSection.addEventListener('dragleave', function(e) {
    e.preventDefault();
    photoUploadSection.classList.remove('dragover');
});

photoUploadSection.addEventListener('drop', function(e) {
    e.preventDefault();
    photoUploadSection.classList.remove('dragover');

    const files = e.dataTransfer.files;
    if (files.length > 0 && files[0].type.startsWith('image/')) {
        photoInput.files = files;
        handlePhotoSelect(files[0]);
    }
});

function handlePhotoSelect(file) {
    selectedPhoto = file;

    // Show photo upload section
    photoUploadSection.style.display = 'block';
    photoBtn.classList.add('active');

    // Create preview
    const reader = new FileReader();
    reader.onload = function(e) {
        photoPreview.innerHTML = `
            <img src="${e.target.result}" alt="Photo preview">
            <p><strong>${file.name}</strong> (${(file.size / 1024 / 1024).toFixed(2)} MB)</p>
            <button type="button" onclick="clearPhotoSelection()" class="btn btn-sm btn-secondary">
                <i class="fa-solid fa-trash"></i>
            </button>
        `;
    };
    reader.readAsDataURL(file);

    // Update placeholder text
    textarea.placeholder = "Describe what you'd like me to analyze in this photo...";
}

function clearPhotoSelection() {
    selectedPhoto = null;
    photoInput.value = '';
    photoUploadSection.style.display = 'none';
    photoBtn.classList.remove('active');
    photoPreview.innerHTML = '';
    plantIdInput.value = '';
    plantSelect.value = '';
    textarea.placeholder = "Type a message or upload a photo for analysis...";
}

// Update plant selection
plantSelect.addEventListener('change', function() {
    plantIdInput.value = this.value;
});

// Function to show typing indicator
function showTypingIndicator() {
    const typingRow = document.createElement('div');
    typingRow.className = 'chat-row bot';
    typingRow.id = 'typing-indicator';

    typingRow.innerHTML = `
        <span class="chat-avatar">
            <i class="fas fa-seedling"></i>
        </span>
        <div class="typing-indicator">
            <span class="typing-text">${selectedPhoto ? 'PlantPal is analyzing your photo' : 'PlantPal is thinking'}</span>
            <div class="typing-dots">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
    `;

    chatWindow.appendChild(typingRow);
    chatWindow.scrollTop = chatWindow.scrollHeight;

}

// Function to hide typing indicator
function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Function to show loading state
function showLoadingState() {
    sendButton.disabled = true;
    sendIcon.style.display = 'none';
    spinner.style.display = 'block';
    textarea.disabled = true;
    if (photoBtn) photoBtn.disabled = true;
}

// Function to hide loading state
function hideLoadingState() {
    sendButton.disabled = false;
    sendIcon.style.display = 'block';
    spinner.style.display = 'none';
    textarea.disabled = false;
    if (photoBtn) photoBtn.disabled = false;
}

// Helper function to add user message to chat
function addUserMessageToChat(messageText, photo, plantId) {
    const userRow = document.createElement('div');
    userRow.className = 'chat-row user';

    let messageContent = '';
    if (photo) {
        const plantName = plantSelect.options[plantSelect.selectedIndex]?.text || 'Selected plant';
        messageContent = `📸 <em>Uploaded photo: ${photo.name}</em><br>`;
        messageContent += `🌱 <em>Plant: ${plantName}</em><br>`;
    }
    messageContent += messageText || 'Please analyze this photo for any plant health issues.';

    userRow.innerHTML = `
        <div class="chat-bubble user-bubble">
            ${messageContent}
            <div class="message-time">Now</div>
        </div>
        <span class="chat-avatar user-avatar">
            <i class="fas fa-user"></i>
        </span>
    `;

    chatWindow.appendChild(userRow);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

// Helper function to add bot message to chat
function addBotMessageToChat(botResponse) {
    hideTypingIndicator();

    const botRow = document.createElement('div');
    botRow.className = 'chat-row bot';

    botRow.innerHTML = `
        <span class="chat-avatar">
            <i class="fas fa-seedling"></i>
        </span>
        <div class="chat-bubble bot-bubble">
            ${botResponse}
            <div class="message-time">Now</div>
        </div>
    `;

    chatWindow.appendChild(botRow);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

// Helper function to show error messages
function showMessage(message, type = 'info') {
    // Create a temporary alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.style.position = 'fixed';
    alertDiv.style.top = '20px';
    alertDiv.style.right = '20px';
    alertDiv.style.zIndex = '9999';
    alertDiv.style.minWidth = '300px';

    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
            <span aria-hidden="true">&times;</span>
        </button>
    `;

    document.body.appendChild(alertDiv);

    // Auto remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 5000);

    // Add click handler for close button
    const closeBtn = alertDiv.querySelector('.close');
    closeBtn.addEventListener('click', () => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    });
}

// Main chat form submission handler - FIXED VERSION
async function handleChatSubmit(e) {
    e.preventDefault();

    // Prevent multiple submissions
    if (isSubmitting) {
        return;
    }

    const messageText = textarea.value.trim();
    const selectedPlantId = plantSelect.value || plantIdInput.value;

    console.log('Chat form data:', {
        messageText,
        hasPhoto: !!selectedPhoto,
        plantId: selectedPlantId
    });

    // Validation
    if (!messageText && !selectedPhoto) {
        showMessage("Please enter a message or upload a photo.", 'warning');
        return;
    }
    if (selectedPhoto && !selectedPlantId) {
        showMessage("Please select a plant when uploading a photo.", 'warning');
        return;
    }

    // Set submitting state
    isSubmitting = true;
    showLoadingState();

    // Hide photo preview section immediately when send is clicked
    if (selectedPhoto) {
        photoUploadSection.style.display = 'none';
        photoBtn.classList.remove('active');
    }

    // Add user message to chat immediately (optimistic update)
    addUserMessageToChat(messageText, selectedPhoto, selectedPlantId);

    // Show typing indicator
    showTypingIndicator();

    // Prepare form data
    const formData = new FormData();
    const finalMessage = messageText || 'Please analyze this photo for any plant health issues.';
    formData.append('user_message', finalMessage);

    if (selectedPhoto) {
        formData.append('photo_file', selectedPhoto, selectedPhoto.name);
    }

    if (selectedPlantId) {
        formData.append('plant_id', selectedPlantId.toString());
    }

    try {
        // Submit to backend using fetch
        const response = await fetch('/ai_chat', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest' // Indicate AJAX request
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Check if response is JSON (bot response) or HTML (redirect)
        const contentType = response.headers.get('content-type');

        if (contentType && contentType.includes('application/json')) {
            // Handle JSON response with bot message
            const data = await response.json();

            if (data.success && data.bot_response) {
                addBotMessageToChat(data.bot_response);
            } else {
                throw new Error(data.error || 'Unknown error occurred');
            }
        } else {
            // Handle HTML response - extract bot message from the response
            const htmlText = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(htmlText, 'text/html');

            // Try to extract the latest bot message from the response HTML
            const botMessages = doc.querySelectorAll('.chat-row.bot:not(#typing-indicator)');
            if (botMessages.length > 0) {
                const latestBotMessage = botMessages[botMessages.length - 1];
                const botBubble = latestBotMessage.querySelector('.chat-bubble');
                if (botBubble) {
                    addBotMessageToChat(botBubble.innerHTML);
                } else {
                    throw new Error('Could not extract bot response');
                }
            } else {
                throw new Error('No bot response found');
            }
        }

        // Clear form after successful submission
        textarea.value = '';
        clearPhotoSelection();

    } catch (error) {
        console.error('Chat submission error:', error);

        // Remove the optimistically added user message on error
        const lastUserMessage = chatWindow.querySelector('.chat-row.user:last-of-type');
        if (lastUserMessage) {
            lastUserMessage.remove();
        }

        hideTypingIndicator();
        showMessage(`Error sending message: ${error.message}`, 'danger');

    } finally {
        // Always reset loading state
        hideLoadingState();
        isSubmitting = false;
    }
}

// Attach the event listener
chatForm.addEventListener('submit', handleChatSubmit);

// Auto-submit on Enter key (but allow Shift+Enter for new line)
textarea.addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
    }
});

// Auto-resize textarea as user types
textarea.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px'; // Max height of 120px
});

// Focus textarea on page load
window.addEventListener('load', function() {
    textarea.focus();
});

// Check if page is reloading after form submission
if (performance.navigation.type === 1) {
    // Page was reloaded, hide any existing typing indicator
    hideTypingIndicator();
}

// Quick photo analysis functions
function addPhotoAnalysisButtons() {
    const photoMessages = document.querySelectorAll('.chat-bubble:contains("📸")');
    photoMessages.forEach(message => {
        if (!message.querySelector('.photo-actions')) {
            const actions = document.createElement('div');
            actions.className = 'photo-actions';
            actions.innerHTML = `
                <button onclick="requestPhotoReanalysis()" class="btn btn-sm btn-secondary">
                    <i class="fas fa-redo"></i> Re-analyze
                </button>
            `;
            message.appendChild(actions);
        }
    });
}

function requestPhotoReanalysis() {
    textarea.value = 'Can you provide a more detailed analysis of my recent photo?';
    chatForm.dispatchEvent(new Event('submit'));
}