// common.js - Shared navigation and theme functionality

document.addEventListener('DOMContentLoaded', function() {
    initializeTheme();
    initializeNavigation();
});

// Theme Management
function initializeTheme() {
    // Create theme toggle button if it doesn't exist
    if (!document.querySelector('.theme-toggle')) {
        createThemeToggle();
    }
    
    // Load saved theme or default to dark
    const savedTheme = localStorage.getItem('dashboard-theme') || 'dark';
    setTheme(savedTheme);
}

function createThemeToggle() {
    const header = document.querySelector('.header');
    if (header) {
        const themeToggle = document.createElement('button');
        themeToggle.className = 'theme-toggle';
        themeToggle.innerHTML = '🌙';
        themeToggle.title = 'Toggle Theme';
        themeToggle.onclick = toggleTheme;
        header.appendChild(themeToggle);
    }
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('dashboard-theme', theme);
    
    // Update theme toggle icon
    const themeToggle = document.querySelector('.theme-toggle');
    if (themeToggle) {
        themeToggle.innerHTML = theme === 'dark' ? '☀️' : '🌙';
    }
}

// Navigation Management
function initializeNavigation() {
    // Get current page name
    const currentPage = getCurrentPageName();
    
    // Set active tab based on current page
    setActiveTab(currentPage);
    
    // Add click handlers for navigation
    addNavigationHandlers();
}

function getCurrentPageName() {
    const path = window.location.pathname;
    const page = path.split('/').pop();
    
    // Remove .html extension and handle index
    let pageName = page.replace('.html', '');
    if (pageName === '' || pageName === 'index') {
        pageName = 'topology';
    }
    
    return pageName;
}

function setActiveTab(pageName) {
    // Remove active class from all tabs
    document.querySelectorAll('.tab-btn').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Find and activate the correct tab
    const pageMapping = {
        'index': 'topology',
        'topology': 'topology',
        'convergence': 'convergence',
        'archetype': 'archetype',
        'integration': 'integration',
        'model': 'model',
        'documentation': 'documentation',
        'seven-rs': 'seven-rs',
        'recommendations': 'recommendations'
    };
    
    const mappedPage = pageMapping[pageName] || pageName;
    
    // Try to find tab by href
    const activeTab = document.querySelector(`a.tab-btn[href*="${mappedPage}"]`) ||
                     document.querySelector(`a.tab-btn[href="${mappedPage}.html"]`) ||
                     document.querySelector(`a.tab-btn[href="index.html"]`);
    
    if (activeTab) {
        activeTab.classList.add('active');
    }
}

function addNavigationHandlers() {
    // Add smooth transition effect when navigating
    document.querySelectorAll('.tab-btn').forEach(tab => {
        tab.addEventListener('click', function(e) {
            // Add loading state
            showNavigationLoading();
        });
    });
}

// API Configuration with localhost fallback
function getApiBase() {
    const currentHost = window.location.hostname;
    const currentPort = window.location.port;
    
    console.log(`API context detection: ${currentHost}:${currentPort}`);
    
    // Force 127.0.0.1 if localhost fails
    if (currentHost === 'localhost') {
        return 'http://127.0.0.1:8001';
    }
    
    // Handle different port scenarios
    if (currentPort === '8000') {
        return `http://127.0.0.1:8001`;
    }
    
    if (currentPort === '9000') {
        return window.location.origin;
    }
    
    if (currentPort === '8002') {
        return `http://127.0.0.1:8001`;
    }
    
    return `http://${currentHost}:8001`;
}

// Make it globally available
window.getApiBase = getApiBase;
window.API_BASE = getApiBase();

function showNavigationLoading() {
    // Add a subtle loading indicator
    const body = document.body;
    body.style.opacity = '0.8';
    body.style.transition = 'opacity 0.2s ease';
    
    // Reset after navigation
    setTimeout(() => {
        body.style.opacity = '1';
    }, 100);
}

// Utility Functions
function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            gap: 10px;
        `;
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    // Add to container
    toastContainer.appendChild(toast);
    
    // Remove after 3 seconds
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

function showLoading() {
    let spinner = document.getElementById('loading-spinner');
    if (!spinner) {
        spinner = document.createElement('div');
        spinner.id = 'loading-spinner';
        spinner.className = 'loading-spinner';
        document.body.appendChild(spinner);
    }
    spinner.style.display = 'block';
}

function hideLoading() {
    const spinner = document.getElementById('loading-spinner');
    if (spinner) {
        spinner.style.display = 'none';
    }
}

// Export functions for use in other scripts
window.dashboardCommon = {
    showToast,
    showLoading,
    hideLoading,
    setTheme,
    getCurrentPageName
};