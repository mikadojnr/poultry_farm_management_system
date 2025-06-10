/**
 * Main JavaScript for Poultry Farm Management System
 * Handles sidebar navigation, notifications, form interactions, and charts
 */

class FarmApp {
    constructor() {
        this.sidebar = document.getElementById('sidebar');
        this.mainContent = document.querySelector('.main-content');
        this.mobileMenuBtn = document.getElementById('mobile-menu-btn');
        this.sidebarToggle = document.getElementById('sidebar-toggle');
        this.mobileOverlay = document.getElementById('mobile-overlay');
        this.isCollapsed = false;
        this.isMobile = window.innerWidth < 768;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupNotifications();
        this.setupForms();
        this.setupCharts();
        this.setActiveNavItem();
        this.handleResize();
    }
    
    setupEventListeners() {
        // Mobile menu toggle
        this.mobileMenuBtn?.addEventListener('click', () => {
            this.toggleMobileMenu();
        });
        
        // Desktop sidebar toggle
        this.sidebarToggle?.addEventListener('click', () => {
            this.toggleSidebar();
        });
        
        // Mobile overlay click
        this.mobileOverlay?.addEventListener('click', () => {
            this.closeMobileMenu();
        });
        
        // Window resize handler
        window.addEventListener('resize', () => {
            this.handleResize();
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcuts(e);
        });
        
        // Close mobile menu on nav item click
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', () => {
                if (this.isMobile) {
                    this.closeMobileMenu();
                }
            });
        });
    }
    
    toggleSidebar() {
        if (this.isMobile) return;
        
        this.isCollapsed = !this.isCollapsed;
        
        // Toggle sidebar classes
        this.sidebar.classList.toggle('collapsed', this.isCollapsed);
        this.mainContent.classList.toggle('collapsed', this.isCollapsed);
        
        // Update main content margin
        if (this.isCollapsed) {
            this.mainContent.style.marginLeft = '4rem';
        } else {
            this.mainContent.style.marginLeft = '16rem';
        }
        
        // Save state to localStorage
        localStorage.setItem('sidebarCollapsed', this.isCollapsed);
        
        // Emit custom event for other components
        window.dispatchEvent(new CustomEvent('sidebarToggle', {
            detail: { collapsed: this.isCollapsed }
        }));
    }
    
    toggleMobileMenu() {
        const isOpen = this.sidebar.classList.contains('mobile-open');
        
        if (isOpen) {
            this.closeMobileMenu();
        } else {
            this.openMobileMenu();
        }
    }
    
    openMobileMenu() {
        this.sidebar.classList.add('mobile-open');
        this.mobileOverlay.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
        
        // Focus management for accessibility
        const firstNavItem = this.sidebar.querySelector('.nav-item');
        firstNavItem?.focus();
    }
    
    closeMobileMenu() {
        this.sidebar.classList.remove('mobile-open');
        this.mobileOverlay.classList.add('hidden');
        document.body.style.overflow = '';
        
        // Return focus to menu button
        this.mobileMenuBtn?.focus();
    }
    
    handleResize() {
        const wasMobile = this.isMobile;
        this.isMobile = window.innerWidth < 768;
        
        // If switching from mobile to desktop
        if (wasmobile && !this.isMobile) {
            this.closeMobileMenu();
            // Restore sidebar state
            const savedState = localStorage.getItem('sidebarCollapsed');
            if (savedState === 'true') {
                this.isCollapsed = true;
                this.sidebar.classList.add('collapsed');
                this.mainContent.classList.add('collapsed');
                this.mainContent.style.marginLeft = '4rem';
            }
        }
        
        // If switching from desktop to mobile
        if (!wasMinile && this.isMobile) {
            this.sidebar.classList.remove('collapsed');
            this.mainContent.classList.remove('collapsed');
            this.mainContent.style.marginLeft = '0';
        }
    }
    
    handleKeyboardShortcuts(e) {
        // Alt + M: Toggle mobile menu
        if (e.altKey && e.key === 'm' && this.isMobile) {
            e.preventDefault();
            this.toggleMobileMenu();
        }
        
        // Alt + S: Toggle sidebar (desktop)
        if (e.altKey && e.key === 's' && !this.isMobile) {
            e.preventDefault();
            this.toggleSidebar();
        }
        
        // Escape: Close mobile menu
        if (e.key === 'Escape' && this.isMobile) {
            this.closeMobileMenu();
        }
    }
    
    setActiveNavItem() {
        const currentPath = window.location.pathname;
        const navItems = document.querySelectorAll('.nav-item');
        
        navItems.forEach(item => {
            const href = item.getAttribute('href');
            if (href === currentPath || (currentPath === '/' && href.includes('dashboard'))) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }
    
    setupNotifications() {
        // Auto-show and hide notifications
        const notifications = document.querySelectorAll('.notification');
        
        notifications.forEach((notification, index) => {
            // Stagger the appearance
            setTimeout(() => {
                notification.classList.add('show');
            }, index * 200);
            
            // Auto-hide after 5 seconds
            setTimeout(() => {
                this.hideNotification(notification);
            }, 5000 + (index * 200));
        });
        
        // Manual close buttons
        document.querySelectorAll('.notification button').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const notification = e.target.closest('.notification');
                this.hideNotification(notification);
            });
        });
    }
    
    hideNotification(notification) {
        notification.classList.remove('show');
        notification.classList.add('hide');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }
    
    showNotification(message, type = 'info', duration = 5000) {
        const notificationContainer = document.querySelector('.notification-container') || 
            this.createNotificationContainer();
        
        const notification = document.createElement('div');
        notification.className = `notification px-6 py-4 rounded-lg shadow-lg ${this.getNotificationClass(type)} text-white`;
        
        notification.innerHTML = `
            <div class="flex items-center justify-between">
                <span>${message}</span>
                <button class="ml-4 text-white hover:text-gray-200 focus:outline-none">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        notificationContainer.appendChild(notification);
        
        // Show notification
        setTimeout(() => notification.classList.add('show'), 100);
        
        // Auto-hide
        setTimeout(() => this.hideNotification(notification), duration);
        
        // Manual close
        notification.querySelector('button').addEventListener('click', () => {
            this.hideNotification(notification);
        });
    }
    
    createNotificationContainer() {
        const container = document.createElement('div');
        container.className = 'notification-container fixed top-4 right-4 z-50 space-y-2';
        document.body.appendChild(container);
        return container;
    }
    
    getNotificationClass(type) {
        const classes = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            warning: 'bg-yellow-500',
            info: 'bg-blue-500'
        };
        return classes[type] || classes.info;
    }
    
    setupForms() {
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            // Add loading state on submit
            form.addEventListener('submit', (e) => {
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn && !form.dataset.noLoading) {
                    this.setButtonLoading(submitBtn, true);
                }
            });
            
            // Real-time validation
            const inputs = form.querySelectorAll('.form-input');
            inputs.forEach(input => {
                input.addEventListener('blur', () => {
                    this.validateInput(input);
                });
                
                input.addEventListener('input', () => {
                    // Clear validation errors on input
                    this.clearInputError(input);
                });
            });
        });
        
        // Auto-resize textareas
        document.querySelectorAll('textarea').forEach(textarea => {
            textarea.addEventListener('input', () => {
                this.autoResizeTextarea(textarea);
            });
        });
    }
    
    setButtonLoading(button, loading) {
        const spinner = button.querySelector('.loading-spinner');
        const text = button.querySelector('.button-text');
        
        if (loading) {
            button.classList.add('loading');
            button.disabled = true;
            if (spinner) spinner.style.display = 'inline-block';
            if (text) text.textContent = 'Processing...';
        } else {
            button.classList.remove('loading');
            button.disabled = false;
            if (spinner) spinner.style.display = 'none';
            if (text) text.textContent = text.dataset.originalText || 'Submit';
        }
    }
    
    validateInput(input) {
        const value = input.value.trim();
        const type = input.type;
        const required = input.hasAttribute('required');
        
        let isValid = true;
        let errorMessage = '';
        
        if (required && !value) {
            isValid = false;
            errorMessage = 'This field is required';
        } else if (type === 'email' && value && !this.isValidEmail(value)) {
            isValid = false;
            errorMessage = 'Please enter a valid email address';
        } else if (type === 'number' && value && isNaN(value)) {
            isValid = false;
            errorMessage = 'Please enter a valid number';
        }
        
        this.showInputValidation(input, isValid, errorMessage);
        return isValid;
    }
    
    showInputValidation(input, isValid, errorMessage) {
        const errorElement = input.parentNode.querySelector('.input-error');
        
        if (isValid) {
            input.classList.remove('border-red-500');
            input.classList.add('border-green-500');
            if (errorElement) errorElement.remove();
        } else {
            input.classList.remove('border-green-500');
            input.classList.add('border-red-500');
            
            if (!errorElement) {
                const error = document.createElement('div');
                error.className = 'input-error text-red-500 text-sm mt-1';
                error.textContent = errorMessage;
                input.parentNode.appendChild(error);
            }
        }
    }
    
    clearInputError(input) {
        input.classList.remove('border-red-500', 'border-green-500');
        const errorElement = input.parentNode.querySelector('.input-error');
        if (errorElement) errorElement.remove();
    }
    
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    
    autoResizeTextarea(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
    }
    
    setupCharts() {
        // Production Chart
        this.initProductionChart();
        
        // Mortality Chart
        this.initMortalityChart();
        
        // Listen for sidebar toggle to resize charts
        window.addEventListener('sidebarToggle', () => {
            setTimeout(() => {
                this.resizeCharts();
            }, 300);
        });
    }
    
    async initProductionChart() {
        const ctx = document.getElementById('productionChart');
        if (!ctx) return;
        
        try {
            const response = await fetch('/api/production-chart');
            const data = await response.json();
            
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.dates,
                    datasets: [
                        {
                            label: 'Eggs Collected',
                            data: data.eggs_collected,
                            borderColor: '#4CAF50',
                            backgroundColor: 'rgba(76, 175, 80, 0.1)',
                            tension: 0.4,
                            fill: true
                        },
                        {
                            label: 'Revenue (₦)',
                            data: data.revenue,
                            borderColor: '#388E3C',
                            backgroundColor: 'rgba(56, 142, 60, 0.1)',
                            tension: 0.4,
                            yAxisID: 'y1'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                        title: {
                            display: true,
                            text: 'Production & Revenue Trends'
                        }
                    },
                    scales: {
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                            title: {
                                display: true,
                                text: 'Eggs Collected'
                            }
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            title: {
                                display: true,
                                text: 'Revenue (₦)'
                            },
                            grid: {
                                drawOnChartArea: false,
                            },
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error loading production chart:', error);
        }
    }
    
    async initMortalityChart() {
        const ctx = document.getElementById('mortalityChart');
        if (!ctx) return;
        
        try {
            const response = await fetch('/api/mortality-chart');
            const data = await response.json();
            
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.dates,
                    datasets: [{
                        label: 'Mortality Count',
                        data: data.mortality,
                        backgroundColor: 'rgba(244, 67, 54, 0.6)',
                        borderColor: '#F44336',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                        title: {
                            display: true,
                            text: 'Daily Mortality Tracking'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Count'
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error loading mortality chart:', error);
        }
    }
    
    resizeCharts() {
        Chart.helpers.each(Chart.instances, (instance) => {
            instance.resize();
        });
    }
    
    // Utility methods
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-NG', {
            style: 'currency',
            currency: 'NGN'
        }).format(amount);
    }
    
    formatDate(date) {
        return new Intl.DateTimeFormat('en-NG', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        }).format(new Date(date));
    }
    
    // Initialize tooltips
    initTooltips() {
        const tooltips = document.querySelectorAll('[data-tooltip]');
        tooltips.forEach(element => {
            element.addEventListener('mouseenter', (e) => {
                this.showTooltip(e.target, e.target.dataset.tooltip);
            });
            
            element.addEventListener('mouseleave', () => {
                this.hideTooltip();
            });
        });
    }
    
    showTooltip(element, text) {
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip absolute bg-gray-800 text-white px-2 py-1 rounded text-sm z-50';
        tooltip.textContent = text;
        
        document.body.appendChild(tooltip);
        
        const rect = element.getBoundingClientRect();
        tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
        tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
    }
    
    hideTooltip() {
        const tooltip = document.querySelector('.tooltip');
        if (tooltip) tooltip.remove();
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.farmApp = new FarmApp();
});

// Export for use in other scripts
window.FarmApp = FarmApp;