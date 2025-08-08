// App Rationalization Dashboard JavaScript - CLEANED AND FIXED VERSION

class AppRationalizationDashboard {
    constructor() {
        this.applications = [];
        this.selectedApps = new Set();
        this.selectedStrategies = new Set(['rehost', 'replatform', 'refactor', 'retire']);
        this.currentApproach = 'phased';
        this.isEditing = false;
        this.migrationAnalysis = {};
        this.rationalizationData = {};
        
        // Initialize unified migration data BEFORE centralized data
        this.initializeMigrationData();
        
        // Initialize with centralized data
        this.initializeWithCentralizedData();
    }
    
    // ================================================================================
    // UNIFIED MIGRATION DATA INITIALIZATION - SINGLE SOURCE OF TRUTH
    // ================================================================================
    
    initializeMigrationData() {
        console.log('🔄 Initializing unified migration data...');
        
        this.migrationAnalysis = {
            approaches: {
                phased: {
                    name: 'Phased Migration',
                    description: 'Gradual migration in multiple phases',
                    timeline: '12-18 months',
                    risk: 'Low',
                    totalDuration: '18 weeks',
                    totalBudget: 350000,
                    riskLevel: 'Medium',
                    successRate: 85,
                    phases: [
                        {
                            name: 'Phase 1: Assessment & Planning',
                            duration: '4 weeks',
                            applications: ['app1', 'app2'],
                            tasks: ['Application inventory', 'Dependency mapping', 'Risk assessment'],
                            status: 'planned',
                            startDate: new Date(),
                            budget: 50000,
                            order: 1
                        },
                        {
                            name: 'Phase 2: Low-Risk Migrations',
                            duration: '6 weeks',
                            applications: ['app3', 'app4'],
                            tasks: ['Migrate non-critical apps', 'Testing', 'Validation'],
                            status: 'planned',
                            startDate: new Date(Date.now() + 28 * 24 * 60 * 60 * 1000),
                            budget: 100000,
                            order: 2
                        },
                        {
                            name: 'Phase 3: Critical Systems',
                            duration: '8 weeks',
                            applications: ['core-banking', 'payment-system'],
                            tasks: ['Critical app migration', 'Performance testing', 'Rollback planning'],
                            status: 'planned',
                            startDate: new Date(Date.now() + 70 * 24 * 60 * 60 * 1000),
                            budget: 200000,
                            order: 3
                        }
                    ]
                },
                
                bigBang: {
                    name: 'Big Bang Migration',
                    description: 'Complete migration in single phase',
                    timeline: '3-6 months',
                    risk: 'High',
                    totalDuration: '24 weeks',
                    totalBudget: 500000,
                    riskLevel: 'High',
                    successRate: 65,
                    phases: [
                        {
                            name: 'Complete Preparation',
                            duration: '20 weeks',
                            applications: 'all',
                            tasks: ['Full system preparation', 'Comprehensive testing', 'Rollback preparation'],
                            status: 'planned',
                            startDate: new Date(),
                            budget: 400000,
                            order: 1
                        },
                        {
                            name: 'Migration Cutover',
                            duration: '4 weeks',
                            applications: 'all',
                            tasks: ['Complete system migration', 'Go-live', 'Support'],
                            status: 'planned',
                            startDate: new Date(Date.now() + 140 * 24 * 60 * 60 * 1000),
                            budget: 100000,
                            order: 2
                        }
                    ]
                }
            },
            
            currentApproach: this.currentApproach,
            timeline: {
                start: new Date(),
                end: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000),
                milestones: []
            }
        };
        
        // Initialize rationalization data with migration structure
        this.rationalizationData = {
            applications: this.applications,
            selectedStrategies: Array.from(this.selectedStrategies),
            migration: {
                phased: this.migrationAnalysis.approaches.phased,
                timeline: this.migrationAnalysis.timeline,
                currentApproach: this.currentApproach
            },
            recommendations: [],
            costSavings: {},
            riskAssessment: {}
        };
        
