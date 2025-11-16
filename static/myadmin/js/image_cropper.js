/**
 * Image Cropper Module for Product Images
 * Provides optional image cropping with 4:3 aspect ratio
 */

(function() {
    'use strict';

    // Configuration
    const ASPECT_RATIO = 4 / 3; // 4:3 aspect ratio
    const DEFAULT_WIDTH = 1200;
    const DEFAULT_HEIGHT = 900;

    // Initialize cropper for a file input
    function initImageCropper(fileInput) {
        if (!fileInput || fileInput.type !== 'file') {
            return;
        }

        // Check if this is a product image input
        // Matches: 'image' (standalone form) or 'images-X-image' (formset with related_name='images')
        const name = fileInput.name || '';
        const isImageInput = name === 'image' || 
            (name.startsWith('images-') && name.endsWith('-image'));

        if (!isImageInput) {
            return;
        }

        // Skip if already initialized
        if (fileInput.dataset.cropperInitialized === 'true') {
            return;
        }

        fileInput.dataset.cropperInitialized = 'true';
        console.log('Image cropper initialized for:', name);

        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (!file) {
                return;
            }
            
            // Check if we're currently processing a crop (to prevent reopening)
            if (fileInput.dataset.processingCrop === 'true') {
                fileInput.dataset.processingCrop = 'false';
                return;
            }
            
            if (!file.type.startsWith('image/')) {
                console.log('File is not an image:', file.type);
                return;
            }

            console.log('Image selected, showing crop modal');
            // Show crop modal
            showCropModal(file, fileInput);
        });
    }

    // Show crop modal with cropper using SweetAlert2
    function showCropModal(file, fileInput) {
        // Check if dependencies are available
        if (typeof Cropper === 'undefined') {
            console.error('Cropper.js is not loaded');
            return;
        }
        
        if (typeof Swal === 'undefined') {
            console.error('SweetAlert2 is not loaded');
            // Load SweetAlert2 if not available
            loadSweetAlert2().then(function() {
                addCropperStyles();
                showCropModal(file, fileInput);
            });
            return;
        }

        // Add styles if not already added
        addCropperStyles();

        let cropper = null;

        // Read file first
        const reader = new FileReader();
        reader.onload = function(e) {
            const imageUrl = e.target.result;
            
            // Create HTML content for SweetAlert2
            const htmlContent = `
                <div class="row">
                    <div class="col-md-8">
                        <div id="cropImageContainer" style="max-width: 100%; max-height: 500px; overflow: hidden; position: relative; background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px; padding: 10px;">
                            <img id="cropImage" src="${imageUrl}" style="max-width: 100%; display: block;">
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div id="cropPreview" style="min-height: 150px; margin-bottom: 15px;"></div>
                        <div>
                            <small class="text-muted">
                                <strong>Instructions:</strong><br>
                                • Adjust the crop area to your desired selection<br>
                                • The crop maintains a 4:3 aspect ratio<br>
                                • Click "Apply Crop" to use the cropped image<br>
                                • Click "Skip" to use the original image
                            </small>
                        </div>
                    </div>
                </div>
            `;

            // Show SweetAlert2 modal
            Swal.fire({
                title: 'Crop Product Image (4:3 Ratio)',
                html: htmlContent,
                width: '90%',
                maxWidth: '900px',
                showCancelButton: true,
                showConfirmButton: true,
                confirmButtonText: 'Apply Crop',
                cancelButtonText: 'Skip',
                confirmButtonColor: '#3085d6',
                cancelButtonColor: '#6c757d',
                allowOutsideClick: false,
                allowEscapeKey: true,
                scrollbarPadding: false,
                heightAuto: true,
                didOpen: function() {
                    // Initialize cropper after modal is opened
                    const imgElement = document.querySelector('#cropImage');
                    const previewElement = document.querySelector('#cropPreview');
                    
                    if (imgElement) {
                        // Small delay to ensure image is loaded
                        setTimeout(function() {
                            cropper = new Cropper(imgElement, {
                                aspectRatio: ASPECT_RATIO,
                                viewMode: 1,
                                dragMode: 'move',
                                autoCropArea: 0.8,
                                restore: false,
                                guides: true,
                                center: true,
                                highlight: false,
                                cropBoxMovable: true,
                                cropBoxResizable: true,
                                toggleDragModeOnDblclick: false,
                                responsive: true,
                                minContainerWidth: 300,
                                minContainerHeight: 300,
                                ready: function() {
                                    // Show preview when cropper is ready
                                    updatePreview(cropper, previewElement);
                                },
                                crop: function() {
                                    // Update preview on crop
                                    updatePreview(cropper, previewElement);
                                }
                            });
                        }, 100);
                    }
                },
                preConfirm: function() {
                    // Apply crop button clicked
                    if (!cropper) {
                        Swal.showValidationMessage('Cropper not initialized');
                        return false;
                    }

                    return new Promise(function(resolve) {
                        const canvas = cropper.getCroppedCanvas({
                            width: DEFAULT_WIDTH,
                            height: DEFAULT_HEIGHT,
                            imageSmoothingEnabled: true,
                            imageSmoothingQuality: 'high',
                        });

                        canvas.toBlob(function(blob) {
                            if (!blob) {
                                Swal.showValidationMessage('Failed to crop image');
                                resolve(false);
                                return;
                            }

                            // Create a new File object from the blob
                            const croppedFile = new File([blob], file.name, {
                                type: file.type,
                                lastModified: Date.now()
                            });

                            // Clean up cropper first
                            if (cropper) {
                                cropper.destroy();
                                cropper = null;
                            }

                            // Set flag to prevent modal from reopening when we set the file
                            fileInput.dataset.processingCrop = 'true';
                            
                            // Create a new DataTransfer object and add the file
                            const dataTransfer = new DataTransfer();
                            dataTransfer.items.add(croppedFile);
                            fileInput.files = dataTransfer.files;

                            // Resolve to close the modal
                            // The flag will prevent the change event from reopening the modal
                            resolve(true);
                        }, file.type, 0.95);
                    });
                },
                didClose: function() {
                    // Clean up when modal closes
                    if (cropper) {
                        cropper.destroy();
                        cropper = null;
                    }
                    // Clear the processing flag
                    fileInput.dataset.processingCrop = 'false';
                }
            }).then(function(result) {
                // Handle result (Skip button or outside click)
                if (result && result.dismiss === Swal.DismissReason.cancel) {
                    // Skip was clicked - do nothing, keep original file
                    if (cropper) {
                        cropper.destroy();
                        cropper = null;
                    }
                    // Clear the processing flag
                    fileInput.dataset.processingCrop = 'false';
                } else if (result && result.value === true) {
                    // Crop was applied successfully - flag already cleared in preConfirm
                    // Just ensure it's cleared
                    fileInput.dataset.processingCrop = 'false';
                }
            });
        };
        reader.readAsDataURL(file);
    }

    // Load SweetAlert2 dynamically if not available
    function loadSweetAlert2() {
        return new Promise(function(resolve, reject) {
            if (typeof Swal !== 'undefined') {
                resolve();
                return;
            }

            // Load CSS
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = 'https://cdn.jsdelivr.net/npm/sweetalert2@11/dist/sweetalert2.min.css';
            document.head.appendChild(link);

            // Load JS
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/sweetalert2@11/dist/sweetalert2.min.js';
            script.onload = function() {
                resolve();
            };
            script.onerror = function() {
                reject(new Error('Failed to load SweetAlert2'));
            };
            document.head.appendChild(script);
        });
    }

    // Add custom CSS for cropper in SweetAlert2
    function addCropperStyles() {
        if (!document.getElementById('cropperSweetAlertStyles')) {
            const style = document.createElement('style');
            style.id = 'cropperSweetAlertStyles';
            style.textContent = `
                /* Ensure cropper works well in SweetAlert2 */
                .swal2-popup #cropImageContainer {
                    max-width: 100%;
                    max-height: 500px;
                    overflow: hidden;
                    position: relative;
                }
                .swal2-popup #cropImageContainer .cropper-container {
                    max-width: 100% !important;
                }
                .swal2-popup .row {
                    margin: 0;
                }
                .swal2-popup .col-md-8,
                .swal2-popup .col-md-4 {
                    padding: 0 10px;
                }
                /* Ensure SweetAlert2 doesn't disable scroll */
                body.swal2-shown {
                    overflow: auto !important;
                }
                body.swal2-height-auto {
                    height: auto !important;
                }
            `;
            document.head.appendChild(style);
        }
    }

    // Update preview
    function updatePreview(cropper, previewElement) {
        if (!cropper || !previewElement) {
            return;
        }

        const canvas = cropper.getCroppedCanvas({
            width: 200,
            height: 150,
        });

        if (canvas) {
            previewElement.innerHTML = '<p class="mb-2"><strong>Preview:</strong></p><img src="' + canvas.toDataURL() + '" style="max-width: 200px; max-height: 150px; border: 1px solid #ddd; border-radius: 4px;">';
        }
    }


    // Initialize all image inputs on page load
    function initAllImageCroppers() {
        // Wait for dependencies (only need Cropper.js, SweetAlert2 will load dynamically)
        if (typeof Cropper === 'undefined') {
            // Retry after a short delay
            setTimeout(initAllImageCroppers, 100);
            return;
        }

        console.log('Initializing image croppers...');
        
        // Find all product image inputs
        // Standalone form: name="image"
        // Formset: name="images-0-image", "images-1-image", etc. (related_name='images')
        const allFileInputs = document.querySelectorAll('input[type="file"]');
        console.log('Found', allFileInputs.length, 'file inputs');
        
        let productImageCount = 0;
        allFileInputs.forEach(function(input) {
            const name = input.name || '';
            console.log('Checking file input:', name);
            
            // Check if it's a product image field
            // Standalone form: name="image"
            // Formset: name starts with "images-" and ends with "-image"
            const isProductImage = 
                name === 'image' || // Standalone form
                (name.startsWith('images-') && name.endsWith('-image')); // Formset with related_name='images'
            
            if (isProductImage) {
                productImageCount++;
                console.log('Initializing cropper for:', name);
                initImageCropper(input);
            }
        });
        
        console.log('Initialized', productImageCount, 'product image croppers');
    }

    // Wait for all dependencies and DOM
    function waitForDependencies() {
        if (typeof Cropper !== 'undefined') {
            // Wait for DOM to be fully ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', function() {
                    // Small delay to ensure all formsets are rendered
                    setTimeout(initAllImageCroppers, 200);
                });
            } else {
                // DOM already loaded, but wait a bit for formsets
                setTimeout(initAllImageCroppers, 200);
            }
        } else {
            setTimeout(waitForDependencies, 100);
        }
    }

    // Start waiting for dependencies
    waitForDependencies();
    
    // Also re-initialize when page is fully loaded (for dynamically loaded content)
    window.addEventListener('load', function() {
        setTimeout(initAllImageCroppers, 300);
    });

    // Export function for dynamic initialization (for formsets)
    window.initImageCropper = initImageCropper;
    window.initAllImageCroppers = initAllImageCroppers;

})();

