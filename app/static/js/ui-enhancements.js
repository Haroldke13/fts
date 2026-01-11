/**
 * Enhanced UI Utilities for FTS
 * Provides common functions for better user experience and accessibility
 */

// Enhanced form validation with visual feedback
function validateForm(form) {
    const inputs = form.querySelectorAll('input, select, textarea');
    let isValid = true;

    inputs.forEach(input => {
        if (input.hasAttribute('required') && !input.value.trim()) {
            showFieldError(input, 'This field is required');
            isValid = false;
        } else if (input.type === 'email' && input.value && !isValidEmail(input.value)) {
            showFieldError(input, 'Please enter a valid email address');
            isValid = false;
        } else {
            clearFieldError(input);
        }
    });

    return isValid;
}

function showFieldError(input, message) {
    clearFieldError(input);

    input.classList.add('is-invalid');
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback d-block';
    errorDiv.textContent = message;

    input.parentNode.appendChild(errorDiv);
    input.focus();
}

function clearFieldError(input) {
    input.classList.remove('is-invalid');
    const errorDiv = input.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Enhanced table sorting and filtering
function makeTableSortable(tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;

    const headers = table.querySelectorAll('th[data-sort]');
    headers.forEach(header => {
        header.style.cursor = 'pointer';
        header.addEventListener('click', function() {
            const column = this.dataset.sort;
            const order = this.dataset.order === 'asc' ? 'desc' : 'asc';
            this.dataset.order = order;

            // Update sort indicators
            headers.forEach(h => h.querySelector('.sort-indicator')?.remove());
            const indicator = document.createElement('i');
            indicator.className = `fas fa-sort-${order === 'asc' ? 'up' : 'down'} sort-indicator ms-1`;
            this.appendChild(indicator);

            sortTable(table, column, order);
        });
    });
}

function sortTable(table, column, order) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));

    rows.sort((a, b) => {
        const aVal = a.querySelector(`td[data-${column}]`)?.textContent || '';
        const bVal = b.querySelector(`td[data-${column}]`)?.textContent || '';

        if (order === 'asc') {
            return aVal.localeCompare(bVal);
        } else {
            return bVal.localeCompare(aVal);
        }
    });

    rows.forEach(row => tbody.appendChild(row));
}

// Enhanced search functionality
function makeTableSearchable(tableId, searchInputId) {
    const table = document.getElementById(tableId);
    const searchInput = document.getElementById(searchInputId);

    if (!table || !searchInput) return;

    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const rows = table.querySelectorAll('tbody tr');

        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            const shouldShow = text.includes(searchTerm);
            row.style.display = shouldShow ? '' : 'none';
        });

        // Show "no results" message if needed
        let noResultsRow = table.querySelector('.no-results');
        if (!noResultsRow) {
            noResultsRow = document.createElement('tr');
            noResultsRow.className = 'no-results';
            noResultsRow.innerHTML = `<td colspan="${table.querySelector('thead th').length}" class="text-center py-4 text-muted">No results found</td>`;
            table.querySelector('tbody').appendChild(noResultsRow);
        }
        noResultsRow.style.display = Array.from(rows).some(row => row.style.display !== 'none') ? 'none' : '';
    });
}

// Enhanced pagination
function createPagination(containerId, currentPage, totalPages, onPageChange) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = '';

    if (totalPages <= 1) return;

    const pagination = document.createElement('nav');
    pagination.setAttribute('aria-label', 'Page navigation');

    const ul = document.createElement('ul');
    ul.className = 'pagination justify-content-center';

    // Previous button
    const prevLi = document.createElement('li');
    prevLi.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
    prevLi.innerHTML = `<a class="page-link" href="#" aria-label="Previous"><i class="fas fa-chevron-left"></i></a>`;
    if (currentPage > 1) {
        prevLi.querySelector('a').addEventListener('click', (e) => {
            e.preventDefault();
            onPageChange(currentPage - 1);
        });
    }
    ul.appendChild(prevLi);

    // Page numbers
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);

    if (startPage > 1) {
        const firstLi = document.createElement('li');
        firstLi.className = 'page-item';
        firstLi.innerHTML = '<a class="page-link" href="#">1</a>';
        firstLi.querySelector('a').addEventListener('click', (e) => {
            e.preventDefault();
            onPageChange(1);
        });
        ul.appendChild(firstLi);

        if (startPage > 2) {
            const ellipsisLi = document.createElement('li');
            ellipsisLi.className = 'page-item disabled';
            ellipsisLi.innerHTML = '<span class="page-link">...</span>';
            ul.appendChild(ellipsisLi);
        }
    }

    for (let i = startPage; i <= endPage; i++) {
        const pageLi = document.createElement('li');
        pageLi.className = `page-item ${i === currentPage ? 'active' : ''}`;
        pageLi.innerHTML = `<a class="page-link" href="#">${i}</a>`;
        pageLi.querySelector('a').addEventListener('click', (e) => {
            e.preventDefault();
            onPageChange(i);
        });
        ul.appendChild(pageLi);
    }

    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            const ellipsisLi = document.createElement('li');
            ellipsisLi.className = 'page-item disabled';
            ellipsisLi.innerHTML = '<span class="page-link">...</span>';
            ul.appendChild(ellipsisLi);
        }

        const lastLi = document.createElement('li');
        lastLi.className = 'page-item';
        lastLi.innerHTML = `<a class="page-link" href="#">${totalPages}</a>`;
        lastLi.querySelector('a').addEventListener('click', (e) => {
            e.preventDefault();
            onPageChange(totalPages);
        });
        ul.appendChild(lastLi);
    }

    // Next button
    const nextLi = document.createElement('li');
    nextLi.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
    nextLi.innerHTML = `<a class="page-link" href="#" aria-label="Next"><i class="fas fa-chevron-right"></i></a>`;
    if (currentPage < totalPages) {
        nextLi.querySelector('a').addEventListener('click', (e) => {
            e.preventDefault();
            onPageChange(currentPage + 1);
        });
    }
    ul.appendChild(nextLi);

    pagination.appendChild(ul);
    container.appendChild(pagination);
}