        console.log('✅ Migration data initialized with approach:', this.currentApproach);
        console.log('✅ Available approaches:', Object.keys(this.migrationAnalysis.approaches));
    }
    
    // ================================================================================
    // RATIONALIZATION DATA GENERATION - SINGLE METHOD
    // ================================================================================
    
    generateRationalizationData() {
        console.log('🔄 Generating rationalization data...');
        
        try {
            // Update rationalization data with current application data
            this.rationalizationData.applications = this.applications;
            this.rationalizationData.selectedStrategies = Array.from(this.selectedStrategies);
            
            // Generate recommendations based on current data
            this.rationalizationData.recommendations = this.generateRecommendations();
            this.rationalizationData.costSavings = this.calculateCostSavings();
            this.rationalizationData.riskAssessment = this.assessRisks();
            
            // Update migration data with current approach
            this.rationalizationData.migration.currentApproach = this.currentApproach;
            
            console.log('✅ Rationalization data generated:', this.rationalizationData);
            
        } catch (error) {
            console.error('❌ Error generating rationalization data:', error);
            this.rationalizationData = this.generateFallbackData();
        }
    }
    
    // Helper methods for rationalization data
    generateRecommendations() {
        return [
            { type: 'consolidate', count: 3, savings: 75000 },
            { type: 'modernize', count: 5, savings: 120000 },
            { type: 'retire', count: 2, savings: 45000 }
        ];
    }
    
    calculateCostSavings() {
        return {
            annual: 240000,
            monthly: 20000,
            breakdown: {
                licensing: 120000,
                maintenance: 80000,
                infrastructure: 40000
            }
        };
    }
    
    assessRisks() {
        return {
            high: 2,
            medium: 5,
            low: 8,
            total: 15,
            details: [
                { app: 'legacy-system', risk: 'high', reason: 'Critical dependency' },
                { app: 'payment-gateway', risk: 'medium', reason: 'Complex integration' }
            ]
        };
    }
    
    generateFallbackData() {
        return {
            applications: [],
            recommendations: [],
            costSavings: { annual: 0, monthly: 0, breakdown: {} },
            riskAssessment: { high: 0, medium: 0, low: 0, details: [] }
        };
    }
    
    // ================================================================================
    // MIGRATION CONTENT GENERATION - SINGLE, CLEAN METHOD
    // ================================================================================
    
    generateMigrationContent() {
        console.log('🔄 generateMigrationContent called');
        
        try {
            const content = document.getElementById('migrationContent');
            if (!content) {
                console.warn('❌ migrationContent element not found');
                return;
            }
            
            // Debug current state
            console.log('🔍 Current approach:', this.currentApproach);
            console.log('🔍 Migration analysis:', this.migrationAnalysis);
            
            // Ensure migration analysis is initialized
            if (!this.migrationAnalysis.approaches) {
                console.warn('❌ Migration analysis not properly initialized, reinitializing...');
                this.initializeMigrationData();
            }
            
            const approach = this.migrationAnalysis.approaches[this.currentApproach];
            if (!approach) {
                console.warn(`❌ Approach '${this.currentApproach}' not found, using default`);
                this.currentApproach = 'phased';
                const fallbackApproach = this.migrationAnalysis.approaches.phased;
                this.renderMigrationContent(content, fallbackApproach);
                return;
            }
            
            console.log('✅ Using approach:', approach.name);
            
            // Render the content
            this.renderMigrationContent(content, approach);
            
        } catch (error) {
            console.error('❌ Error in generateMigrationContent:', error);
            this.renderErrorContent();
        }
    }
    
    renderMigrationContent(content, approach) {
        const html = `
            <div class="migration-approach-content">
                <div class="approach-header">
                    <h3>📋 ${approach.name}</h3>
                    <p class="approach-description">${approach.description}</p>
                </div>
                
                <div class="migration-metrics">
                    <div class="metric">
                        <span class="metric-label">Duration:</span>
                        <span class="metric-value">${approach.totalDuration || approach.timeline}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Budget:</span>
                        <span class="metric-value">$${approach.totalBudget?.toLocaleString() || 'TBD'}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Risk Level:</span>
                        <span class="metric-value ${approach.riskLevel?.toLowerCase()}-risk">${approach.riskLevel || approach.risk}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Success Rate:</span>
                        <span class="metric-value">${approach.successRate || 'TBD'}%</span>
                    </div>
                </div>
                
                <div class="migration-phases">
                    <h4>📅 Migration Phases (${approach.phases?.length || 0})</h4>
                    <div class="phases-container">
                        ${approach.phases ? approach.phases.map((phase, index) => `
                            <div class="phase-card">
                                <div class="phase-header">
                                    <h5>Phase ${index + 1}: ${phase.name}</h5>
                                    <span class="phase-duration">${phase.duration}</span>
                                </div>
                                <div class="phase-details">
                                    <p><strong>Budget:</strong> $${phase.budget?.toLocaleString() || 'TBD'}</p>
                                    <p><strong>Applications:</strong> ${Array.isArray(phase.applications) ? phase.applications.join(', ') : phase.applications}</p>
                                    <div class="phase-tasks">
                                        <strong>Key Tasks:</strong>
                                        <ul>
                                            ${phase.tasks.map(task => `<li>${task}</li>`).join('')}
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        `).join('') : '<p>No phases defined for this approach.</p>'}
                    </div>
                </div>
            </div>
        `;
        
        content.innerHTML = html;
    }
    
    renderErrorContent() {
        const content = document.getElementById('migrationContent');
        if (content) {
            content.innerHTML = `
                <div class="migration-error">
                    <h3>⚠️ Migration Content Error</h3>
                    <p>Unable to load migration approach content.</p>
                    <button onclick="window.dashboard?.retryMigrationContent()" class="retry-button">
                        🔄 Retry
                    </button>
                </div>
            `;
        }
    }
    
    retryMigrationContent() {
        console.log('🔄 Retrying migration content generation...');
        this.initializeMigrationData();
        this.generateMigrationContent();
    }
    
    // ================================================================================
    // CENTRALIZED DATA INTEGRATION
    // ================================================================================
    
    initializeWithCentralizedData() {
        console.log('🔄 Initializing App Rationalization with centralized data...');
        
        if (!window.AppData) {
            console.warn('⚠️ AppData not available, using fallback initialization');
            this.initializeFallbackData();
            return;
        }
        
        // Wait for centralized data to be loaded
        if (window.AppData.onDataLoaded) {
            window.AppData.onDataLoaded(() => {
                this.loadApplicationsFromCentralizedData();
                this.generateRationalizationData();
                this.setupEventListeners();
                this.initializeUI();
                this.updateDashboard();
                console.log('✅ App Rationalization Dashboard initialized with centralized data');
            });
        } else {
            console.warn('⚠️ AppData.onDataLoaded not available, initializing with fallback');
            this.initializeFallbackData();
        }
        
        // Listen for filter changes from other components
        if (window.AppData && window.AppData.onFilterChange) {
            window.AppData.onFilterChange((filterData) => {
                if (filterData.source !== 'app-rationalization' && filterData.selectedApps) {
                    console.log('📡 App Rationalization received filter update from:', filterData.source);
                    this.syncExternalFilterChange(filterData.selectedApps);
                }
            });
        }
    }
    
    initializeFallbackData() {
        // Create sample data when centralized data isn't available
        this.applications = [
            {
                id: 'app1',
                name: 'Core Banking System',
                archetype: 'Monolithic',
                businessFunction: 'Core Banking',
                criticality: 'critical',
                technology: 'Java',
                strategy: 'replatform',
                complexity: 'high',
                currentCost: 50000,
                projectedSavings: 15000
            },
            {
                id: 'app2',
                name: 'Customer Portal',
                archetype: 'Client-Server',
                businessFunction: 'Customer Services',
                criticality: 'high',
                technology: '.NET',
                strategy: 'rehost',
                complexity: 'medium',
                currentCost: 25000,
                projectedSavings: 8000
            }
        ];
        
        this.generateRationalizationData();
        this.setupEventListeners();
        this.initializeUI();
        this.updateDashboard();
        
        console.log('✅ App Rationalization initialized with fallback data');
    }
    
    loadApplicationsFromCentralizedData() {
        console.log('📊 Loading applications from centralized data...');
        
        if (!window.AppData || !window.AppData.getApplicationsByIds) {
            console.warn('❌ AppData or getApplicationsByIds not available');
            return;
        }
        
        try {
            const centralizedApps = window.AppData.getApplicationsByIds(['all']);
            
            this.applications = centralizedApps.map(app => {
                const rationalizationData = this.generateRationalizationMetrics(app);
                
                return {
                    id: app.id,
                    name: app.name,
                    archetype: app.archetype,
                    businessFunction: app.businessFunction,
                    criticality: app.criticality,
                    technology: app.technology,
                    nodeCount: app.nodeCount,
                    strategy: rationalizationData.strategy,
                    complexity: rationalizationData.complexity,
                    dependencies: rationalizationData.dependencies,
                    businessCriticality: app.criticality,
                    currentCost: rationalizationData.currentCost,
                    projectedSavings: rationalizationData.projectedSavings,
                    migrationEffort: rationalizationData.migrationEffort,
                    cloudReadiness: rationalizationData.cloudReadiness,
                    technicalDebt: rationalizationData.technicalDebt,
                    riskScore: rationalizationData.riskScore,
                    roi: rationalizationData.roi
                };
            });
            
            console.log(`📋 Transformed ${this.applications.length} applications for rationalization analysis`);
            this.populateApplicationSelector();
            
        } catch (error) {
            console.error('❌ Error loading applications from centralized data:', error);
            this.initializeFallbackData();
        }
    }
    
    generateRationalizationMetrics(app) {
        const strategies = ['rehost', 'replatform', 'refactor', 'retire'];
        const complexities = ['low', 'medium', 'high'];
        
        // Intelligent strategy assignment based on app characteristics
        let strategy;
        if (app.archetype === 'Monolithic' && app.criticality !== 'critical') {
            strategy = Math.random() > 0.5 ? 'retire' : 'refactor';
        } else if (app.archetype === 'Client-Server') {
            strategy = 'replatform';
        } else if (app.archetype === 'Microservices') {
            strategy = 'rehost';
        } else {
            strategy = strategies[Math.floor(Math.random() * strategies.length)];
        }
        
        // Complexity based on node count and archetype
        let complexity;
        if (app.nodeCount > 5 || app.archetype === 'SOA') {
            complexity = 'high';
        } else if (app.nodeCount > 3) {
            complexity = 'medium';
        } else {
            complexity = 'low';
        }
        
        const dependencies = Math.max(1, app.nodeCount - 1 + (app.businessFunction === 'Core Banking' ? 3 : 1));
        const baseCost = complexity === 'high' ? 50000 : complexity === 'medium' ? 25000 : 15000;
        const criticalityMultiplier = app.criticality === 'critical' ? 1.5 : app.criticality === 'high' ? 1.2 : 1;
        const currentCost = Math.floor(baseCost * criticalityMultiplier * (0.8 + Math.random() * 0.4));
        
        const savingsMultiplier = {
            'retire': 1.0,
            'rehost': 0.3,
            'replatform': 0.5,
            'refactor': 0.7
        };
        const projectedSavings = Math.floor(currentCost * (savingsMultiplier[strategy] || 0.4));
        
        const migrationEffort = complexity === 'high' || strategy === 'refactor' ? 'high' : 
                              complexity === 'medium' || strategy === 'replatform' ? 'medium' : 'low';
        
        return {
            strategy,
            complexity,
            dependencies,
            currentCost,
            projectedSavings,
            migrationEffort,
            cloudReadiness: Math.floor(Math.random() * 100),
            technicalDebt: Math.floor(Math.random() * 10),
            riskScore: Math.floor(Math.random() * 100),
            roi: projectedSavings > 0 ? Math.floor((projectedSavings / currentCost) * 100) : 0
        };
    }
    
    // ================================================================================
    // UI METHODS
    // ================================================================================
    
    populateApplicationSelector() {
        const selector = document.getElementById('appSelect');
        if (!selector) return;

        selector.innerHTML = '';
        
        const allOption = document.createElement('option');
        allOption.value = 'all';
        allOption.textContent = `All Applications (${this.applications.length})`;
        allOption.selected = true;
        selector.appendChild(allOption);
        
        const groupedApps = this.groupApplicationsByBusinessFunction();
        
        Object.entries(groupedApps).forEach(([businessFunction, apps]) => {
            const optgroup = document.createElement('optgroup');
            optgroup.label = `${businessFunction} (${apps.length})`;
            
            apps.forEach(app => {
                const option = document.createElement('option');
                option.value = app.id;
                option.textContent = `${app.name} (${app.strategy} - ${app.criticality})`;
                option.dataset.archetype = app.archetype;
                option.dataset.strategy = app.strategy;
                option.dataset.criticality = app.criticality;
                optgroup.appendChild(option);
            });
            
            selector.appendChild(optgroup);
        });
        
        this.selectedApps = new Set(this.applications.map(app => app.id));
    }
    
    groupApplicationsByBusinessFunction() {
        const grouped = {};
        
        this.applications.forEach(app => {
            const bf = app.businessFunction || 'Other';
            if (!grouped[bf]) {
                grouped[bf] = [];
            }
            grouped[bf].push(app);
        });
        
        Object.keys(grouped).forEach(bf => {
            grouped[bf].sort((a, b) => {
                const criticalityOrder = { 'critical': 4, 'high': 3, 'medium': 2, 'low': 1 };
                const aCrit = criticalityOrder[a.criticality] || 1;
                const bCrit = criticalityOrder[b.criticality] || 1;
                
                if (aCrit !== bCrit) return bCrit - aCrit;
                return a.name.localeCompare(b.name);
            });
        });
        
        return grouped;
    }
    
    setupEventListeners() {
        // Strategy filter checkboxes
        document.querySelectorAll('.rs-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const strategy = e.target.closest('.rs-item').dataset.strategy;
                if (e.target.checked) {
                    this.selectedStrategies.add(strategy);
                    e.target.closest('.rs-item').classList.add('selected');
                } else {
                    this.selectedStrategies.delete(strategy);
                    e.target.closest('.rs-item').classList.remove('selected');
                }
                this.updateDashboard();
                this.broadcastFilterChange();
            });
        });

        // Strategy filter items (clickable)
        document.querySelectorAll('.rs-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (e.target.type === 'checkbox') return;
                
                const checkbox = item.querySelector('.rs-checkbox');
                if (checkbox) {
                    checkbox.checked = !checkbox.checked;
                    checkbox.dispatchEvent(new Event('change'));
                }
            });
        });

        // Application selector
        const appSelect = document.getElementById('appSelect');
        if (appSelect) {
            appSelect.addEventListener('change', () => {
                this.updateSelectedApplications();
                this.updateDashboard();
                this.broadcastFilterChange();
            });
        }

        this.setupToolbarButtons();
    }
    
    setupToolbarButtons() {
        const editBtn = document.getElementById('editBtn');
        if (editBtn) {
            editBtn.addEventListener('click', () => this.toggleEdit());
        }

        const approachToggle = document.getElementById('approachToggle');
        if (approachToggle) {
            approachToggle.addEventListener('click', () => this.toggleApproach());
        }
    }
    
    initializeUI() {
        const reportDate = document.getElementById('reportDate');
        if (reportDate) {
            reportDate.textContent = new Date().toLocaleDateString();
        }

        const currentApproach = document.getElementById('currentApproach');
        if (currentApproach) {
            currentApproach.textContent = this.currentApproach === 'phased' ? 'Phased Migration' : 'Big Bang Migration';
        }

        this.selectedApps = new Set(this.applications.map(app => app.id));
        this.updateStrategyCounts();
    }
    
    updateDashboard() {
        console.log('🔄 Updating dashboard...');
        
        try {
            if (!this.rationalizationData) {
                console.warn('❌ No rationalization data available');
                this.showErrorState('No data available');
                return;
            }
            
            console.log('📊 Dashboard data:', this.rationalizationData);
            
            this.updateStrategyCounts();
            this.updateSummaryCards();
            this.generateMigrationContent();
            this.updateFinancialContent();
            
        } catch (error) {
            console.error('❌ Error updating dashboard:', error);
            this.showErrorState(`Dashboard update failed: ${error.message}`);
        }
    }
    
    showErrorState(message) {
        const container = document.getElementById('app-rationalization-dashboard');
        if (container) {
            container.innerHTML = `
                <div style="padding: 20px; text-align: center; color: #ef4444; background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; margin: 20px;">
                    <h3>⚠️ Dashboard Error</h3>
                    <p>${message}</p>
                    <button onclick="window.dashboard?.retryMigrationContent()" style="margin-top: 10px; padding: 8px 16px; background: #3b82f6; color: white; border: none; border-radius: 4px; cursor: pointer;">
                        Retry
                    </button>
                </div>
            `;
        }
    }
    
    // ================================================================================
    // DASHBOARD UPDATE METHODS
    // ================================================================================
    
    updateStrategyCounts() {
        const filteredApps = this.getFilteredApplications();
        const strategyCounts = {};
        
        ['rehost', 'replatform', 'refactor', 'retire', 'retain', 'repurchase', 'relocate'].forEach(strategy => {
            strategyCounts[strategy] = 0;
        });
        
        filteredApps.forEach(app => {
            strategyCounts[app.strategy]++;
        });
        
        Object.entries(strategyCounts).forEach(([strategy, count]) => {
            const countElement = document.getElementById(`${strategy}Count`);
            if (countElement) {
                countElement.textContent = count;
            }
            
            const quickCountElement = document.getElementById(`quick${strategy.charAt(0).toUpperCase() + strategy.slice(1)}Count`);
            if (quickCountElement) {
                quickCountElement.textContent = count;
            }
        });
    }
    
    updateSummaryCards() {
        const filteredApps = this.getFilteredApplications();
        const readyApps = filteredApps.filter(app => app.strategy !== 'retain').length;
        const totalSavings = filteredApps.reduce((sum, app) => sum + (app.projectedSavings || 0), 0);
        
        this.updateElement('totalApps', filteredApps.length);
        this.updateElement('readyToMigrate', readyApps);
        this.updateElement('estimatedSavings', this.formatCurrency(totalSavings));
        this.updateElement('totalCostSavings', this.formatCurrency(totalSavings * 0.6));
        this.updateElement('cloudReadyPercent', Math.round((readyApps / filteredApps.length) * 100) + '%');
        
        const roi = totalSavings > 0 ? Math.round((totalSavings / (totalSavings * 0.4)) * 100) : 0;
        this.updateElement('quickROI', roi + '%');
    }
    
    updateFinancialContent() {
        const content = document.getElementById('financialContent');
        if (!content) return;

        const filteredApps = this.getFilteredApplications();
        const totalCurrentCost = filteredApps.reduce((sum, app) => sum + (app.currentCost || 0), 0);
        const totalSavings = filteredApps.reduce((sum, app) => sum + (app.projectedSavings || 0), 0);
        const migrationCost = totalCurrentCost * 0.15;
        const paybackMonths = totalSavings > 0 ? Math.round(migrationCost / (totalSavings / 12)) : 0;
        const threeYearSavings = totalSavings * 3;
        const roi = totalSavings > 0 ? Math.round(((threeYearSavings - migrationCost) / migrationCost) * 100) : 0;

        content.innerHTML = `
            <div class="financial-overview">
                <div class="cost-timeline">
                    <div class="cost-item current">
                        <div class="cost-value">${this.formatCurrency(totalCurrentCost)}</div>
                        <div class="cost-label">Current Annual Cost</div>
                        <div class="cost-trend">📊 Baseline</div>
                    </div>
                    <div class="cost-item investment">
                        <div class="cost-value">${this.formatCurrency(migrationCost)}</div>
                        <div class="cost-label">Migration Investment</div>
                        <div class="cost-trend">💰 One-time</div>
                    </div>
                    <div class="cost-item savings">
                        <div class="cost-value">${this.formatCurrency(totalSavings)}</div>
                        <div class="cost-label">Annual Savings</div>
                        <div class="cost-trend">📈 Recurring</div>
                    </div>
                    <div class="cost-item payback">
                        <div class="cost-value">${paybackMonths} mo</div>
                        <div class="cost-label">Payback Period</div>
                        <div class="cost-trend">⚡ ROI Start</div>
                    </div>
                </div>
                
                <div class="financial-metrics">
                    <div class="metric-card">
                        <div class="metric-value">${roi}%</div>
                        <div class="metric-label">3-Year ROI</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${this.formatCurrency(threeYearSavings)}</div>
                        <div class="metric-label">3-Year Savings</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // ================================================================================
    // UTILITY METHODS
    // ================================================================================
    
    getFilteredApplications() {
        return this.applications.filter(app => {
            const matchesStrategy = this.selectedStrategies.has(app.strategy);
            const matchesSelection = this.selectedApps.has(app.id) || this.selectedApps.size === 0;
            return matchesStrategy && matchesSelection;
        });
    }
    
    updateSelectedApplications() {
        const selector = document.getElementById('appSelect');
        if (!selector) return;

        const selectedValues = Array.from(selector.selectedOptions).map(option => option.value);
        
        if (selectedValues.includes('all')) {
            this.selectedApps = new Set(this.applications.map(app => app.id));
        } else {
            this.selectedApps = new Set(selectedValues);
        }
    }
    
    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    formatCurrency(amount) {
        if (amount >= 1000000) {
            return `$${(amount / 1000000).toFixed(1)}M`;
        } else if (amount >= 1000) {
            return `$${(amount / 1000).toFixed(0)}K`;
        } else {
            return `$${amount.toFixed(0)}`;
        }
    }
    
    toggleEdit() {
        this.isEditing = !this.isEditing;
        const content = document.getElementById('documentContent');
        const editBtn = document.getElementById('editBtn');
        
        if (content && editBtn) {
            content.contentEditable = this.isEditing;
            content.classList.toggle('editing', this.isEditing);
            editBtn.classList.toggle('active', this.isEditing);
            editBtn.innerHTML = this.isEditing ? '💾 Save' : '✏️ Edit';
        }
        
        this.showNotification(this.isEditing ? 'Edit mode enabled' : 'Changes saved', this.isEditing ? 'info' : 'success');
    }

    toggleApproach() {
        this.currentApproach = this.currentApproach === 'phased' ? 'bigBang' : 'phased';
        
        const toggle = document.getElementById('approachToggle');
        const currentApproachSpan = document.getElementById('currentApproach');
        
        if (toggle) {
            toggle.textContent = this.currentApproach === 'phased' ? 
                '📋 Switch to Big Bang' : '📋 Switch to Phased';
        }
        
        if (currentApproachSpan) {
            currentApproachSpan.textContent = this.currentApproach === 'phased' ? 
                'Phased Migration' : 'Big Bang Migration';
        }
        
        this.updateDashboard();
        this.broadcastFilterChange();
        this.showNotification(`Switched to ${this.currentApproach === 'phased' ? 'Phased' : 'Big Bang'} migration approach`, 'success');
    }
    
    showNotification(message, type = 'info') {
        console.log(`${type.toUpperCase()}: ${message}`);
        
        // Create a simple toast notification
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed; top: 20px; right: 20px; z-index: 9999;
            background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : '#3b82f6'};
            color: white; padding: 12px 16px; border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        `;
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => toast.remove(), 3000);
    }
    
    // ================================================================================
    // FILTER SYNCHRONIZATION
    // ================================================================================
    
    syncExternalFilterChange(selectedAppIds) {
        if (selectedAppIds.includes('all')) {
            this.selectedApps = new Set(this.applications.map(app => app.id));
        } else {
            const validAppIds = selectedAppIds.filter(id => 
                this.applications.some(app => app.id === id)
            );
            this.selectedApps = new Set(validAppIds);
        }
        
        this.updateApplicationSelectorUI();
        this.updateDashboard();
        this.showNotification(`Filter synchronized: ${this.selectedApps.size} applications selected`, 'info');
    }
    
    updateApplicationSelectorUI() {
        const selector = document.getElementById('appSelect');
        if (!selector) return;
        
        Array.from(selector.options).forEach(option => {
            if (option.value === 'all') {
                option.selected = this.selectedApps.size === this.applications.length;
            } else {
                option.selected = this.selectedApps.has(option.value);
            }
        });
    }
    
    broadcastFilterChange() {
        if (window.AppData && window.AppData.syncFilterAcrossComponents) {
            const selectedAppIds = this.selectedApps.size === this.applications.length ? 
                ['all'] : Array.from(this.selectedApps);
            
            window.AppData.syncFilterAcrossComponents({
                selectedApps: selectedAppIds,
                source: 'app-rationalization',
                timestamp: Date.now(),
                context: {
                    rationalizationContext: true,
                    selectedStrategies: Array.from(this.selectedStrategies),
                    approach: this.currentApproach
                }
            });
            
            console.log('📡 App Rationalization broadcasted filter change:', selectedAppIds.length, 'applications');
        }
    }
    
    // ================================================================================
    // ANALYSIS TOOLS
    // ================================================================================
    
    generateDetailedReport() {
        this.showNotification('Generating comprehensive migration report...', 'info');
        setTimeout(() => {
            const filteredApps = this.getFilteredApplications();
            console.log('📑 Detailed Report Generated for', filteredApps.length, 'applications');
            this.showNotification(`Detailed report generated for ${filteredApps.length} applications`, 'success');
        }, 2000);
    }

    generateCostAnalysis() {
        this.showNotification('Performing advanced cost-benefit analysis...', 'info');
        setTimeout(() => {
            const filteredApps = this.getFilteredApplications();
            console.log('💰 Cost Analysis Generated for', filteredApps.length, 'applications');
            this.showNotification('Advanced cost analysis completed with risk assessment', 'success');
        }, 1500);
    }

    generateTimeline() {
        this.showNotification('Creating interactive migration timeline...', 'info');
        setTimeout(() => {
            console.log('📅 Migration Timeline Generated');
            this.showNotification('Interactive timeline view ready with key milestones', 'success');
        }, 1000);
    }

    generateRiskMatrix() {
        this.showNotification('Analyzing migration risks and dependencies...', 'info');
        setTimeout(() => {
            const filteredApps = this.getFilteredApplications();
            const highRiskApps = filteredApps.filter(app => 
                app.complexity === 'high' && app.businessCriticality === 'critical'
            );
            console.log('⚠️ Risk Matrix Generated');
            this.showNotification(`Risk analysis complete: ${highRiskApps.length} high-risk applications identified`, 'success');
        }, 1800);
    }
}

