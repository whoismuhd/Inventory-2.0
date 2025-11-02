// Istrom Inventory Management System - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Tab persistence
    const currentPath = window.location.pathname;
    const tabMap = {
        '/manual_entry': 'manual_entry',
        '/inventory': 'inventory',
        '/make_request': 'make_request',
        '/review_history': 'review_history',
        '/budget_summary': 'budget_summary',
        '/actuals': 'actuals',
        '/admin_settings': 'admin_settings',
        '/notifications': 'notifications'
    };
    
    const currentTab = tabMap[currentPath] || 'manual_entry';
    sessionStorage.setItem('currentTab', currentTab);
    
    // Highlight active tab
    document.querySelectorAll('.nav-link').forEach(link => {
        const tab = link.getAttribute('data-tab');
        if (tab === currentTab || link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
    
    // Sidebar toggle functionality
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
            // Adjust toggle button position based on sidebar state
            if (sidebar.classList.contains('show')) {
                sidebarToggle.style.left = '260px';
            } else {
                sidebarToggle.style.left = '0.75rem';
            }
        });
    }
    
    // Start with sidebar hidden by default
    if (sidebar) {
        sidebar.classList.remove('show');
    }
    
    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        document.querySelectorAll('.alert').forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Real-time line amount calculation
    const qtyInput = document.getElementById('manual_qty_input');
    const rateInput = document.getElementById('manual_rate_input');
    const lineAmountDisplay = document.getElementById('line_amount_display');
    
    if (qtyInput && rateInput && lineAmountDisplay) {
        function updateLineAmount() {
            const qty = parseFloat(qtyInput.value) || 0;
            const rate = parseFloat(rateInput.value) || 0;
            const amount = qty * rate;
            lineAmountDisplay.textContent = `Line Amount: ₦${amount.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
        }
        
        qtyInput.addEventListener('input', updateLineAmount);
        rateInput.addEventListener('input', updateLineAmount);
        updateLineAmount();
    }
    
    // Budget filtering based on building type
    const buildingTypeSelect = document.getElementById('building_type_select');
    const budgetSelect = document.getElementById('budget_selectbox');
    
    if (buildingTypeSelect && budgetSelect) {
        buildingTypeSelect.addEventListener('change', function() {
            const buildingType = this.value;
            if (buildingType) {
                // Reload page with building type filter
                const url = new URL(window.location.href);
                url.searchParams.set('building_type', buildingType);
                window.location.href = url.toString();
            }
        });
    }
    
    // Real-time notification checking (for admins and users)
    checkServerNotifications();
    // Check every 5 seconds for real-time updates
    setInterval(checkServerNotifications, 5000);
    
    // Also check localStorage notifications (for backwards compatibility)
    checkLocalStorageNotifications();
    
    // Initialize theme
    initTheme();
    
    // Initialize tab scrolling
    initTabScrolling();
    
    // Initialize session monitoring for tab detection
    initSessionMonitoring();
});

// Tab Scrolling Functionality
function initTabScrolling() {
    const tabsContainer = document.getElementById('tabsContainer');
    const scrollLeftBtn = document.getElementById('tabScrollLeft');
    const scrollRightBtn = document.getElementById('tabScrollRight');
    
    if (!tabsContainer || !scrollLeftBtn || !scrollRightBtn) return;
    
    // Update scroll button visibility
    function updateScrollButtons() {
        const isScrollable = tabsContainer.scrollWidth > tabsContainer.clientWidth;
        const canScrollLeft = tabsContainer.scrollLeft > 0;
        const canScrollRight = tabsContainer.scrollLeft < (tabsContainer.scrollWidth - tabsContainer.clientWidth - 10);
        
        scrollLeftBtn.classList.toggle('hidden', !isScrollable || !canScrollLeft);
        scrollRightBtn.classList.toggle('hidden', !isScrollable || !canScrollRight);
    }
    
    // Scroll functions
    function scrollTabs(direction) {
        const scrollAmount = 200;
        const currentScroll = tabsContainer.scrollLeft;
        const newScroll = direction === 'left' 
            ? currentScroll - scrollAmount 
            : currentScroll + scrollAmount;
        
        tabsContainer.scrollTo({
            left: newScroll,
            behavior: 'smooth'
        });
    }
    
    // Event listeners
    scrollLeftBtn.addEventListener('click', () => scrollTabs('left'));
    scrollRightBtn.addEventListener('click', () => scrollTabs('right'));
    
    // Update on scroll
    tabsContainer.addEventListener('scroll', updateScrollButtons);
    
    // Update on resize
    window.addEventListener('resize', updateScrollButtons);
    
    // Initial update
    updateScrollButtons();
    
    // Update after a short delay to ensure layout is complete
    setTimeout(updateScrollButtons, 100);
}

// Theme Toggle Functionality
function initTheme() {
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = document.getElementById('themeIcon');
    
    // Get saved theme or default to light
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);
    
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            setTheme(newTheme);
            localStorage.setItem('theme', newTheme);
        });
    }
}

function setTheme(theme) {
    const themeIcon = document.getElementById('themeIcon');
    
    if (theme === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
        if (themeIcon) {
            themeIcon.className = 'bi bi-sun-fill';
        }
    } else {
        document.documentElement.setAttribute('data-theme', 'light');
        if (themeIcon) {
            themeIcon.className = 'bi bi-moon-fill';
        }
    }
}

// Real-time notification system - checks server for new notifications
const seenNotificationIds = new Set();
let notificationCheckInterval = null;

function checkServerNotifications() {
    fetch('/api/check_notifications')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch notifications');
            }
            return response.json();
        })
        .then(data => {
            if (data.notifications && data.notifications.length > 0) {
                data.notifications.forEach(notif => {
                    // Only show popups for specific notification types:
                    // - 'request' (admin gets popup when project site makes request)
                    // - 'approval' (project site gets popup when request approved)
                    // - 'rejection' (project site gets popup when request rejected)
                    const shouldShowPopup = ['request', 'approval', 'rejection'].includes(notif.type);
                    
                    if (shouldShowPopup && !seenNotificationIds.has(notif.id)) {
                        seenNotificationIds.add(notif.id);
                        
                        // Determine notification type/color
                        let notifType = 'info';
                        if (notif.type === 'approval') {
                            notifType = 'success';
                        } else if (notif.type === 'rejection') {
                            notifType = 'danger';
                        } else if (notif.type === 'request') {
                            notifType = 'warning';
                        }
                        
                        // Show toast notification
                        showToast(`<strong>${notif.title}</strong><br>${notif.message}`, notifType);
                        
                        // Update notification badge if on admin settings page
                        updateNotificationBadge();
                    }
                });
            }
        })
        .catch(error => {
            // Silently fail - user might not be logged in or endpoint might not exist
            console.debug('Notification check failed:', error);
        });
}

function updateNotificationBadge() {
    // Update badge in admin settings if it exists
    const badge = document.querySelector('#adminNotifications .badge');
    if (badge) {
        fetch('/api/check_notifications')
            .then(response => response.json())
            .then(data => {
                if (badge) {
                    const count = data.count || 0;
                    if (count > 0) {
                        badge.textContent = count;
                        badge.style.display = 'inline-block';
                    } else {
                        badge.style.display = 'none';
                    }
                }
            })
            .catch(() => {});
    }
}

// Check localStorage for notifications (legacy support)
function checkLocalStorageNotifications() {
    const notificationKeys = [
        'request_approved_notification',
        'item_added_notification',
        'item_updated_notification',
        'request_submitted_notification'
    ];
    
    notificationKeys.forEach(key => {
        const notification = localStorage.getItem(key);
        if (notification) {
            try {
                const data = JSON.parse(notification);
                showToast(data.message, data.type || 'info');
                localStorage.removeItem(key);
            } catch (e) {
                localStorage.removeItem(key);
            }
        }
    });
}

function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) return;
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'info'} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Play notification sound
    playNotificationSound();
    
    // Remove toast element after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

function playNotificationSound() {
    // Create a simple beep sound (800Hz)
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    oscillator.frequency.value = 800;
    oscillator.type = 'sine';
    
    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
    
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.1);
}

// Format currency helper
function formatCurrency(amount) {
    return `₦${parseFloat(amount || 0).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
}

// Confirm delete with double-click
let deleteConfirmCount = 0;
function confirmDelete() {
    deleteConfirmCount++;
    if (deleteConfirmCount === 1) {
        alert('Click the button again to confirm deletion. This action cannot be undone!');
        setTimeout(() => {
            deleteConfirmCount = 0;
        }, 5000);
        return false;
    }
    deleteConfirmCount = 0;
    return true;
}

