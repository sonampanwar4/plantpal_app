// Photo Gallery JavaScript functionality

document.addEventListener('DOMContentLoaded', function() {
    // Get modal elements
    const modal = document.getElementById('diagnosisModal');
    const modalContent = document.getElementById('diagnosisContent');
    const closeBtn = modal.querySelector('.close');
    const loadingOverlay = document.getElementById('loadingOverlay');

    // Close modal functionality
    closeBtn.addEventListener('click', function() {
        modal.style.display = 'none';
    });

    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });

    // View diagnosis functionality
    document.querySelectorAll('.view-diagnosis').forEach(button => {
        button.addEventListener('click', function() {
            const diagnosisJson = this.getAttribute('data-diagnosis');
            viewDiagnosis(diagnosisJson);
        });
    });

    // Delete photo functionality
    document.querySelectorAll('.delete-photo').forEach(button => {
        button.addEventListener('click', function() {
            const photoId = this.getAttribute('data-photo-id');
            deletePhoto(photoId);
        });
    });

    // Functions
    function showLoading() {
        loadingOverlay.style.display = 'flex';
    }

    function hideLoading() {
        loadingOverlay.style.display = 'none';
    }

    function showModal(content) {
        modalContent.innerHTML = content;
        modal.style.display = 'block';
    }

    function formatDate(dateString) {
        // Format date to: 5 Jan 2026, 2:36:40 PM
        const date = new Date(dateString);
        const options = {
            day: 'numeric',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        };
        return date.toLocaleDateString('en-US', options);
    }

    function viewDiagnosis(diagnosisJson) {
        try {
            const diagnosis = JSON.parse(diagnosisJson);
            let content = `
                <h2><i class="fas fa-microscope"></i> Plant Diagnosis Report</h2>
                <div class="diagnosis-details">
                    <div class="confidence-section">
                        <h4>Analysis Confidence</h4>
                        <div class="confidence-bar">
                            <div class="confidence-fill" style="width: ${(diagnosis.confidence_score || 0) * 100}%"></div>
                        </div>
                        <p>${((diagnosis.confidence_score || 0) * 100).toFixed(1)}% confidence</p>
                    </div>
            `;

            // Add identified issues
            if (diagnosis.identified_issues) {
                content += '<div class="issues-section"><h4>Issues Identified</h4>';
                for (const [category, issues] of Object.entries(diagnosis.identified_issues)) {
                    if (issues && issues.length > 0) {
                        content += `
                            <div class="issue-category">
                                <h5>${category.replace('_', ' ').toUpperCase()}</h5>
                                <ul>
                                    ${issues.map(issue => `<li>${issue}</li>`).join('')}
                                </ul>
                            </div>
                        `;
                    }
                }
                content += '</div>';
                
            }
            
            // Add recommended actions
            if (diagnosis.recommended_actions && typeof diagnosis.recommended_actions === 'object') {
                console.log('Recommended actions:', diagnosis.recommended_actions);
                content += '<div class="actions-section"><h4>Recommended Actions</h4>';
                for (const [category, actions] of Object.entries(diagnosis.recommended_actions)) {
                    // Handle both string and array values
                    let actionItems = '';
                    if (Array.isArray(actions) && actions.length > 0) {
                        actionItems = actions.map(action => `<li>${String(action).replace(/</g, '&lt;').replace(/>/g, '&gt;')}</li>`).join('');
                    } else if (typeof actions === 'string' && actions.trim()) {
                        actionItems = `<li>${String(actions).replace(/</g, '&lt;').replace(/>/g, '&gt;')}</li>`;
                    }
                    
                    if (actionItems) {
                        content += `
                            <div class="action-category">
                                <h5>${String(category).replace(/_/g, ' ').toUpperCase()}</h5>
                                <ul>
                                    ${actionItems}
                                </ul>
                            </div>
                        `;
                    }
                }
                content += '</div>';
            }

            // Add full diagnosis text
            // Add full diagnosis text
            if (diagnosis.diagnosis_text) {
                content += `
                    <div class="diagnosis-text-section">
                        <h4>Full Analysis</h4>
                        <div class="diagnosis-text">${String(diagnosis.diagnosis_text).replace(/</g, '&lt;').replace(/>/g, '&gt;')}</div>
                    </div>
                `;
            }

            // Add diagnosis metadata
            content += `
                <div class="diagnosis-meta">
                    ${diagnosis.treatment_outcome ? `<p><strong>Treatment Outcome:</strong> ${String(diagnosis.treatment_outcome).replace(/_/g, ' ')}</p>` : ''}
                    <p><strong>Analysis Date:</strong> ${formatDate(diagnosis.created_at)}</p>
                </div>
            </div>
            `;
            
            showModal(content);
        } catch (error) {
            console.error('Error parsing diagnosis:', error);
            showModal(`
                <h2><i class="fas fa-exclamation-triangle"></i> Error</h2>
                <p>Failed to load diagnosis data.</p>
            `);
        }
    }
    function analyzePhoto(photoId) {
        showLoading();

        const formData = new FormData();
        formData.append('user_message', 'Please provide a detailed analysis of this plant photo');

        fetch(`/analyze_photo/${photoId}`, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();

            if (data.success) {
                showModal(`
                    <h2><i class="fas fa-check-circle"></i> Analysis Complete</h2>
                    <div class="analysis-result">
                        ${data.analysis}
                    </div>
                    <div class="modal-actions">
                        <button onclick="location.reload()" class="btn btn-primary">
                            <i class="fas fa-refresh"></i> Refresh Gallery
                        </button>

                    </div>
                `);
            } else {
                showModal(`
                    <h2><i class="fas fa-exclamation-triangle"></i> Analysis Failed</h2>
                    <p>${data.error || 'Unknown error occurred'}</p>
                    <button onclick="analyzePhoto(${photoId})" class="btn btn-primary">
                        <i class="fas fa-redo"></i> Try Again
                    </button>
                `);
            }
        })
        .catch(error => {
            hideLoading();
            console.error('Error analyzing photo:', error);
            showModal(`
                <h2>Error</h2>
                <p>Failed to analyze photo. Please try again.</p>
                <button onclick="analyzePhoto(${photoId})" class="btn btn-primary">
                    <i class="fas fa-redo"></i> Try Again
                </button>
            `);
        });
    }


    function deletePhoto(photoId) {
        if (confirm('Are you sure you want to delete this photo? This action cannot be undone.')) {
            showLoading();

            fetch(`/delete_photo/${photoId}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                hideLoading();

                if (data.success) {
                    // Remove the photo card from the gallery
                    const photoCard = document.querySelector(`[data-photo-id="${photoId}"]`);
                    if (photoCard) {
                        photoCard.style.opacity = '0';
                        setTimeout(() => {
                            photoCard.remove();

                            // Check if gallery is now empty
                            const remainingPhotos = document.querySelectorAll('.photo-card');
                            if (remainingPhotos.length === 0) {
                                location.reload(); // Reload to show empty state
                            }
                        }, 300);
                    }

                    showNotification('Photo deleted successfully', 'success');
                } else {
                    showNotification(data.error || 'Failed to delete photo', 'error');
                }
            })
            .catch(error => {
                hideLoading();
                console.error('Error deleting photo:', error);
                showNotification('Failed to delete photo', 'error');
            });
        }
    }

    function showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            ${message}
        `;

        // Add to page
        document.body.appendChild(notification);

        // Show notification
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);

        // Hide and remove notification
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }

    // Make functions globally available for onclick handlers
    window.analyzePhoto = analyzePhoto;
    window.deletePhoto = deletePhoto;
    window.viewDiagnosis = viewDiagnosis;
});