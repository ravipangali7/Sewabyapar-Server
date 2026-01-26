/**
 * Travel Vehicle Seat Layout Visualization
 * Real-time rendering of bus seat layout based on formset data
 */

(function() {
    'use strict';

    const SEAT_STATUS_COLORS = {
        'available': 'success',  // Green
        'booked': 'warning',     // Yellow
        'boarded': 'danger'      // Red
    };

    /**
     * Get formset prefix dynamically
     */
    function getFormsetPrefix() {
        const formsContainer = document.getElementById('travelvehicleseat_set-forms');
        if (formsContainer) {
            return 'travelvehicleseat_set';
        }
        // Fallback: try to find any seat formset
        const seatForms = document.querySelectorAll('[id$="-forms"]');
        for (let i = 0; i < seatForms.length; i++) {
            const id = seatForms[i].id;
            if (id.includes('seat')) {
                return id.replace('-forms', '');
            }
        }
        return 'travelvehicleseat_set';
    }

    /**
     * Extract seat data from formset
     */
    function getSeatsFromFormset() {
        const seats = [];
        const prefix = getFormsetPrefix();
        const formRows = document.querySelectorAll('#' + prefix + '-forms .form-row');
        
        formRows.forEach(function(row) {
            const deleteCheckbox = row.querySelector('input[name*="-DELETE"]');
            if (deleteCheckbox && deleteCheckbox.checked) {
                return; // Skip deleted seats
            }
            
            const sideSelect = row.querySelector('select[name*="-side"]');
            const numberInput = row.querySelector('input[name*="-number"]');
            const statusSelect = row.querySelector('select[name*="-status"]');
            const floorSelect = row.querySelector('select[name*="-floor"]');
            const priceInput = row.querySelector('input[name*="-price"]');
            
            if (sideSelect && numberInput && statusSelect && floorSelect) {
                const side = sideSelect.value;
                const number = numberInput.value;
                const status = statusSelect.value || 'available';
                const floor = floorSelect.value;
                const price = priceInput ? parseFloat(priceInput.value) || 0 : 0;
                
                if (side && number) {
                    seats.push({
                        side: side,
                        number: parseInt(number),
                        status: status,
                        floor: floor,
                        price: price,
                        id: side + number + floor
                    });
                }
            }
        });
        
        return seats;
    }

    /**
     * Group seats by side and floor
     */
    function groupSeatsBySideAndFloor(seats) {
        const grouped = {};
        
        seats.forEach(function(seat) {
            const key = seat.floor + '_' + seat.side;
            if (!grouped[key]) {
                grouped[key] = [];
            }
            grouped[key].push(seat);
        });
        
        // Sort seats by number within each group
        Object.keys(grouped).forEach(function(key) {
            grouped[key].sort(function(a, b) {
                return a.number - b.number;
            });
        });
        
        return grouped;
    }

    /**
     * Get maximum seat number for a side/floor combination
     */
    function getMaxSeatNumber(seats, side, floor) {
        const filtered = seats.filter(function(seat) {
            return seat.side === side && seat.floor === floor;
        });
        if (filtered.length === 0) return 0;
        return Math.max.apply(Math, filtered.map(function(seat) { return seat.number; }));
    }

    /**
     * Render seat layout
     */
    function renderSeatLayout() {
        const container = document.getElementById('seat-layout-container');
        if (!container) return;
        
        const seats = getSeatsFromFormset();
        
        if (seats.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted py-5">
                    <i class="align-middle" data-feather="grid" style="width: 48px; height: 48px;"></i>
                    <p class="mt-2 mb-0">Add seats to see layout</p>
                </div>
            `;
            if (typeof feather !== 'undefined') {
                feather.replace();
            }
            return;
        }
        
        const grouped = groupSeatsBySideAndFloor(seats);
        const floors = ['upper', 'lower'];
        const sides = ['A', 'B', 'C'];
        
        let html = '';
        
        floors.forEach(function(floor) {
            const floorSeats = {};
            sides.forEach(function(side) {
                const key = floor + '_' + side;
                floorSeats[side] = grouped[key] || [];
            });
            
            // Check if this floor has any seats
            const hasSeats = sides.some(function(side) {
                return floorSeats[side].length > 0;
            });
            
            if (hasSeats) {
                html += `<div class="mb-4"><h6 class="mb-2 text-capitalize">${floor} Floor</h6>`;
                html += '<div class="d-flex gap-3 justify-content-center">';
                
                sides.forEach(function(side) {
                    const sideSeats = floorSeats[side];
                    if (sideSeats.length > 0) {
                        html += `<div class="seat-column"><div class="text-center mb-2"><strong>Side ${side}</strong></div>`;
                        html += '<div class="d-flex flex-column gap-2">';
                        
                        // Get max number to create grid
                        const maxNumber = getMaxSeatNumber(seats, side, floor);
                        const seatMap = {};
                        sideSeats.forEach(function(seat) {
                            seatMap[seat.number] = seat;
                        });
                        
                        // Render seats in grid (2 columns)
                        for (let i = 1; i <= maxNumber; i++) {
                            const seat = seatMap[i];
                            if (seat) {
                                const statusColor = SEAT_STATUS_COLORS[seat.status] || 'secondary';
                                html += `
                                    <div class="seat-box badge bg-${statusColor}" 
                                         style="width: 50px; height: 40px; display: flex; align-items: center; justify-content: center; cursor: pointer;"
                                         title="Seat ${seat.side}${seat.number} - ${seat.status} - ₹${seat.price.toFixed(2)}">
                                        ${seat.side}${seat.number}
                                    </div>
                                `;
                            } else {
                                // Empty slot
                                html += '<div style="width: 50px; height: 40px;"></div>';
                            }
                        }
                        
                        html += '</div></div>';
                    }
                });
                
                html += '</div></div>';
            }
        });
        
        if (html === '') {
            html = `
                <div class="text-center text-muted py-5">
                    <i class="align-middle" data-feather="grid" style="width: 48px; height: 48px;"></i>
                    <p class="mt-2 mb-0">Add seats to see layout</p>
                </div>
            `;
        }
        
        container.innerHTML = html;
        
        // Reinitialize feather icons
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }

    /**
     * Initialize seat layout visualization
     */
    function initSeatLayout() {
        const formsetPrefix = getFormsetPrefix();
        const formsContainer = document.getElementById(formsetPrefix + '-forms');
        const addButton = document.getElementById('add-' + formsetPrefix + '-row');
        
        if (!formsContainer) return;
        
        // Render initial layout
        renderSeatLayout();
        
        // Listen for formset changes (add/delete)
        if (addButton) {
            const originalClick = addButton.onclick;
            addButton.addEventListener('click', function() {
                setTimeout(function() {
                    renderSeatLayout();
                }, 200);
            });
        }
        
        // Also listen for inline_forms.js events by overriding addStackedForm if available
        if (typeof window.addStackedForm === 'function') {
            const originalAddStacked = window.addStackedForm;
            window.addStackedForm = function(prefix) {
                const result = originalAddStacked(prefix);
                if (prefix === formsetPrefix) {
                    setTimeout(function() {
                        renderSeatLayout();
                    }, 200);
                }
                return result;
            };
        }
        
        // Listen for field changes in existing forms
        formsContainer.addEventListener('change', function(e) {
            if (e.target.matches('select[name*="-side"], select[name*="-status"], select[name*="-floor"], input[name*="-number"], input[name*="-price"]')) {
                renderSeatLayout();
            }
        });
        
        formsContainer.addEventListener('input', function(e) {
            if (e.target.matches('input[name*="-number"], input[name*="-price"]')) {
                renderSeatLayout();
            }
        });
        
        // Listen for delete checkbox changes
        formsContainer.addEventListener('change', function(e) {
            if (e.target.matches('input[name*="-DELETE"]')) {
                renderSeatLayout();
            }
        });
        
        // Use MutationObserver to detect when forms are added/removed
        const observer = new MutationObserver(function(mutations) {
            let shouldUpdate = false;
            mutations.forEach(function(mutation) {
                if (mutation.addedNodes.length > 0 || mutation.removedNodes.length > 0) {
                    shouldUpdate = true;
                }
            });
            if (shouldUpdate) {
                setTimeout(function() {
                    renderSeatLayout();
                }, 100);
            }
        });
        
        observer.observe(formsContainer, {
            childList: true,
            subtree: true
        });
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(initSeatLayout, 100);
        });
    } else {
        setTimeout(initSeatLayout, 100);
    }
    
    // Also initialize after inline_forms.js adds rows
    window.addEventListener('load', function() {
        setTimeout(initSeatLayout, 500);
    });
    
    // Expose render function globally for inline_forms.js to call
    window.renderSeatLayout = renderSeatLayout;

})();
