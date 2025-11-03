// GrocerStock Main Application
class GrocerStockApp {
    constructor() {
        this.currentUser = null;
        this.currentPage = 'dashboard';
        this.inventory = [];
        this.socket = null;
        this.init();
    }

    async init() {
        // Initialize the application
        await this.checkAuthStatus();
        this.setupEventListeners();
        this.setupNavigation();
        this.setupRealTimeConnection();
        
        // Hide splash screen after 2 seconds
        setTimeout(() => {
            this.hideSplashScreen();
        }, 2000);
    }

    async checkAuthStatus() {
        try {
            const token = localStorage.getItem('authToken');
            if (token) {
                const user = await this.verifyToken(token);
                if (user) {
                    this.currentUser = user;
                    this.showAuthenticatedUI();
                } else {
                    this.showLoginPage();
                }
            } else {
                this.showLoginPage();
            }
        } catch (error) {
            console.error('Auth check failed:', error);
            this.showLoginPage();
        }
    }

    async verifyToken(token) {
        // Verify JWT token with backend
        try {
            const response = await fetch('/api/auth/verify', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const userData = await response.json();
                return userData.user;
            }
            return null;
        } catch (error) {
            console.error('Token verification failed:', error);
            return null;
        }
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = link.getAttribute('data-page');
                this.navigateTo(page);
            });
        });

        // User menu
        const userMenuBtn = document.getElementById('user-menu-btn');
        const userDropdown = document.getElementById('user-dropdown');
        
        if (userMenuBtn && userDropdown) {
            userMenuBtn.addEventListener('click', () => {
                userDropdown.classList.toggle('hidden');
            });

            // Close dropdown when clicking outside
            document.addEventListener('click', (e) => {
                if (!userMenuBtn.contains(e.target) && !userDropdown.contains(e.target)) {
                    userDropdown.classList.add('hidden');
                }
            });
        }

        // Logout
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                this.logout();
            });
        }

        // Auth forms
        const loginForm = document.getElementById('login-form');
        const signupForm = document.getElementById('signup-form');
        const showSignup = document.getElementById('show-signup');
        const showLogin = document.getElementById('show-login');

        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }
        if (signupForm) {
            signupForm.addEventListener('submit', (e) => this.handleSignup(e));
        }
        if (showSignup) {
            showSignup.addEventListener('click', (e) => {
                e.preventDefault();
                this.showSignupPage();
            });
        }
        if (showLogin) {
            showLogin.addEventListener('click', (e) => {
                e.preventDefault();
                this.showLoginPage();
            });
        }

        // Scanner
        const startScanBtn = document.getElementById('start-scan-btn');
        const cancelScanBtn = document.getElementById('cancel-scan-btn');
        const manualEntryBtn = document.getElementById('manual-entry-btn');
        const manualEntryMainBtn = document.getElementById('manual-entry-main-btn');
        const cancelManualBtn = document.getElementById('cancel-manual-btn');
        const productForm = document.getElementById('product-form');

        if (startScanBtn) {
            startScanBtn.addEventListener('click', () => this.startScanner());
        }
        if (cancelScanBtn) {
            cancelScanBtn.addEventListener('click', () => this.stopScanner());
        }
        if (manualEntryBtn) {
            manualEntryBtn.addEventListener('click', () => this.showManualEntry());
        }
        if (manualEntryMainBtn) {
            manualEntryMainBtn.addEventListener('click', () => this.showManualEntry());
        }
        if (cancelManualBtn) {
            cancelManualBtn.addEventListener('click', () => this.hideManualEntry());
        }
        if (productForm) {
            productForm.addEventListener('submit', (e) => this.handleManualEntry(e));
        }

        // Barcode Generator
        const barcodeForm = document.getElementById('barcode-generator-form');
        const downloadBarcodeBtn = document.getElementById('download-barcode');
        const printBarcodeBtn = document.getElementById('print-barcode');
        const generateAnotherBtn = document.getElementById('generate-another');

        if (barcodeForm) {
            barcodeForm.addEventListener('submit', (e) => this.generateBarcode(e));
        }
        if (downloadBarcodeBtn) {
            downloadBarcodeBtn.addEventListener('click', () => this.downloadBarcode());
        }
        if (printBarcodeBtn) {
            printBarcodeBtn.addEventListener('click', () => this.printBarcode());
        }
        if (generateAnotherBtn) {
            generateAnotherBtn.addEventListener('click', () => this.resetBarcodeForm());
        }

        // Inventory
        const addItemBtn = document.getElementById('add-item-btn');
        const filterBtn = document.getElementById('filter-btn');
        const searchInput = document.getElementById('search-input');
        const searchBtn = document.getElementById('search-btn');

        if (addItemBtn) {
            addItemBtn.addEventListener('click', () => this.navigateTo('scanner'));
        }
        if (filterBtn) {
            filterBtn.addEventListener('click', () => this.toggleFilters());
        }
        if (searchInput && searchBtn) {
            searchInput.addEventListener('input', () => this.searchInventory());
            searchBtn.addEventListener('click', () => this.searchInventory());
        }
    }

    setupNavigation() {
        // Handle browser back/forward
        window.addEventListener('popstate', (e) => {
            const page = window.location.hash.replace('#', '') || 'dashboard';
            this.navigateTo(page, false);
        });

        // Initial page load
        const initialPage = window.location.hash.replace('#', '') || 'dashboard';
        this.navigateTo(initialPage, false);
    }

    navigateTo(page, pushState = true) {
        if (!this.currentUser && page !== 'login' && page !== 'signup') {
            this.showLoginPage();
            return;
        }

        // Update active nav link
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('data-page') === page) {
                link.classList.add('active');
            }
        });

        // Hide all pages
        document.querySelectorAll('.page').forEach(pageEl => {
            pageEl.classList.remove('active');
        });

        // Show target page
        const targetPage = document.getElementById(`${page}-page`);
        if (targetPage) {
            targetPage.classList.add('active');
            this.currentPage = page;

            if (pushState) {
                window.history.pushState({}, '', `#${page}`);
            }

            // Load page-specific data
            this.loadPageData(page);
        }
    }

    async loadPageData(page) {
        switch (page) {
            case 'dashboard':
                await this.loadDashboard();
                break;
            case 'inventory':
                await this.loadInventory();
                break;
            case 'barcode-generator':
                await this.loadBarcodeGenerator();
                break;
        }
    }

    async loadDashboard() {
        try {
            this.showLoading();
            const inventory = await this.fetchInventory();
            this.updateDashboardStats(inventory);
            this.updateRecentItems(inventory);
            this.updateExpiringItems(inventory);
            this.hideLoading();
        } catch (error) {
            console.error('Failed to load dashboard:', error);
            this.showNotification('Failed to load dashboard data', 'error');
            this.hideLoading();
        }
    }

    async loadInventory() {
        try {
            this.showLoading();
            const inventory = await this.fetchInventory();
            this.renderInventory(inventory);
            this.hideLoading();
        } catch (error) {
            console.error('Failed to load inventory:', error);
            this.showNotification('Failed to load inventory', 'error');
            this.hideLoading();
        }
    }

    async loadBarcodeGenerator() {
        try {
            const barcodes = await this.fetchMyBarcodes();
            this.renderMyBarcodes(barcodes);
        } catch (error) {
            console.error('Failed to load barcodes:', error);
            this.showNotification('Failed to load your barcodes', 'error');
        }
    }

    // Authentication Methods
    async handleLogin(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const credentials = {
            email: formData.get('email'),
            password: formData.get('password')
        };

        try {
            this.showLoading();
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(credentials)
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('authToken', data.access_token);
                this.currentUser = data.user;
                this.showAuthenticatedUI();
                this.showNotification('Login successful!', 'success');
            } else {
                const error = await response.json();
                this.showNotification(error.message || 'Login failed', 'error');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showNotification('Login failed. Please try again.', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async handleSignup(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const userData = {
            username: formData.get('username'),
            email: formData.get('email'),
            password: formData.get('password')
        };

        if (userData.password !== formData.get('confirm-password')) {
            this.showNotification('Passwords do not match', 'error');
            return;
        }

        try {
            this.showLoading();
            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(userData)
            });

            if (response.ok) {
                const data = await response.json();
                this.showNotification('Account created successfully! Please login.', 'success');
                this.showLoginPage();
            } else {
                const error = await response.json();
                this.showNotification(error.message || 'Registration failed', 'error');
            }
        } catch (error) {
            console.error('Signup error:', error);
            this.showNotification('Registration failed. Please try again.', 'error');
        } finally {
            this.hideLoading();
        }
    }

    logout() {
        localStorage.removeItem('authToken');
        this.currentUser = null;
        this.socket?.disconnect();
        this.socket = null;
        this.showLoginPage();
        this.showNotification('Logged out successfully', 'success');
    }

    // UI Management
    showAuthenticatedUI() {
        document.getElementById('app').classList.remove('hidden');
        document.getElementById('login-page').classList.add('hidden');
        document.getElementById('signup-page').classList.add('hidden');
        
        if (this.currentUser) {
            const userNameElement = document.getElementById('user-name');
            if (userNameElement) {
                userNameElement.textContent = this.currentUser.username || 'User';
            }
        }
        
        this.navigateTo('dashboard');
    }

    showLoginPage() {
        document.getElementById('app').classList.add('hidden');
        document.getElementById('login-page').classList.remove('hidden');
        document.getElementById('signup-page').classList.add('hidden');
    }

    showSignupPage() {
        document.getElementById('app').classList.add('hidden');
        document.getElementById('login-page').classList.add('hidden');
        document.getElementById('signup-page').classList.remove('hidden');
    }

    hideSplashScreen() {
        const splashScreen = document.getElementById('splash-screen');
        if (splashScreen) {
            splashScreen.style.opacity = '0';
            setTimeout(() => {
                splashScreen.style.display = 'none';
            }, 500);
        }
    }

    showLoading() {
        document.getElementById('loading-overlay').classList.remove('hidden');
    }

    hideLoading() {
        document.getElementById('loading-overlay').classList.add('hidden');
    }

    showNotification(message, type = 'info') {
        const container = document.getElementById('notification-container');
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-icon">${this.getNotificationIcon(type)}</div>
            <div class="notification-content">${message}</div>
            <button class="notification-close">&times;</button>
        `;

        container.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'slideInRight 0.3s ease-out reverse forwards';
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.parentNode.removeChild(notification);
                    }
                }, 300);
            }
        }, 5000);

        // Close button
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.style.animation = 'slideInRight 0.3s ease-out reverse forwards';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        });
    }

    getNotificationIcon(type) {
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        return icons[type] || 'ℹ️';
    }

    // API Methods
    async fetchWithAuth(url, options = {}) {
        const token = localStorage.getItem('authToken');
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(url, {
            ...options,
            headers
        });

        if (response.status === 401) {
            this.logout();
            throw new Error('Authentication required');
        }

        return response;
    }

    async fetchInventory() {
        const response = await this.fetchWithAuth('/api/inventory');
        if (response.ok) {
            const data = await response.json();
            return data.inventory || [];
        }
        throw new Error('Failed to fetch inventory');
    }

    async fetchMyBarcodes() {
        const response = await this.fetchWithAuth('/api/barcode/my-barcodes');
        if (response.ok) {
            const data = await response.json();
            return data.barcodes || [];
        }
        throw new Error('Failed to fetch barcodes');
    }

    // Real-time setup
    setupRealTimeConnection() {
        if (!this.currentUser) return;

        try {
            this.socket = io('http://localhost:3000');
            
            this.socket.on('connect', () => {
                console.log('Connected to real-time service');
                this.socket.emit('join-inventory', this.currentUser.id);
                this.socket.emit('subscribe-expiry', this.currentUser.id);
            });

            this.socket.on('inventory-changed', (data) => {
                this.handleInventoryUpdate(data);
            });

            this.socket.on('expiry-alert', (data) => {
                this.handleExpiryAlert(data);
            });

            this.socket.on('disconnect', () => {
                console.log('Disconnected from real-time service');
            });

        } catch (error) {
            console.error('Failed to connect to real-time service:', error);
        }
    }

    handleInventoryUpdate(data) {
        // Update UI based on inventory changes
        if (this.currentPage === 'dashboard' || this.currentPage === 'inventory') {
            this.loadPageData(this.currentPage);
        }
        this.showNotification('Inventory updated', 'info');
    }

    handleExpiryAlert(data) {
        const message = `${data.product} expires in ${data.days_remaining} day(s)`;
        this.showNotification(message, data.alert_level);
    }

    // Placeholder methods for other functionality
    startScanner() {
        // Implemented in scanner.js
        console.log('Starting scanner...');
    }

    stopScanner() {
        // Implemented in scanner.js
        console.log('Stopping scanner...');
    }

    showManualEntry() {
        // Implemented in scanner.js
        console.log('Showing manual entry form...');
    }

    hideManualEntry() {
        // Implemented in scanner.js
        console.log('Hiding manual entry form...');
    }

    handleManualEntry(e) {
        // Implemented in scanner.js
        e.preventDefault();
        console.log('Handling manual entry...');
    }

    generateBarcode(e) {
        // Implemented in barcode-generator.js
        e.preventDefault();
        console.log('Generating barcode...');
    }

    downloadBarcode() {
        // Implemented in barcode-generator.js
        console.log('Downloading barcode...');
    }

    printBarcode() {
        // Implemented in barcode-generator.js
        console.log('Printing barcode...');
    }

    resetBarcodeForm() {
        // Implemented in barcode-generator.js
        console.log('Resetting barcode form...');
    }

    toggleFilters() {
        // Implemented in inventory.js
        console.log('Toggling filters...');
    }

    searchInventory() {
        // Implemented in inventory.js
        console.log('Searching inventory...');
    }

    updateDashboardStats(inventory) {
        // Implemented in dashboard.js
        console.log('Updating dashboard stats...');
    }

    updateRecentItems(inventory) {
        // Implemented in dashboard.js
        console.log('Updating recent items...');
    }

    updateExpiringItems(inventory) {
        // Implemented in dashboard.js
        console.log('Updating expiring items...');
    }

    renderInventory(inventory) {
        // Implemented in inventory.js
        console.log('Rendering inventory...');
    }

    renderMyBarcodes(barcodes) {
        // Implemented in barcode-generator.js
        console.log('Rendering barcodes...');
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new GrocerStockApp();
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GrocerStockApp;
}