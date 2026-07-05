// Dashboard functionality for Plant Care Task Management

document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initializing...');

    setupRecurrenceLogic();
    setupModalCloseEvents();

    console.log('Dashboard initialization complete');
});

// Setup modal close on background click
function setupModalCloseEvents() {
    const taskModal = document.getElementById('task-modal');
    const taskForm = document.getElementById('task-form');

    if (taskModal) {
        taskModal.addEventListener('click', function(e) {
            if (e.target === taskModal) {
                closeTaskModal();
            }
        });
    }

    if (taskForm) {
        taskForm.addEventListener('submit', handleTaskSubmit);
    }
}

// Complete task function
async function completeTask(taskId, isCompleted = true) {
    try {
        const response = await fetch(`/dashboard/tasks/${taskId}/complete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                is_completed: isCompleted
            })
        });

        if (response.ok) {
            showMessage('Task status updated successfully!', 'success');
            location.reload();
        } else {
            throw new Error('Failed to update task status');
        }
    } catch (error) {
        console.error('Error updating task status:', error);
        showMessage('Failed to update task status.', 'error');
    }
}

// Handle task form submission
async function handleTaskSubmit(e) {
    e.preventDefault();

    const form = e.target;
    const taskId = form.getAttribute('data-task-id');
    const isEditing = !!taskId;

    try {
        const formData = new FormData(form);
        const recurrenceType = formData.get('recurrence_type');
        let frequencyDays = parseInt(formData.get('frequency_days'));

        // If custom recurrence, use the user-entered value
        // Otherwise, get the frequency based on recurrence type
        if (recurrenceType !== 'custom' && recurrenceType !== 'none') {
            frequencyDays = getFrequencyForRecurrence(recurrenceType);
        }

        // Clear and rebuild FormData with proper values
        formData.set('plant_id', formData.get('plant_id'));
        formData.set('task_type', formData.get('task_type').toLowerCase());
        formData.set('title', formData.get('title'));
        formData.set('description', formData.get('description'));
        formData.set('recurrence_type', recurrenceType);
        formData.set('frequency_days', frequencyDays);

        console.log('Sending task data:', {
            plant_id: formData.get('plant_id'),
            task_type: formData.get('task_type'),
            title: formData.get('title'),
            description: formData.get('description'),
            recurrence_type: formData.get('recurrence_type'),
            frequency_days: formData.get('frequency_days')
        });

        const url = isEditing ? `/dashboard/tasks/${taskId}` : '/dashboard/tasks';
        const method = isEditing ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            body: formData
        });

        if (response.ok) {
            closeTaskModal();
            const message = isEditing ? 'Task updated successfully!' : 'Task created successfully!';
            showMessage(message, 'success');
            setTimeout(() => location.reload(), 500);
        } else {
            const errorData = await response.json();
            console.error('Server error:', errorData);
            const errorMsg = errorData.detail?.[0]?.msg || 'Unknown error';
            showMessage(`Failed to save task: ${errorMsg}`, 'error');
        }
    } catch (error) {
        console.error('Error saving task:', error);
        showMessage('Failed to save task. Please try again.', 'error');
    }
}

// Setup recurrence and frequency input logic
function setupRecurrenceLogic() {
    const recurrenceSelect = document.getElementById('recurrence_type');
    const frequencyInput = document.getElementById('frequency_days');

    function updateFrequencyInput() {
        if (!recurrenceSelect || !frequencyInput) return;

        const selectedValue = recurrenceSelect.value;

        if (selectedValue === 'custom') {
            frequencyInput.disabled = false;
            frequencyInput.placeholder = 'Enter custom days';
            if (!frequencyInput.value) {
                frequencyInput.value = '';
            }
        } else {
            frequencyInput.disabled = true;
            const frequency = getFrequencyForRecurrence(selectedValue);
            frequencyInput.value = frequency;
        }
    }

    if (recurrenceSelect && frequencyInput) {
        recurrenceSelect.addEventListener('change', updateFrequencyInput);
        updateFrequencyInput();
    }
}

// Helper function to get frequency days based on recurrence type
function getFrequencyForRecurrence(recurrenceType) {
    switch (recurrenceType) {
        case 'none':
            return 0;
        case 'daily':
            return 1;
        case 'weekly':
            return 7;
        case 'monthly':
            return 30;
        case 'weekend':
            return 7;
        case 'custom':
            return null;
        default:
            return 0;
    }
}

// ==================== TASK MODAL FUNCTIONS ====================

function openTaskModal(taskId = null) {
    const modal = document.getElementById('task-modal');
    const title = document.getElementById('task-modal-title');
    const form = document.getElementById('task-form');

    if (!modal) {
        console.error('Task modal not found');
        return;
    }

    if (taskId) {
        title.textContent = 'Edit Task';
        form.setAttribute('data-task-id', taskId);
        loadTaskForEditing(taskId);
    } else {
        title.textContent = 'Add New Task';
        form.reset();
        form.removeAttribute('data-task-id');
        setupRecurrenceLogic();
    }

    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

// Load task data for editing
async function loadTaskForEditing(taskId) {
    try {
        const response = await fetch(`/dashboard/tasks/${taskId}`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const task = await response.json();
        populateTaskForm(task);

    } catch (error) {
        console.error('Error loading task for editing:', error);
        showMessage('Failed to load task data. Please try again.', 'error');
        closeTaskModal();
    }
}

// Populate form with task data
function populateTaskForm(task) {
    const form = document.getElementById('task-form');

    const fields = {
        'plant_id': task.plant_id,
        'task_type': task.task_type,
        'title': task.title,
        'description': task.description || '',
        'recurrence_type': task.recurrence_type || 'none',
        'frequency_days': task.frequency_days || 0
    };

    Object.keys(fields).forEach(fieldName => {
        const field = form.querySelector(`[name="${fieldName}"]`);
        if (field) {
            field.value = fields[fieldName];
        }
    });

    setTimeout(() => {
        setupRecurrenceLogic();
    }, 100);
}

function closeTaskModal() {
    const modal = document.getElementById('task-modal');
    if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = 'auto';
    }
}

// ==================== TASK FILTER FUNCTIONS ====================

function switchTaskFilter(filterType) {
    const taskTypes = ['today', 'delayed', 'completed', 'upcoming'];
    const cardMap = {
        'delayed': 'overdue',
        'today': 'today',
        'completed': 'finished',
        'upcoming': 'upcoming'
    };

    taskTypes.forEach(task => {
        const filterElement = document.querySelector(`[data-filter="${task}"]`);
        const cardElement = document.querySelector(`.stat-card.${cardMap[task]}`);

        if (task === filterType) {
            if (filterElement) {
                filterElement.classList.remove('hidden');
                filterElement.classList.add('active');
            }
            if (cardElement) {
                cardElement.classList.add('active');
                cardElement.style.backgroundColor = '#e8f5e8';
            }
        } else {
            if (filterElement) {
                filterElement.classList.add('hidden');
                filterElement.classList.remove('active');
            }
            if (cardElement) {
                cardElement.classList.remove('active');
                cardElement.style.backgroundColor = '#ffffff';
            }
        }
    });
}

// ==================== UTILITY FUNCTIONS ====================

function showMessage(message, type) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 24px;
        border-radius: 8px;
        color: white;
        font-weight: 600;
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
        ${type === 'success' ? 'background: #27ae60;' : 'background: #e74c3c;'}
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, 3000);
}

// Add CSS for toast animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);