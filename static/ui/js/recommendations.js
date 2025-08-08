/**
 * Network Segmentation Recommendations JavaScript
 * Handles tab management, interactivity, and data integration
 */

// Global state management
const RecommendationsApp = {
    currentTab: 'overview',
    applicationData: null,
    networkData: null,
    
    // Initialize the application
    init() {
        this.initializeTabs();
        this.initializeInteractions();
        this.loadApplicationData();
        this.updateMetrics();
        this.initializeAnimations();
        console.log('🔐 Network Segmentation Recommendations initialized');
    },
    
    // Tab Management
    initializeTabs() {
        const tabs = document.querySelectorAll('.sub-tab-btn');
        const contents = document.querySelectorAll('.tab-content');

        tabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                
                // Remove active classes
                tabs.forEach(t => t.classList.remove('active'));
                contents.forEach(c => c.classList.remove('active'));
                
                // Add active class to clicked tab
                tab.classList.add('active');
                
                // Show corresponding content
                const targetTab = tab.getAttribute('data-tab');
                const targetContent = document.getElementById(targetTab + '-tab');
                if (targetContent) {
                    targetContent.classList.add('active');
                    this.currentTab = targetTab;
                    this.onTabChange(targetTab);
                }
            });
        });
        
        // Handle hash navigation
        window.addEventListener('hashchange', () => {
            const hash = window.location.hash.substring(1);
            if (hash) {
                this.switchToTab(hash);
            }
        });
        
        // Initial hash check
        const initialHash = window.location.hash.substring(1);
        if (initialHash && ['overview', 'segmentation', 'roadmap', 'compliance', 'implementation'].includes(initialHash)) {
            this.switchToTab(initialHash);
        }
    },
    
    // Switch to specific tab
    switchToTab(tabName) {
        const tabBtn = document.querySelector(`[data-tab="${tabName}"]`);
        if (tabBtn) {
            tabBtn.click();
        }
    },
    
    // Handle tab change events
    onTabChange(tabName) {
        // Update URL hash
        if (history.replaceState) {
            history.replaceState(null, null, `#${tabName}`);
        }
        
        // Load tab-specific data
        switch (tabName) {
            case 'overview':
                this.loadOverviewData();
                break;
            case 'segmentation':
                this.loadSegmentationData();
                break;
            case 'roadmap':
                this.loadRoadmapData();
                break;
            case 'compliance':
                this.loadComplianceData();
                break;
            case 'implementation':
                this.loadImplementationData();
                break;
        }
        
        // Trigger animations for newly visible content
        this.animateTabContent(tabName);
    },
    
    // Load application data
    async loadApplicationData() {
        try {
            // Check if AppData is available from app-data.js
            if (window.AppData && window.AppData.isDataLoaded) {
                this.applicationData = window.AppData.applicationList;
                this.updateApplicationMetrics();
            } else {
                // Fallback to simulated data
                this.applicationData = this.generateSimulatedData();
                this.updateApplicationMetrics();
            }
        } catch (error) {
            console.warn('Failed to load application data:', error);
            this.applicationData = this.generateSimulatedData();
            this.updateApplicationMetrics();
        }
    },
    
    // Generate simulated data for demo
    generateSimulatedData() {
        const criticalApps = ['ACDA', 'FAPI', 'BCA', 'KYCP', 'FCMS', 'IDRP', 'CDD', 'CACS'];
        const highPriorityApps = ['ALE', 'APSE', 'BP', 'BLZE', 'AODSVY', 'CCPA', 'CIPIV'];
        const operationalApps = ['BOD', 'BTIF', 'CLSR', 'EAPM', 'GWAY', 'HCMS', 'ICBK', 'ITGC', 'MCA'];
        
        const allApps = [...criticalApps, ...highPriorityApps, ...operationalApps];
        
        return allApps.map(id => ({
            id: id,
            name: this.getAppName(id),
            criticality: criticalApps.includes(id) ? 'Critical' : 
                        highPriorityApps.includes(id) ? 'High' : 'Medium',
            zone: this.getSecurityZone(id, criticalApps, highPriorityApps),
            connections: Math.floor(Math.random() * 15) + 5,
            traffic: Math.floor(Math.random() * 1000) + 100
        }));
    },
    
    // Get application name from ID
    getAppName(id) {
        const nameMap = {
            'ACDA': 'ATM Card Dispute Application',
            'FAPI': 'Fraud Detection API',
            'BCA': 'Branch Customer Authentication',
            'KYCP': 'Know Your Customer Platform',
            'FCMS': 'Fraud Case Management System',
            'IDRP': 'Identity Resolution Platform',
            'CDD': 'Customer Due Diligence',
            'CACS': 'Customer Account Control System',
            'ALE': 'Account Lifecycle Engine',
            'APSE': 'Account Processing Service Engine',
            'BP': 'Banking Platform',
            'BLZE': 'Business Logic Zone Engine',
            'AODSVY': 'Account Opening Data Survey',
            'CCPA': 'Customer Communication Platform',
            'CIPIV': 'Customer Identity Verification',
            'BOD': 'Business Operations Dashboard',
            'BTIF': 'Banking Transaction Interface',
            'CLSR': 'Core Ledger Service Router',
            'EAPM': 'Enterprise Application Management',
            'GWAY': 'API Gateway',
            'HCMS': 'Human Capital Management System'
        };
        return nameMap[id] || `${id} Application`;
    },
    
    // Determine security zone for application
    getSecurityZone(id, criticalApps, highPriorityApps) {
        if (criticalApps.includes(id)) return 'critical-banking';
        if (highPriorityApps.includes(id)) return 'customer-services';
        return Math.random() > 0.5 ? 'operations' : 'analytics';
    },
    
    // Update application metrics
    updateApplicationMetrics() {
        if (!this.applicationData) return;
        
        const totalApps = this.applicationData.length;
        const criticalApps = this.applicationData.filter(app => app.criticality === 'Critical').length;
        const networkComponents = totalApps * 4.6; // Estimated components per app
        
        // Update header metrics
        const headerAppCount = document.getElementById('total-applications');
        const headerComponents = document.getElementById('network-components');
        
        if (headerAppCount) headerAppCount.textContent = totalApps;
        if (headerComponents) headerComponents.textContent = Math.round(networkComponents);
        
        // Update overview metrics
        const overviewAppCount = document.getElementById('total-apps-metric');
        const overviewComponents = document.getElementById('components-metric');
        
        if (overviewAppCount) overviewAppCount.textContent = totalApps;
        if (overviewComponents) overviewComponents.textContent = Math.round(networkComponents);
    },
    
    // Initialize interactions
    initializeInteractions() {
        // Checkbox interactions
        this.initializeCheckboxes();
        
        // Zone card interactions
        this.initializeZoneCards();
        
        // Progress tracking
        this.initializeProgressTracking();
        
        // Search and filter functionality
        this.initializeSearchAndFilter();
    },
    
    // Initialize checkbox functionality
    initializeCheckboxes() {
        const checkboxes = document.querySelectorAll('.checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('click', () => {
                this.toggleCheckbox(checkbox);
            });
        });
    },
    
    // Toggle checkbox state
    toggleCheckbox(checkbox) {
        checkbox.classList.toggle('checked');
        this.updateProgress();
        
        // Add animation
        checkbox.style.transform = 'scale(1.1)';
        setTimeout(() => {
            checkbox.style.transform = 'scale(1)';
        }, 150);
    },
    
    // Update progress calculation
    updateProgress() {
        const checkboxes = document.querySelectorAll('.checkbox');
        const checkedBoxes = document.querySelectorAll('.checkbox.checked');
        const progressPercentage = Math.round((checkedBoxes.length / checkboxes.length) * 100);
        
        const progressElement = document.querySelector('.progress-percentage');
        const progressFill = document.querySelector('.progress-fill');
        
        if (progressElement) {
            progressElement.textContent = progressPercentage + '%';
        }
        
        if (progressFill) {
            progressFill.style.width = progressPercentage + '%';
        }
        
        // Update progress description
        const progressDesc = document.getElementById('progress-description');
        if (progressDesc) {
            if (progressPercentage < 25) {
                progressDesc.textContent = 'Initial setup and basic infrastructure in place';
            } else if (progressPercentage < 50) {
                progressDesc.textContent = 'Foundation established, beginning segmentation implementation';
            } else if (progressPercentage < 75) {
                progressDesc.textContent = 'Microsegmentation in progress, security controls active';
            } else if (progressPercentage < 95) {
                progressDesc.textContent = 'Advanced security measures deployed, compliance alignment';
            } else {
                progressDesc.textContent = 'Zero trust architecture fully implemented and operational';
            }
        }
    },
    
    // Initialize zone card interactions
    initializeZoneCards() {
        const zoneCards = document.querySelectorAll('.zone-card');
        zoneCards.forEach(card => {
            card.addEventListener('click', () => {
                this.selectZone(card);
            });
            
            card.addEventListener('mouseenter', () => {
                this.highlightZone(card, true);
            });
            
            card.addEventListener('mouseleave', () => {
                this.highlightZone(card, false);
            });
        });
    },
    
    // Select zone functionality
    selectZone(zoneCard) {
        // Remove previous selections
        document.querySelectorAll('.zone-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        // Add selection to clicked card
        zoneCard.classList.add('selected');
        
        // Show zone details
        const zoneName = zoneCard.querySelector('.zone-title').textContent;
        this.showZoneDetails(zoneName);
    },
    
    // Highlight zone on hover
    highlightZone(zoneCard, highlight) {
        if (highlight) {
            zoneCard.style.transform = 'translateY(-4px) scale(1.02)';
            zoneCard.style.boxShadow = '0 8px 25px rgba(59, 130, 246, 0.2)';
        } else {
            zoneCard.style.transform = 'translateY(0) scale(1)';
            zoneCard.style.boxShadow = '';
        }
    },
    
    // Show zone details
    showZoneDetails(zoneName) {
        // This could open a modal or update a details panel
        console.log(`Showing details for zone: ${zoneName}`);
        
        // For now, just show a toast notification
        this.showToast(`Selected ${zoneName} zone for detailed analysis`);
    },
    
    // Initialize progress tracking
    initializeProgressTracking() {
        // Set initial progress
        this.updateProgress();
        
        // Add progress animations
        const progressBar = document.querySelector('.progress-fill');
        if (progressBar) {
            progressBar.style.transition = 'width 0.3s ease-in-out';
        }
    },
    
    // Initialize search and filter
    initializeSearchAndFilter() {
        // This would integrate with the main app's search functionality
        // For now, we'll add basic interaction feedback
        const searchInputs = document.querySelectorAll('input[type="text"]');
        searchInputs.forEach(input => {
            input.addEventListener('focus', () => {
                input.style.borderColor = 'var(--accent-blue)';
            });
            
            input.addEventListener('blur', () => {
                input.style.borderColor = 'var(--border-color)';
            });
        });
    },
    
    // Load tab-specific data
    loadOverviewData() {
        // Update current state analysis based on application data
        if (this.applicationData) {
            this.updateCurrentStateAnalysis();
        }
    },
    
    loadSegmentationData() {
        if (this.applicationData) {
            this.updateSegmentationZones();
        }
    },
    
    loadRoadmapData() {
        // No specific data loading needed for roadmap
        // Timeline is static content
    },
    
    loadComplianceData() {
        // Update compliance scores based on current implementation
        this.updateComplianceScores();
    },
    
    loadImplementationData() {
        // Update implementation checklist and progress
        this.updateImplementationStatus();
    },
    
    // Update current state analysis
    updateCurrentStateAnalysis() {
        const criticalCount = this.applicationData.filter(app => app.criticality === 'Critical').length;
        const highCount = this.applicationData.filter(app => app.criticality === 'High').length;
        const standardCount = this.applicationData.length - criticalCount - highCount;
        
        // Update risk matrix
        const riskCards = document.querySelectorAll('#current-state-matrix .risk-score');
        if (riskCards.length >= 3) {
            riskCards[0].textContent = criticalCount;
            riskCards[1].textContent = highCount;
            riskCards[2].textContent = standardCount;
        }
    },
    
    // Update segmentation zones
    updateSegmentationZones() {
        if (!this.applicationData) return;
        
        const zones = {
            'critical-banking': 0,
            'customer-services': 0,
            'operations': 0,
            'analytics': 0
        };
        
        this.applicationData.forEach(app => {
            if (zones.hasOwnProperty(app.zone)) {
                zones[app.zone]++;
            }
        });
        
        // Update zone cards
        const zoneCards = document.querySelectorAll('.zone-card .zone-apps');
        if (zoneCards.length >= 4) {
            zoneCards[0].textContent = zones['critical-banking'];
            zoneCards[1].textContent = zones['customer-services'];
            zoneCards[2].textContent = zones['operations'];
            zoneCards[3].textContent = zones['analytics'];
        }
    },
    
    // Update compliance scores
    updateComplianceScores() {
        // Simulate compliance score calculation based on progress
        const progressPercentage = this.calculateOverallProgress();
        
        const pciScore = Math.min(25 + (progressPercentage * 0.7), 95);
        const soxScore = Math.min(40 + (progressPercentage * 0.55), 95);
        const ffiecScore = Math.min(35 + (progressPercentage * 0.6), 95);
        const nistScore = Math.min(65 + (progressPercentage * 0.3), 95);
        
        // Update compliance cards if they exist
        const complianceCards = document.querySelectorAll('.compliance-score');
        if (complianceCards.length >= 4) {
            complianceCards[0].textContent = Math.round(pciScore) + '%';
            complianceCards[1].textContent = Math.round(soxScore) + '%';
            complianceCards[2].textContent = Math.round(ffiecScore) + '%';
            complianceCards[3].textContent = Math.round(nistScore) + '%';
        }
    },
    
    // Calculate overall progress
    calculateOverallProgress() {
        const checkboxes = document.querySelectorAll('.checkbox');
        const checkedBoxes = document.querySelectorAll('.checkbox.checked');
        return checkboxes.length > 0 ? (checkedBoxes.length / checkboxes.length) * 100 : 12;
    },
    
    // Update implementation status
    updateImplementationStatus() {
        // This would typically sync with backend implementation status
        // For now, maintain current checkbox states
        this.updateProgress();
    },
    
    // Animation functions
    initializeAnimations() {
        // Intersection Observer for fade-in animations
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-fade-in');
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });

        // Observe cards and major elements
        document.querySelectorAll('.card, .metric-card, .zone-card, .timeline-content').forEach(el => {
            observer.observe(el);
        });
        
        // Add CSS for animations
        if (!document.querySelector('#recommendations-animations')) {
            const style = document.createElement('style');
            style.id = 'recommendations-animations';
            style.textContent = `
                .animate-fade-in {
                    animation: fadeInUp 0.6s ease-out forwards;
                }
                
                @keyframes fadeInUp {
                    from {
                        opacity: 0;
                        transform: translateY(20px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }
                
                .zone-card.selected {
                    border-color: var(--accent-blue) !important;
                    background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), transparent) !important;
                    transform: translateY(-2px) scale(1.02);
                    box-shadow: 0 8px 25px rgba(59, 130, 246, 0.3);
                }
            `;
            document.head.appendChild(style);
        }
    },
    
    // Animate tab content
    animateTabContent(tabName) {
        const activeTab = document.getElementById(tabName + '-tab');
        if (activeTab) {
            // Reset animations
            const elements = activeTab.querySelectorAll('.card, .metric-card, .action-item');
            elements.forEach((el, index) => {
                el.style.opacity = '0';
                el.style.transform = 'translateY(20px)';
                
                setTimeout(() => {
                    el.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
                    el.style.opacity = '1';
                    el.style.transform = 'translateY(0)';
                }, index * 100);
            });
        }
    },
    
    // Utility functions
    updateMetrics() {
        // Update any dynamic metrics
        if (this.applicationData) {
            this.updateApplicationMetrics();
        }
    },
    
    // Show toast notification
    showToast(message, type = 'info') {
        // Create toast if it doesn't exist
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 1000;
                display: flex;
                flex-direction: column;
                gap: 10px;
            `;
            document.body.appendChild(toastContainer);
        }
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.style.cssText = `
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-left: 4px solid var(--accent-blue);
            border-radius: 8px;
            padding: 12px 16px;
            color: var(--text-primary);
            font-size: 14px;
            max-width: 300px;
            transform: translateX(100%);
            transition: transform 0.3s ease;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        `;
        toast.textContent = message;
        
        toastContainer.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.style.transform = 'translateX(0)';
        }, 10);
        
        // Remove after 3 seconds
        setTimeout(() => {
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 3000);
    },
    
    // Export functionality (if needed)
    exportData() {
        const exportData = {
            applicationData: this.applicationData,
            currentProgress: this.calculateOverallProgress(),
            implementationStatus: this.getImplementationStatus(),
            timestamp: new Date().toISOString()
        };
        
        const dataStr = JSON.stringify(exportData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        
        const link = document.createElement('a');
        link.href = URL.createObjectURL(dataBlob);
        link.download = 'network-segmentation-analysis.json';
        link.click();
        
        this.showToast('Analysis data exported successfully');
    },
    
    // Get implementation status
    getImplementationStatus() {
        const checkboxes = document.querySelectorAll('.checkbox');
        const status = {};
        
        checkboxes.forEach((checkbox, index) => {
            const section = checkbox.closest('.checklist-section');
            const sectionTitle = section ? section.querySelector('.checklist-title').textContent.trim() : 'Unknown';
            const itemText = checkbox.nextElementSibling ? checkbox.nextElementSibling.textContent.trim() : 'Unknown';
            
            if (!status[sectionTitle]) {
                status[sectionTitle] = {};
            }
            
            status[sectionTitle][itemText] = checkbox.classList.contains('checked');
        });
        
        return status;
    }
};

// Global functions for HTML onclick handlers
function toggleCheckbox(checkbox) {
    RecommendationsApp.toggleCheckbox(checkbox);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    RecommendationsApp.init();
});

// Initialize when app data is loaded (if it loads after DOM)
if (window.AppData) {
    window.AppData.onDataLoaded = () => {
        RecommendationsApp.loadApplicationData();
    };
}

// Export for global access
window.RecommendationsApp = RecommendationsApp;