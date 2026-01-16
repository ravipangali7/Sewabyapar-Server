/**
 * Dynamic inline formset management
 * Handles add/remove functionality for inline formsets
 */

(function() {
    'use strict';

    function updateFormsetTotal(formsetPrefix) {
        const totalFormsInput = document.getElementById(`id_${formsetPrefix}-TOTAL_FORMS`);
        const formRows = document.querySelectorAll(`#${formsetPrefix}-tbody .form-row, #${formsetPrefix}-forms .form-row`);
        if (totalFormsInput) {
            totalFormsInput.value = formRows.length;
        }
    }

    function getFormsetEmptyForm(formsetPrefix) {
        const emptyFormHtml = document.getElementById(`${formsetPrefix}-empty-form`);
        if (emptyFormHtml) {
            return emptyFormHtml.innerHTML;
        }
        return null;
    }

    function addTabularRow(formsetPrefix) {
        const tbody = document.getElementById(`${formsetPrefix}-tbody`);
        if (!tbody) return;

        const totalFormsInput = document.getElementById(`id_${formsetPrefix}-TOTAL_FORMS`);
        const formCount = totalFormsInput ? parseInt(totalFormsInput.value) : 0;

        // Get the last form row as template (or first if none)
        const templateRow = tbody.querySelector('.form-row:last-child') || tbody.querySelector('.form-row');
        if (!templateRow) return;

        // Clone the template row
        const newRow = templateRow.cloneNode(true);
        newRow.classList.remove('d-none');
        
        // Update form indices
        newRow.setAttribute('data-form-index', formCount);
        newRow.querySelectorAll('input, select, textarea, label').forEach(function(element) {
            if (element.name) {
                // Replace the form index in the name attribute
                const nameMatch = element.name.match(new RegExp(`^${formsetPrefix}-(\\d+)-`));
                if (nameMatch) {
                    element.name = element.name.replace(/-\d+-/, `-${formCount}-`);
                }
            }
            if (element.id) {
                const idMatch = element.id.match(new RegExp(`^id_${formsetPrefix}-(\\d+)-`));
                if (idMatch) {
                    element.id = element.id.replace(/-\d+-/, `-${formCount}-`);
                }
            }
            if (element.getAttribute && element.getAttribute('for')) {
                const forAttr = element.getAttribute('for');
                const forMatch = forAttr.match(new RegExp(`^id_${formsetPrefix}-(\\d+)-`));
                if (forMatch) {
                    element.setAttribute('for', forAttr.replace(/-\d+-/, `-${formCount}-`));
                }
            }
            
            // Clear values for new row
            if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                if (element.type !== 'checkbox' && element.type !== 'hidden' && element.type !== 'button') {
                    element.value = '';
                } else if (element.type === 'checkbox' && !element.name.includes('DELETE')) {
                    element.checked = false;
                }
            } else if (element.tagName === 'SELECT') {
                element.selectedIndex = 0;
            }
        });

        tbody.appendChild(newRow);
        updateFormsetTotal(formsetPrefix);

        // Initialize Feather icons for new row
        if (typeof feather !== 'undefined') {
            feather.replace();
        }

        // Initialize image cropper for new image inputs (if cropper is available)
        if (typeof window.initImageCropper === 'function') {
            const imageInputs = newRow.querySelectorAll('input[type="file"][name*="image"]');
            imageInputs.forEach(function(input) {
                window.initImageCropper(input);
            });
        }

        // Setup primary image selection for new rows (if images formset)
        if (formsetPrefix === 'images' && typeof window.setupPrimaryImageSelection === 'function') {
            window.setupPrimaryImageSelection();
        }
    }

    function addStackedForm(formsetPrefix) {
        const formsContainer = document.getElementById(`${formsetPrefix}-forms`);
        if (!formsContainer) return;

        const totalFormsInput = document.getElementById(`id_${formsetPrefix}-TOTAL_FORMS`);
        const formCount = totalFormsInput ? parseInt(totalFormsInput.value) : 0;

        // Get the last form as template (or first if none)
        const templateForm = formsContainer.querySelector('.form-row:last-child') || formsContainer.querySelector('.form-row');
        if (!templateForm) return;

        // Clone the template form
        const newForm = templateForm.cloneNode(true);
        newForm.classList.remove('d-none');
        
        // Update form indices
        newForm.setAttribute('data-form-index', formCount);
        const h6 = newForm.querySelector('h6');
        if (h6) {
            h6.textContent = `Item #${formCount + 1}`;
        }
        
        newForm.querySelectorAll('input, select, textarea, label').forEach(function(element) {
            if (element.name) {
                const nameMatch = element.name.match(new RegExp(`^${formsetPrefix}-(\\d+)-`));
                if (nameMatch) {
                    element.name = element.name.replace(/-\d+-/, `-${formCount}-`);
                }
            }
            if (element.id) {
                const idMatch = element.id.match(new RegExp(`^id_${formsetPrefix}-(\\d+)-`));
                if (idMatch) {
                    element.id = element.id.replace(/-\d+-/, `-${formCount}-`);
                }
            }
            if (element.getAttribute && element.getAttribute('for')) {
                const forAttr = element.getAttribute('for');
                const forMatch = forAttr.match(new RegExp(`^id_${formsetPrefix}-(\\d+)-`));
                if (forMatch) {
                    element.setAttribute('for', forAttr.replace(/-\d+-/, `-${formCount}-`));
                }
            }
            
            // Clear values for new form
            if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                if (element.type !== 'checkbox' && element.type !== 'hidden' && element.type !== 'button') {
                    element.value = '';
                } else if (element.type === 'checkbox' && !element.name.includes('DELETE')) {
                    element.checked = false;
                }
            } else if (element.tagName === 'SELECT') {
                element.selectedIndex = 0;
            }
        });

        formsContainer.appendChild(newForm);
        updateFormsetTotal(formsetPrefix);

        // Initialize Feather icons for new form
        if (typeof feather !== 'undefined') {
            feather.replace();
        }

        // Initialize image cropper for new image inputs (if cropper is available)
        if (typeof window.initImageCropper === 'function') {
            const imageInputs = newForm.querySelectorAll('input[type="file"][name*="image"]');
            imageInputs.forEach(function(input) {
                window.initImageCropper(input);
            });
        }
    }

    function removeRow(button) {
        const row = button.closest('.form-row');
        if (row) {
            const deleteCheckbox = row.querySelector('input[name*="-DELETE"]');
            if (deleteCheckbox) {
                deleteCheckbox.checked = true;
                row.style.display = 'none';
            } else {
                row.remove();
                updateFormsetTotal(row.closest('[id$="-tbody"], [id$="-forms"]').id.replace(/-tbody|-forms$/, ''));
            }
        }
    }

    // Initialize on page load
    document.addEventListener('DOMContentLoaded', function() {
        // Handle tabular formsets
        document.querySelectorAll('[id$="-tbody"]').forEach(function(tbody) {
            const formsetPrefix = tbody.id.replace('-tbody', '');
            const addButton = document.getElementById(`add-${formsetPrefix}-row`);
            if (addButton) {
                addButton.addEventListener('click', function() {
                    addTabularRow(formsetPrefix);
                });
            }
        });

        // Handle stacked formsets
        document.querySelectorAll('[id$="-forms"]').forEach(function(formsContainer) {
            const formsetPrefix = formsContainer.id.replace('-forms', '');
            const addButton = document.getElementById(`add-${formsetPrefix}-row`);
            if (addButton) {
                addButton.addEventListener('click', function() {
                    addStackedForm(formsetPrefix);
                });
            }
        });

        // Handle delete checkboxes
        document.querySelectorAll('input[name*="-DELETE"]').forEach(function(checkbox) {
            checkbox.addEventListener('change', function() {
                const row = this.closest('.form-row');
                if (row && this.checked) {
                    row.style.opacity = '0.5';
                } else if (row) {
                    row.style.opacity = '1';
                }
            });
        });

        // Calculate totals for OrderItem formsets
        document.querySelectorAll('#orderitem_set-tbody input[name*="-quantity"], #orderitem_set-tbody input[name*="-price"]').forEach(function(input) {
            input.addEventListener('input', function() {
                const row = this.closest('.form-row');
                if (row) {
                    const quantityInput = row.querySelector('input[name*="-quantity"]');
                    const priceInput = row.querySelector('input[name*="-price"]');
                    const totalInput = row.querySelector('input[name*="-total"]');
                    
                    if (quantityInput && priceInput && totalInput) {
                        const quantity = parseFloat(quantityInput.value) || 0;
                        const price = parseFloat(priceInput.value) || 0;
                        totalInput.value = (quantity * price).toFixed(2);
                    }
                }
            });
        });

        // Handle primary image selection for product images
        setupPrimaryImageSelection();
    });

    function setupPrimaryImageSelection() {
        const imagesFormset = document.getElementById('images-tbody');
        if (!imagesFormset) return;

        // Handle primary checkbox changes
        const primaryCheckboxes = imagesFormset.querySelectorAll('input[name*="-is_primary"]');
        primaryCheckboxes.forEach(function(checkbox) {
            checkbox.addEventListener('change', function() {
                if (this.checked) {
                    // Uncheck all other primary checkboxes
                    primaryCheckboxes.forEach(function(otherCheckbox) {
                        if (otherCheckbox !== checkbox) {
                            otherCheckbox.checked = false;
                            updatePrimaryBadge(otherCheckbox, false);
                        }
                    });
                    // Add primary badge to this row
                    updatePrimaryBadge(checkbox, true);
                } else {
                    // Remove primary badge
                    updatePrimaryBadge(checkbox, false);
                }
            });

            // Initialize badge state
            updatePrimaryBadge(checkbox, checkbox.checked);
        });

        // Handle image preview clicks to set primary
        const imagePreviews = imagesFormset.querySelectorAll('.product-image-preview');
        imagePreviews.forEach(function(preview) {
            preview.addEventListener('click', function() {
                const formIndex = this.getAttribute('data-form-index');
                const primaryCheckbox = imagesFormset.querySelector(`input[name="images-${formIndex}-is_primary"]`);
                if (primaryCheckbox) {
                    primaryCheckbox.checked = true;
                    primaryCheckbox.dispatchEvent(new Event('change'));
                }
            });
        });
    }

    function updatePrimaryBadge(checkbox, isPrimary) {
        const row = checkbox.closest('.form-row');
        if (!row) return;

        // Remove existing badge
        const existingBadge = row.querySelector('.primary-image-badge');
        if (existingBadge) {
            existingBadge.remove();
        }

        // Add badge if primary
        if (isPrimary) {
            const imagePreview = row.querySelector('.product-image-preview');
            if (imagePreview) {
                const badge = document.createElement('span');
                badge.className = 'badge bg-primary position-absolute top-0 start-0 m-1 primary-image-badge';
                badge.style.cssText = 'font-size: 0.7rem; z-index: 10;';
                badge.textContent = 'Primary';
                
                const parent = imagePreview.parentElement;
                if (parent && !parent.classList.contains('position-relative')) {
                    parent.classList.add('position-relative', 'd-inline-block');
                }
                parent.appendChild(badge);
            }
        }
    }

    // Expose function for dynamically added rows
    window.setupPrimaryImageSelection = setupPrimaryImageSelection;
})();