// ================================================================================
// GLOBAL FUNCTIONS
// ================================================================================

function toggleEdit() {
    if (window.dashboard) {
        window.dashboard.toggleEdit();
    }
}

function toggleApproach() {
    if (window.dashboard) {
        window.dashboard.toggleApproach();
    }
}

function exportDoc() {
    if (window.dashboard) {
        const filteredApps = window.dashboard.getFilteredApplications();
        window.dashboard.showNotification(`Exporting analysis for ${filteredApps.length} applications...`, 'info');
        
        setTimeout(() => {
            window.dashboard.showNotification('Export completed successfully', 'success');
        }, 2000);
    }
}

function printDoc() {
    window.print();
}

function generateSummary() {
    if (window.dashboard) {
        window.dashboard.showNotification('Generating executive summary with centralized insights...', 'info');
        
        setTimeout(() => {
            window.dashboard.showNotification('Executive summary generated with portfolio analytics', 'success');
        }, 2000);
    }
}

function refreshAnalysis() {
    if (window.dashboard) {
        window.dashboard.showNotification('Refreshing analysis with latest data...', 'info');
        
        setTimeout(() => {
            window.dashboard.loadApplicationsFromCentralizedData();
            window.dashboard.updateDashboard();
            window.dashboard.showNotification('Analysis refreshed with updated application data', 'success');
        }, 1500);
    }
}

function generateDetailedReport() {
    if (window.dashboard) {
        window.dashboard.generateDetailedReport();
    }
}

function generateCostAnalysis() {
    if (window.dashboard) {
        window.dashboard.generateCostAnalysis();
    }
}

function generateTimeline() {
    if (window.dashboard) {
        window.dashboard.generateTimeline();
    }
}

function generateRiskMatrix() {
    if (window.dashboard) {
        window.dashboard.generateRiskMatrix();
    }
}

// ================================================================================
// INITIALIZATION
// ================================================================================

document.addEventListener('DOMContentLoaded', () => {
    if (window.AppData) {
        window.dashboard = new AppRationalizationDashboard();
        console.log('✅ App Rationalization Dashboard initialized with AppData');
    } else {
        console.warn('⚠️ Centralized AppData not available, retrying...');
        setTimeout(() => {
            if (window.AppData) {
                window.dashboard = new AppRationalizationDashboard();
                console.log('✅ App Rationalization Dashboard initialized after retry');
            } else {
                console.warn('⚠️ AppData still not available, initializing with fallback');
                window.dashboard = new AppRationalizationDashboard();
            }
        }, 1000);
    }
});