// Enhanced modal management
function createModal(options = {}) {
    const {
        id = 'dynamicModal',
        title = 'Modal Title',
        content = '',
        size = 'md',
        buttons = []
    } = options;

    // Remove existing modal if it exists
    const existingModal = document.getElementById(id);
    if (existingModal) {
        existingModal.remove();
    }

    const modal = document.createElement('div');
    modal.className = `modal fade`;
    modal.id = id;
    modal.setAttribute('tabindex', '-1');
    modal.setAttribute('aria-labelledby', `${id}Label`);
    modal.setAttribute('aria-hidden', 'true');

    modal.innerHTML = `
        <div class="modal-dialog modal-${size}">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="${id}Label">${title}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
                <div class="modal-footer">
                    ${buttons.map(btn => `
                        <button type="button" class="btn btn-${btn.type || 'secondary'}" ${btn.id ? `id="${btn.id}"` : ''}>
                            ${btn.text}
                        </button>
                    `).join('')}
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    // Add event listeners to buttons
    buttons.forEach((btn, index) => {
        if (btn.onClick) {
            const buttonEl = modal.querySelector(`.modal-footer button:nth-child(${index + 1})`);
            buttonEl.addEventListener('click', btn.onClick);
        }
    });

    return modal;
}

// Enhanced confirmation dialog
function confirmAction(message, options = {}) {
    const {
        title = 'Confirm Action',
        confirmText = 'Confirm',
        cancelText = 'Cancel',
        confirmType = 'primary',
        onConfirm,
        onCancel
    } = options;

    const modal = createModal({
        id: 'confirmModal',
        title,
        content: `<p class="mb-0">${message}</p>`,
        buttons: [
            {
                text: cancelText,
                type: 'secondary',
                onClick: function() {
                    const bsModal = bootstrap.Modal.getInstance(modal);
                    bsModal.hide();
                    if (onCancel) onCancel();
                }
            },
            {
                text: confirmText,
                type: confirmType,
                onClick: function() {
                    const bsModal = bootstrap.Modal.getInstance(modal);
                    bsModal.hide();
                    if (onConfirm) onConfirm();
                }
            }
        ]
    });

    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();

    return modal;
}

// Enhanced file upload preview
function createFilePreview(input, options = {}) {
    const {
        maxSize = 5 * 1024 * 1024, // 5MB
        allowedTypes = ['image/jpeg', 'image/png', 'image/gif'],
        previewContainer,
        onSuccess,
        onError
    } = options;

    input.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (!file) return;

        // Validate file size
        if (file.size > maxSize) {
            if (onError) onError('File size too large');
            showNotification('File size too large. Maximum size is 5MB.', 'error');
            return;
        }

        // Validate file type
        if (!allowedTypes.includes(file.type)) {
            if (onError) onError('Invalid file type');
            showNotification('Invalid file type. Please select an image file.', 'error');
            return;
        }

        // Create preview
        if (previewContainer && file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = function(e) {
                previewContainer.innerHTML = `
                    <div class="text-center">
                        <img src="${e.target.result}" class="img-fluid rounded" style="max-height: 200px;" alt="Preview">
                        <p class="mt-2 mb-0 text-muted small">${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)</p>
                    </div>
                `;
            };
            reader.readAsDataURL(file);
        }

        if (onSuccess) onSuccess(file);
    });
}

// Utility function to format file sizes
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Utility function to debounce function calls
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Utility function to throttle function calls
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Export functions to global scope
window.validateForm = validateForm;
window.makeTableSortable = makeTableSortable;
window.makeTableSearchable = makeTableSearchable;
window.createPagination = createPagination;
window.createModal = createModal;
window.confirmAction = confirmAction;
window.createFilePreview = createFilePreview;
window.formatFileSize = formatFileSize;
window.debounce = debounce;
window.throttle = throttle;