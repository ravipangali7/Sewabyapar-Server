/**
 * Product Variants Management
 * Handles variant types, combinations, and their details
 */

(function() {
    'use strict';

    // Variant state
    let variantState = {
        enabled: false,
        variants: [], // [{name: "Color", values: ["White", "Blue"]}]
        combinations: {} // {"White/XL": {price: 500, stock: 10, image: "", is_primary: false, discount_type: "", discount: ""}}
    };

    // Initialize on page load
    document.addEventListener('DOMContentLoaded', function() {
        initializeVariants();
    });

    function initializeVariants() {
        // Get initial data from server if editing
        const variantsDataEl = document.getElementById('variants-data');
        if (variantsDataEl) {
            try {
                const data = JSON.parse(variantsDataEl.textContent || variantsDataEl.value);
                variantState = {
                    enabled: data.enabled || false,
                    variants: data.variants || [],
                    combinations: data.combinations || {}
                };
            } catch (e) {
                console.error('Error parsing variant data:', e);
            }
        }

        // Setup toggle
        const enableToggle = document.getElementById('enable-variants-toggle');
        if (enableToggle) {
            enableToggle.checked = variantState.enabled;
            enableToggle.addEventListener('change', handleToggleChange);
            updateVariantSectionVisibility();
        }

        // Load existing variants
        if (variantState.variants.length > 0) {
            variantState.variants.forEach((variant, index) => {
                addVariantTypeUI(variant.name, variant.values, index);
            });
            generateCombinations();
        }
        
        // Update price/stock fields based on initial state
        if (variantState.enabled) {
            disablePriceStockFields(true);
            // Show variant form content if enabled
            const variantFormContent = document.getElementById('variant-form-content');
            const variantTypesSection = document.getElementById('variant-types-section');
            const variantCombinationsSection = document.getElementById('variant-combinations-section');
            const variantInfoMessage = document.getElementById('variant-info-message');
            if (variantFormContent) variantFormContent.style.display = 'block';
            if (variantTypesSection) variantTypesSection.style.display = 'block';
            if (variantCombinationsSection) variantCombinationsSection.style.display = 'block';
            if (variantInfoMessage) variantInfoMessage.style.display = 'block';
        } else {
            disablePriceStockFields(false);
        }

        // Setup form submission
        const form = document.querySelector('form[method="post"]');
        if (form) {
            form.addEventListener('submit', handleFormSubmit);
        }
    }

    function handleToggleChange(e) {
        variantState.enabled = e.target.checked;
        updateVariantSectionVisibility();
        if (!variantState.enabled) {
            // Clear variants when disabled
            variantState.variants = [];
            variantState.combinations = {};
            document.getElementById('variant-types-container').innerHTML = '';
            document.getElementById('combinations-table-body').innerHTML = '';
        } else {
            // Add default variant type when enabled
            if (variantState.variants.length === 0) {
                addVariantType();
            }
        }
    }

    function updateVariantSectionVisibility() {
        const variantSection = document.getElementById('product-variants-section');
        const variantFormContent = document.getElementById('variant-form-content');
        const variantTypesSection = document.getElementById('variant-types-section');
        const variantCombinationsSection = document.getElementById('variant-combinations-section');
        const variantInfoMessage = document.getElementById('variant-info-message');
        
        if (variantSection) {
            // Card is always visible, only show/hide form content
            if (variantState.enabled) {
                // Show variant form content
                if (variantFormContent) variantFormContent.style.display = 'block';
                if (variantTypesSection) variantTypesSection.style.display = 'block';
                if (variantCombinationsSection) variantCombinationsSection.style.display = 'block';
                if (variantInfoMessage) variantInfoMessage.style.display = 'block';
                
                // Remove disabled attribute from inputs when visible (only variant section inputs)
                const inputs = variantSection.querySelectorAll('input, select, textarea');
                inputs.forEach(input => {
                    // Don't disable the toggle itself
                    if (input.id !== 'enable-variants-toggle') {
                        input.disabled = false;
                    }
                });
                // Disable price and stock fields when variants enabled
                disablePriceStockFields(true);
            } else {
                // Hide variant form content (but keep card visible)
                if (variantFormContent) variantFormContent.style.display = 'none';
                if (variantTypesSection) variantTypesSection.style.display = 'none';
                if (variantCombinationsSection) variantCombinationsSection.style.display = 'none';
                if (variantInfoMessage) variantInfoMessage.style.display = 'none';
                
                // Disable inputs when hidden to prevent validation (only variant section inputs)
                const inputs = variantSection.querySelectorAll('input, select, textarea');
                inputs.forEach(input => {
                    // Don't disable the toggle itself
                    if (input.id !== 'enable-variants-toggle') {
                        input.disabled = true;
                        input.removeAttribute('required');
                    }
                });
                // Enable price and stock fields when variants disabled
                disablePriceStockFields(false);
            }
        }
    }

    function disablePriceStockFields(disable) {
        const priceField = document.getElementById('id_price');
        const stockField = document.getElementById('id_stock_quantity');
        const priceInfo = document.getElementById('price-stock-info');
        
        if (priceField) {
            priceField.disabled = disable;
            if (disable) {
                // Gray out when disabled (matching app's Colors.grey.shade100)
                priceField.classList.add('bg-light');
                priceField.style.cursor = 'not-allowed';
                priceField.removeAttribute('required');
                // Remove any validation classes
                priceField.classList.remove('is-invalid', 'is-valid');
            } else {
                // White background when enabled (matching app's Colors.white)
                priceField.classList.remove('bg-light');
                priceField.style.cursor = 'text';
                priceField.setAttribute('required', 'required');
            }
        }
        
        if (stockField) {
            stockField.disabled = disable;
            if (disable) {
                // Gray out when disabled (matching app's Colors.grey.shade100)
                stockField.classList.add('bg-light');
                stockField.style.cursor = 'not-allowed';
                stockField.removeAttribute('required');
                // Remove any validation classes
                stockField.classList.remove('is-invalid', 'is-valid');
            } else {
                // White background when enabled (matching app's Colors.white)
                stockField.classList.remove('bg-light');
                stockField.style.cursor = 'text';
                stockField.setAttribute('required', 'required');
            }
        }
        
        // Show/hide info message (matching app's blue info box)
        if (priceInfo) {
            priceInfo.style.display = disable ? 'block' : 'none';
        }
    }

    function addVariantType(name = '', values = [], index = null) {
        if (index === null) {
            index = variantState.variants.length;
            variantState.variants.push({ name: name, values: values });
        } else {
            variantState.variants[index] = { name: name, values: values };
        }
        addVariantTypeUI(name, values, index);
        generateCombinations();
    }

    function addVariantTypeUI(name, values, index) {
        const container = document.getElementById('variant-types-container');
        if (!container) return;

        const variantDiv = document.createElement('div');
        variantDiv.className = 'variant-type-item mb-3 p-3 border rounded';
        variantDiv.dataset.index = index;

        const valuesDisplay = values.length > 0 ? values.map(v => 
            `<span class="badge bg-primary rounded-pill me-2 mb-2 px-3 py-1" style="font-size: 0.875rem; cursor: default;">
                ${escapeHtml(v)}
            </span>`
        ).join('') : '';

        variantDiv.innerHTML = `
            <div class="card border shadow-sm">
                <div class="card-body">
                    <div class="row align-items-end">
                        <div class="col-md-4">
                            <label class="form-label fw-bold">Variant Name *</label>
                            <input type="text" class="form-control variant-name" 
                                   name="variant_name_${index}"
                                   value="${escapeHtml(name)}" 
                                   placeholder="e.g., Color, Size">
                        </div>
                        <div class="col-md-6">
                            <label class="form-label fw-bold">Variant Values *</label>
                            <input type="text" class="form-control variant-values" 
                                   name="variant_values_${index}"
                                   value="${escapeHtml(values.join(', '))}" 
                                   placeholder="Enter values separated by commas (e.g., Red, Blue, Green)">
                            <small class="form-text text-muted d-block mt-1">
                                <i class="align-middle" data-feather="info" style="width: 14px; height: 14px;"></i>
                                Enter values separated by commas.
                            </small>
                            <div class="variant-values-display mt-3">${valuesDisplay}</div>
                        </div>
                        <div class="col-md-2 d-flex align-items-end">
                            <button type="button" class="btn btn-danger btn-sm w-100 remove-variant" 
                                    ${variantState.variants.length <= 1 ? 'disabled' : ''}>
                                <i class="align-middle" data-feather="trash-2" style="width: 14px; height: 14px;"></i>
                                Remove
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Reinitialize feather icons for new content
        if (typeof feather !== 'undefined') {
            feather.replace();
        }

        // Update container
        const existing = container.querySelector(`[data-index="${index}"]`);
        if (existing) {
            existing.replaceWith(variantDiv);
        } else {
            container.appendChild(variantDiv);
        }

        // Setup event listeners
        const nameInput = variantDiv.querySelector('.variant-name');
        const valuesInput = variantDiv.querySelector('.variant-values');
        const removeBtn = variantDiv.querySelector('.remove-variant');

        // Set disabled state based on variant enabled status
        nameInput.disabled = !variantState.enabled;
        valuesInput.disabled = !variantState.enabled;

        nameInput.addEventListener('input', function() {
            updateVariantFromUI(index);
        });

        valuesInput.addEventListener('input', function() {
            updateVariantFromUI(index);
            updateVariantValuesDisplay(variantDiv, valuesInput.value);
        });

        removeBtn.addEventListener('click', function() {
            removeVariantType(index);
        });
    }

    function updateVariantValuesDisplay(container, valuesStr) {
        const displayDiv = container.querySelector('.variant-values-display');
        if (!displayDiv) return;

        const values = parseVariantValues(valuesStr);
        if (values.length === 0) {
            displayDiv.innerHTML = '';
            return;
        }
        
        displayDiv.innerHTML = values.map(v => 
            `<span class="badge bg-primary rounded-pill me-2 mb-2 px-3 py-1" style="font-size: 0.875rem; cursor: default;">
                ${escapeHtml(v)}
            </span>`
        ).join('');
    }

    function updateVariantFromUI(index) {
        const container = document.querySelector(`[data-index="${index}"]`);
        if (!container) return;

        const name = container.querySelector('.variant-name').value.trim();
        const valuesStr = container.querySelector('.variant-values').value;
        const values = parseVariantValues(valuesStr);

        if (name && values.length > 0) {
            variantState.variants[index] = { name: name, values: values };
            generateCombinations();
        }
    }

    function parseVariantValues(valuesStr) {
        return valuesStr.split(',')
            .map(v => v.trim())
            .filter(v => v.length > 0);
    }

    function removeVariantType(index) {
        variantState.variants.splice(index, 1);
        const container = document.getElementById('variant-types-container');
        const variantDiv = container.querySelector(`[data-index="${index}"]`);
        if (variantDiv) {
            variantDiv.remove();
        }
        
        // Re-index remaining variants
        const remaining = container.querySelectorAll('.variant-type-item');
        remaining.forEach((div, newIndex) => {
            div.dataset.index = newIndex;
            const nameInput = div.querySelector('.variant-name');
            const valuesInput = div.querySelector('.variant-values');
            if (nameInput && valuesInput) {
                const name = nameInput.value.trim();
                const valuesStr = valuesInput.value;
                const values = parseVariantValues(valuesStr);
                variantState.variants[newIndex] = { name: name, values: values };
            }
        });

        generateCombinations();
    }

    function generateCombinations() {
        if (variantState.variants.length === 0) {
            variantState.combinations = {};
            renderCombinationsTable();
            return;
        }

        // Generate all combinations
        const combinations = generateAllCombinations(variantState.variants);
        const newCombinations = {};

        combinations.forEach(combo => {
            const key = combo.join('/');
            // Preserve existing data if available
            if (variantState.combinations[key]) {
                newCombinations[key] = { ...variantState.combinations[key] };
            } else {
                newCombinations[key] = {
                    price: '',
                    stock: '',
                    image: '',
                    is_primary: false,
                    discount_type: '',
                    discount: ''
                };
            }
        });

        variantState.combinations = newCombinations;
        renderCombinationsTable();
    }

    function generateAllCombinations(variants) {
        if (variants.length === 0) return [];
        if (variants.length === 1) {
            return variants[0].values.map(v => [v]);
        }

        const [first, ...rest] = variants;
        const restCombinations = generateAllCombinations(rest);
        const combinations = [];

        first.values.forEach(value => {
            if (restCombinations.length === 0) {
                combinations.push([value]);
            } else {
                restCombinations.forEach(restCombo => {
                    combinations.push([value, ...restCombo]);
                });
            }
        });

        return combinations;
    }

    function renderCombinationsTable() {
        const tbody = document.getElementById('combinations-table-body');
        if (!tbody) return;

        tbody.innerHTML = '';

        const combinations = Object.keys(variantState.combinations).sort();
        
        if (combinations.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No combinations available. Add variant types above.</td></tr>';
            return;
        }
        
        // Find primary combination if any
        let primaryKey = null;
        for (const key in variantState.combinations) {
            if (variantState.combinations[key].is_primary) {
                primaryKey = key;
                break;
            }
        }
        
        // If no primary set and combinations exist, set first as primary
        if (!primaryKey && combinations.length > 0) {
            primaryKey = combinations[0]; // combinations[0] is already a string key, not an array
            if (variantState.combinations[primaryKey]) {
                variantState.combinations[primaryKey].is_primary = true;
            }
        }

        combinations.forEach(comboKey => {
            const combo = variantState.combinations[comboKey];
            const row = document.createElement('tr');
            row.dataset.combination = comboKey;

            const imagePreview = combo.image ? 
                `<img src="${escapeHtml(combo.image)}" class="combination-image-preview img-thumbnail me-2" style="max-width: 60px; max-height: 60px; border-radius: 4px; object-fit: cover;">` : 
                '';
            
            const isPrimary = combo.is_primary || false;
            const primaryChecked = isPrimary ? 'checked' : '';
            
            const discountType = combo.discount_type || '';
            const discountValue = combo.discount || '';

            row.innerHTML = `
                <td><strong>${escapeHtml(comboKey)}</strong></td>
                <td>
                    <input type="number" class="form-control form-control-sm combination-price" 
                           value="${escapeHtml(combo.price || '')}" 
                           placeholder="0.00" step="0.01" min="0">
                </td>
                <td>
                    <input type="number" class="form-control form-control-sm combination-stock" 
                           value="${escapeHtml(combo.stock || '')}" 
                           placeholder="0" min="0">
                </td>
                <td class="text-center">
                    <input type="radio" class="form-check-input combination-primary" 
                           name="primary_combination" 
                           value="${escapeHtml(comboKey)}"
                           ${primaryChecked}>
                </td>
                <td>
                    <select class="form-select form-select-sm combination-discount-type">
                        <option value="">---------</option>
                        <option value="flat" ${discountType === 'flat' ? 'selected' : ''}>Flat</option>
                        <option value="percentage" ${discountType === 'percentage' ? 'selected' : ''}>Percentage</option>
                    </select>
                </td>
                <td>
                    <input type="number" class="form-control form-control-sm combination-discount" 
                           value="${escapeHtml(discountValue)}" 
                           placeholder="0" step="0.01" min="0">
                </td>
                <td>
                    <div class="d-flex align-items-center gap-2">
                        ${imagePreview}
                        <button type="button" class="btn btn-sm btn-outline-secondary combination-image-btn" 
                                style="min-width: 100px;">
                            ${combo.image ? 'Change Image' : 'Add Image'}
                        </button>
                        <input type="file" class="d-none combination-image" 
                               accept="image/*">
                        <input type="hidden" class="combination-image-url" value="${escapeHtml(combo.image || '')}">
                    </div>
                </td>
            `;

            tbody.appendChild(row);

            // Setup event listeners
            const priceInput = row.querySelector('.combination-price');
            const stockInput = row.querySelector('.combination-stock');
            const discountTypeSelect = row.querySelector('.combination-discount-type');
            const discountInput = row.querySelector('.combination-discount');
            const imageBtn = row.querySelector('.combination-image-btn');
            const imageInput = row.querySelector('.combination-image');
            const imageUrlInput = row.querySelector('.combination-image-url');

            priceInput.addEventListener('input', function() {
                variantState.combinations[comboKey].price = this.value;
            });

            stockInput.addEventListener('input', function() {
                variantState.combinations[comboKey].stock = this.value;
            });

            discountTypeSelect.addEventListener('change', function() {
                variantState.combinations[comboKey].discount_type = this.value;
            });

            discountInput.addEventListener('input', function() {
                variantState.combinations[comboKey].discount = this.value;
            });

            // Setup image button to trigger file input
            imageBtn.addEventListener('click', function() {
                imageInput.click();
            });

            imageInput.addEventListener('change', function(e) {
                handleImageUpload(e.target, comboKey, imageUrlInput, row, imageBtn);
            });
            
            // Setup primary radio button handler
            const primaryRadio = row.querySelector('.combination-primary');
            primaryRadio.addEventListener('change', function() {
                if (this.checked) {
                    // Unset all other primary flags
                    Object.keys(variantState.combinations).forEach(key => {
                        variantState.combinations[key].is_primary = false;
                    });
                    // Set this one as primary
                    variantState.combinations[comboKey].is_primary = true;
                }
            });
        });
    }

    function handleImageUpload(input, comboKey, imageUrlInput, row, imageBtn) {
        const file = input.files[0];
        if (!file) return;

        // Create FormData for upload
        const formData = new FormData();
        formData.append('image', file);
        formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);

        // Show loading
        const existingPreview = row.querySelector('.combination-image-preview');
        const preview = existingPreview || document.createElement('img');
        preview.className = 'combination-image-preview img-thumbnail me-2';
        preview.style.cssText = 'max-width: 60px; max-height: 60px; border-radius: 4px; object-fit: cover;';
        preview.src = '';
        preview.alt = 'Loading...';
        
        if (!existingPreview && imageBtn) {
            imageBtn.textContent = 'Uploading...';
            imageBtn.disabled = true;
        }

        // Get upload URL from page
        const uploadUrlEl = document.getElementById('variant-upload-url');
        const uploadUrl = uploadUrlEl ? uploadUrlEl.textContent.trim() : '/myadmin/ecommerce/upload-variant-image/';
        
        // Upload image
        fetch(uploadUrl, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.url) {
                imageUrlInput.value = data.url;
                variantState.combinations[comboKey].image = data.url;
                preview.src = data.url;
                preview.alt = comboKey;
                
                // Update button text and enable
                if (imageBtn) {
                    imageBtn.textContent = 'Change Image';
                    imageBtn.disabled = false;
                }
                
                // Insert preview if not exists
                const existingPreview = row.querySelector('.combination-image-preview');
                if (existingPreview && existingPreview !== preview) {
                    existingPreview.replaceWith(preview);
                } else if (!existingPreview) {
                    const imageContainer = imageBtn.parentElement;
                    imageContainer.insertBefore(preview, imageBtn);
                }
                preview.classList.add('combination-image-preview');
            } else {
                if (imageBtn) {
                    imageBtn.textContent = 'Add Image';
                    imageBtn.disabled = false;
                }
                alert('Failed to upload image: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error uploading image:', error);
            if (imageBtn) {
                imageBtn.textContent = 'Add Image';
                imageBtn.disabled = false;
            }
            alert('Error uploading image. Please try again.');
        });
    }

    function handleFormSubmit(e) {
        // If variants are enabled, validate variant inputs and skip price/stock validation
        if (variantState.enabled) {
            // Ensure price and stock are not required when variants enabled
            const priceField = document.getElementById('id_price');
            const stockField = document.getElementById('id_stock_quantity');
            if (priceField) {
                priceField.removeAttribute('required');
                priceField.removeAttribute('aria-required');
            }
            if (stockField) {
                stockField.removeAttribute('required');
                stockField.removeAttribute('aria-required');
            }
            
            const containers = document.querySelectorAll('.variant-type-item');
            let isValid = true;
            
            containers.forEach((container, index) => {
                const nameInput = container.querySelector('.variant-name');
                const valuesInput = container.querySelector('.variant-values');
                
                // Remove previous validation styling
                nameInput.classList.remove('is-invalid');
                valuesInput.classList.remove('is-invalid');
                
                const name = nameInput.value.trim();
                const valuesStr = valuesInput.value.trim();
                const values = parseVariantValues(valuesStr);
                
                // Validate
                if (!name) {
                    nameInput.classList.add('is-invalid');
                    isValid = false;
                }
                
                if (!valuesStr || values.length === 0) {
                    valuesInput.classList.add('is-invalid');
                    isValid = false;
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                alert('Please fill in all required variant fields.');
                return false;
            }
        } else {
            // When variants disabled, ensure price and stock are required
            const priceField = document.getElementById('id_price');
            const stockField = document.getElementById('id_stock_quantity');
            if (priceField && !priceField.disabled) {
                priceField.setAttribute('required', 'required');
            }
            if (stockField && !stockField.disabled) {
                stockField.setAttribute('required', 'required');
            }
        }
        
        // Update variant state from UI before submission
        updateAllVariantsFromUI();
        updateAllCombinationsFromUI();

        // Create hidden input with variant data
        let hiddenInput = document.getElementById('variants-json-input');
        if (!hiddenInput) {
            hiddenInput = document.createElement('input');
            hiddenInput.type = 'hidden';
            hiddenInput.id = 'variants-json-input';
            hiddenInput.name = 'variants_json';
            e.target.appendChild(hiddenInput);
        }

        hiddenInput.value = JSON.stringify(variantState);
    }

    function updateAllVariantsFromUI() {
        const containers = document.querySelectorAll('.variant-type-item');
        containers.forEach((container, index) => {
            const name = container.querySelector('.variant-name').value.trim();
            const valuesStr = container.querySelector('.variant-values').value;
            const values = parseVariantValues(valuesStr);
            
            if (name && values.length > 0) {
                variantState.variants[index] = { name: name, values: values };
            }
        });
    }

    function updateAllCombinationsFromUI() {
        const rows = document.querySelectorAll('#combinations-table-body tr[data-combination]');
        rows.forEach(row => {
            const comboKey = row.dataset.combination;
            const priceInput = row.querySelector('.combination-price');
            const stockInput = row.querySelector('.combination-stock');
            const discountTypeSelect = row.querySelector('.combination-discount-type');
            const discountInput = row.querySelector('.combination-discount');
            const imageUrlInput = row.querySelector('.combination-image-url');
            const primaryRadio = row.querySelector('.combination-primary');

            if (variantState.combinations[comboKey]) {
                variantState.combinations[comboKey].price = priceInput ? priceInput.value : '';
                variantState.combinations[comboKey].stock = stockInput ? stockInput.value : '';
                variantState.combinations[comboKey].discount_type = discountTypeSelect ? discountTypeSelect.value : '';
                variantState.combinations[comboKey].discount = discountInput ? discountInput.value : '';
                variantState.combinations[comboKey].image = imageUrlInput ? imageUrlInput.value : '';
                variantState.combinations[comboKey].is_primary = primaryRadio ? primaryRadio.checked : false;
            }
        });
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Expose add variant button handler
    window.addVariantType = function() {
        if (!variantState.enabled) {
            document.getElementById('enable-variants-toggle').checked = true;
            handleToggleChange({ target: document.getElementById('enable-variants-toggle') });
        }
        addVariantType();
    };

})();
