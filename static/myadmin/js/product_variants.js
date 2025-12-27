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
        combinations: {} // {"White/XL": {price: 500, stock: 10, image: ""}}
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
        } else {
            // Add one empty variant type by default
            addVariantType();
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
        if (variantSection) {
            if (variantState.enabled) {
                variantSection.style.display = 'block';
                // Remove disabled attribute from inputs when visible
                const inputs = variantSection.querySelectorAll('input');
                inputs.forEach(input => {
                    input.disabled = false;
                });
            } else {
                variantSection.style.display = 'none';
                // Disable inputs when hidden to prevent validation
                const inputs = variantSection.querySelectorAll('input');
                inputs.forEach(input => {
                    input.disabled = true;
                    input.removeAttribute('required');
                });
            }
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

        const valuesDisplay = values.map(v => 
            `<span class="badge bg-primary me-1 mb-1">${escapeHtml(v)}</span>`
        ).join('');

        variantDiv.innerHTML = `
            <div class="row">
                <div class="col-md-4">
                    <label class="form-label">Variant Name *</label>
                    <input type="text" class="form-control variant-name" 
                           name="variant_name_${index}"
                           value="${escapeHtml(name)}" 
                           placeholder="e.g., Color">
                </div>
                <div class="col-md-6">
                    <label class="form-label">Variant Values *</label>
                    <input type="text" class="form-control variant-values" 
                           name="variant_values_${index}"
                           value="${escapeHtml(values.join(', '))}" 
                           placeholder="Enter values separated by commas">
                    <small class="form-text text-muted">Enter values separated by commas.</small>
                    <div class="variant-values-display mt-2">${valuesDisplay}</div>
                </div>
                <div class="col-md-2 d-flex align-items-end">
                    <button type="button" class="btn btn-danger btn-sm remove-variant" 
                            ${variantState.variants.length <= 1 ? 'disabled' : ''}>
                        Remove
                    </button>
                </div>
            </div>
        `;

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
        displayDiv.innerHTML = values.map(v => 
            `<span class="badge bg-primary me-1 mb-1">${escapeHtml(v)}</span>`
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
                    image: ''
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
            tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No combinations available. Add variant types above.</td></tr>';
            return;
        }

        combinations.forEach(comboKey => {
            const combo = variantState.combinations[comboKey];
            const row = document.createElement('tr');
            row.dataset.combination = comboKey;

            const imagePreview = combo.image ? 
                `<img src="${escapeHtml(combo.image)}" class="img-thumbnail me-2" style="max-width: 50px; max-height: 50px;">` : 
                '';

            row.innerHTML = `
                <td>${escapeHtml(comboKey)}</td>
                <td>
                    <input type="number" class="form-control form-control-sm combination-price" 
                           value="${escapeHtml(combo.price || '')}" 
                           placeholder="Price" step="0.01" min="0">
                </td>
                <td>
                    <input type="number" class="form-control form-control-sm combination-stock" 
                           value="${escapeHtml(combo.stock || '')}" 
                           placeholder="Stock" min="0">
                </td>
                <td>
                    <div class="d-flex align-items-center">
                        ${imagePreview}
                        <input type="file" class="form-control form-control-sm combination-image" 
                               accept="image/*" style="max-width: 150px;">
                        <input type="hidden" class="combination-image-url" value="${escapeHtml(combo.image || '')}">
                    </div>
                </td>
            `;

            tbody.appendChild(row);

            // Setup event listeners
            const priceInput = row.querySelector('.combination-price');
            const stockInput = row.querySelector('.combination-stock');
            const imageInput = row.querySelector('.combination-image');
            const imageUrlInput = row.querySelector('.combination-image-url');

            priceInput.addEventListener('input', function() {
                variantState.combinations[comboKey].price = this.value;
            });

            stockInput.addEventListener('input', function() {
                variantState.combinations[comboKey].stock = this.value;
            });

            imageInput.addEventListener('change', function(e) {
                handleImageUpload(e.target, comboKey, imageUrlInput, row);
            });
        });
    }

    function handleImageUpload(input, comboKey, imageUrlInput, row) {
        const file = input.files[0];
        if (!file) return;

        // Create FormData for upload
        const formData = new FormData();
        formData.append('image', file);
        formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);

        // Show loading
        const preview = row.querySelector('img') || document.createElement('img');
        preview.className = 'img-thumbnail me-2';
        preview.style.cssText = 'max-width: 50px; max-height: 50px;';
        preview.src = '';
        preview.alt = 'Loading...';

        // Upload image (you may need to adjust this endpoint)
        fetch('/admin/ecommerce/upload-variant-image/', {
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
                if (!row.querySelector('img')) {
                    imageInput.parentElement.insertBefore(preview, imageInput);
                }
            } else {
                alert('Failed to upload image: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error uploading image:', error);
            alert('Error uploading image. Please try again.');
        });
    }

    function handleFormSubmit(e) {
        // If variants are enabled, validate variant inputs
        if (variantState.enabled) {
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
            const imageUrlInput = row.querySelector('.combination-image-url');

            if (variantState.combinations[comboKey]) {
                variantState.combinations[comboKey].price = priceInput.value;
                variantState.combinations[comboKey].stock = stockInput.value;
                variantState.combinations[comboKey].image = imageUrlInput.value;
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
