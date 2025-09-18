// Simplified Network Traffic-Based Archetype Dashboard - Rendering Only
class NetworkBasedArchetypeClassificationDashboard {
    constructor() {
        this.canvas = document.getElementById('appCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.currentView = 'cards';
        this.selectedArchetypes = new Set();
        this.selectedApps = new Set();
        this.searchTerm = '';
        this.selectedApp = null;
        
        // API configuration - matches your FastAPI setup
        this.apiUrl = '/api/v1';
        
        // UI state
        this.isLoading = false;
        this.loadingProgress = 0;
        
        // Data from API - no local processing
        this.applications = [];
        this.filteredApps = [];
        this.archetypes = [];
        this.archetypeDefinitions = {};
        
        this.init();
    }
    
    async init() {
        this.showLoadingSpinner('Loading data from server...');
        
        try {
            // Load data from FastAPI backend
            await this.loadDataFromAPI();
            
            // Setup UI components
            setTimeout(() => {
                this.setupEventListeners();
                this.setupSearchDropdown();
                this.renderArchetypeList();
                this.renderLegend();
                this.updateStats();
                this.setInitialButtonState();
                this.render();
                this.hideLoadingSpinner();
            }, 150);
            
        } catch (error) {
            console.error('Failed to load data:', error);
            this.showError('Failed to load data from server');
            this.hideLoadingSpinner();
        }
        
        // Handle window resize
        window.addEventListener('resize', () => {
            setTimeout(() => {
                if (this.currentView !== 'cards') {
                    this.setupCanvas();
                    this.render();
                }
            }, 100);
        });
    }
    
    async loadDataFromAPI() {
        try {
            this.updateLoadingProgress(20, 'Fetching processed data...');
            
            // Call your existing FastAPI archetype endpoint
            const response = await fetch(`${this.apiUrl}/archetype/data`);
            
            if (!response.ok) {
                throw new Error(`API Error: ${response.status} - ${response.statusText}`);
            }

            const data = await response.json();
            
            this.updateLoadingProgress(60, 'Processing applications...');
            
            // Handle the data structure from your FastAPI backend
            this.applications = data.applications || [];
            this.archetypeDefinitions = data.archetype_definitions || data.definitions || {};
            
            this.updateLoadingProgress(80, 'Generating summaries...');
            
            this.filteredApps = this.applications.slice();
            this.archetypes = this.generateArchetypeSummary();
            
            this.updateLoadingProgress(100, 'Complete!');
            
            console.log(`Loaded ${this.applications.length} applications from FastAPI backend`);
            
        } catch (error) {
            console.error('FastAPI loading error:', error);
            // Fallback to static files if API fails
            console.log('Falling back to static CSV file...');
            await this.loadDataFromStaticFiles();
        }
    }
    
    async loadDataFromStaticFiles() {
        try {
            // Fallback to your mounted static files
            const csvEndpoint = await getCurrentCsvEndpoint();
			if (!csvEndpoint) {
				throw new Error('No CSV data available');
			}
			const csvResponse = await fetch(csvEndpoint);
            const yamlResponse = await fetch('/templates/archetype_templates.yaml');
            
            if (csvResponse.ok && yamlResponse.ok) {
                // Basic parsing for fallback (simplified)
                const csvText = await csvResponse.text();
                const yamlText = await yamlResponse.text();
                
                // Simple demo data creation
                this.applications = this.createDemoApplications();
                this.archetypeDefinitions = this.createDemoArchetypes();
                this.filteredApps = this.applications.slice();
                this.archetypes = this.generateArchetypeSummary();
                
                console.log('Using static file fallback data');
            } else {
                throw new Error('Static files not available');
            }
        } catch (error) {
            console.error('Static file fallback failed:', error);
            // Last resort: demo data
            this.createFallbackData();
        }
    }
    
    createDemoApplications() {
        return [
            {
                id: 'DEMO1',
                name: 'Web Application Demo',
                archetype: '3-Tier',
                color: '#3b82f6',
                status: 'active',
                flow_count: 2500,
                traffic_pattern: 'North-South Layered',
                primary_ports: [{ port: 80, count: 1200 }],
                network_evidence: ['Web traffic', 'Database connectivity'],
                x: Math.random() * 800,
                y: Math.random() * 600
            },
            {
                id: 'DEMO2', 
                name: 'Microservice Demo',
                archetype: 'Microservices',
                color: '#10b981',
                status: 'active',
                flow_count: 3200,
                traffic_pattern: 'East-West Service Communication',
                primary_ports: [{ port: 3000, count: 800 }],
                network_evidence: ['Service mesh', 'Container orchestration'],
                x: Math.random() * 800,
                y: Math.random() * 600
            }
        ];
    }
    
    createDemoArchetypes() {
        return {
            '3-Tier': {
                color: '#3b82f6',
                description: 'Traditional web-app-database architecture',
                traffic_pattern: 'North-South Layered'
            },
            'Microservices': {
                color: '#10b981',
                description: 'Service-oriented architecture',
                traffic_pattern: 'East-West Service Communication'
            }
        };
    }
    
    createFallbackData() {
        console.log('Using minimal fallback data');
        this.applications = this.createDemoApplications();
        this.archetypeDefinitions = this.createDemoArchetypes();
        this.filteredApps = this.applications.slice();
        this.archetypes = this.generateArchetypeSummary();
    }
    
    generateArchetypeSummary() {
        const summary = {};
        
        Object.keys(this.archetypeDefinitions).forEach(archetype => {
            summary[archetype] = {
                name: archetype,
                color: this.archetypeDefinitions[archetype].color,
                count: 0,
                apps: []
            };
        });
        
        this.applications.forEach(app => {
            if (summary[app.archetype]) {
                summary[app.archetype].count++;
                summary[app.archetype].apps.push(app);
            }
        });
        
        return Object.values(summary).filter(archetype => archetype.count > 0);
    }
    
    showLoadingSpinner(message = 'Loading...') {
        this.isLoading = true;
        this.loadingProgress = 0;
        
        let overlay = document.getElementById('loadingOverlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'loadingOverlay';
            overlay.className = 'loading-overlay';
            document.body.appendChild(overlay);
        }
        
        overlay.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner"></div>
                <div class="loading-message">${message}</div>
                <div class="loading-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${this.loadingProgress}%"></div>
                    </div>
                    <div class="progress-text">${this.loadingProgress}%</div>
                </div>
            </div>
        `;
        
        overlay.style.display = 'flex';
    }
    
    updateLoadingProgress(percentage, message) {
        this.loadingProgress = Math.min(100, Math.max(0, percentage));
        
        const overlay = document.getElementById('loadingOverlay');
        if (overlay && this.isLoading) {
            const messageEl = overlay.querySelector('.loading-message');
            const progressFill = overlay.querySelector('.progress-fill');
            const progressText = overlay.querySelector('.progress-text');
            
            if (messageEl && message) messageEl.textContent = message;
            if (progressFill) progressFill.style.width = `${this.loadingProgress}%`;
            if (progressText) progressText.textContent = `${Math.round(this.loadingProgress)}%`;
        }
    }
    
    hideLoadingSpinner() {
        this.isLoading = false;
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }
    
    showError(message) {
        const toast = document.createElement('div');
        toast.className = 'error-toast';
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #dc2626;
            color: white;
            padding: 12px 16px;
            border-radius: 8px;
            z-index: 10001;
            font-size: 14px;
            max-width: 400px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        `;
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => toast.remove(), 5000);
    }
    
    setupSearchDropdown() {
        const searchInput = document.getElementById('archetypeSearch');
        const searchContainer = document.querySelector('.search-container');
        
        if (!searchInput || !searchContainer) return;
        
        const dropdown = document.createElement('div');
        dropdown.className = 'search-dropdown';
        dropdown.id = 'searchDropdown';
        
        const selectedContainer = document.createElement('div');
        selectedContainer.className = 'selected-apps-container';
        selectedContainer.innerHTML = `
            <div class="selected-apps-title">Selected Applications</div>
            <div class="selected-apps-list" id="selectedAppsList"></div>
            <button class="clear-all-btn" onclick="clearAllSelectedApps()">Clear All</button>
        `;
        
        searchContainer.appendChild(dropdown);
        searchContainer.appendChild(selectedContainer);
        
        searchInput.addEventListener('input', (e) => {
            this.handleSearchInput(e.target.value);
        });
        
        searchInput.addEventListener('focus', () => {
            this.showSearchDropdown();
        });
        
        document.addEventListener('click', (e) => {
            if (!searchContainer.contains(e.target)) {
                this.hideSearchDropdown();
            }
        });
        
        this.updateSelectedAppsDisplay();
    }
    
    handleSearchInput(query) {
        this.searchTerm = query.toLowerCase();
        this.updateSearchDropdown();
        this.applyFilters();
    }
    
    updateSearchDropdown() {
        const dropdown = document.getElementById('searchDropdown');
        if (!dropdown) return;
        
        const filteredApps = this.searchTerm ? 
            this.applications.filter(app => 
                app.name.toLowerCase().includes(this.searchTerm) ||
                app.id.toLowerCase().includes(this.searchTerm) ||
                app.archetype.toLowerCase().includes(this.searchTerm)
            ) : this.applications;
        
        const groupedApps = {};
        filteredApps.forEach(app => {
            if (!groupedApps[app.archetype]) {
                groupedApps[app.archetype] = [];
            }
            groupedApps[app.archetype].push(app);
        });
        
        let dropdownHTML = '';
        
        if (this.searchTerm) {
            dropdownHTML += `
                <div class="dropdown-section">
                    <div class="dropdown-item" onclick="selectAllFilteredApps()">
                        <span>📋</span>
                        <span>Select All (${filteredApps.length} apps)</span>
                    </div>
                </div>
            `;
        }
        
        Object.entries(groupedApps).forEach(([archetype, apps]) => {
            const archetypeInfo = this.archetypeDefinitions[archetype];
            dropdownHTML += `
                <div class="dropdown-section">
                    <div class="dropdown-header">
                        ${archetype} (${apps.length})
                    </div>
            `;
            
            apps.forEach(app => {
                const isSelected = this.selectedApps.has(app.id);
                const flowCount = app.flow_count || 0;
                
                dropdownHTML += `
                    <div class="dropdown-item ${isSelected ? 'selected' : ''}" onclick="toggleAppSelection('${app.id}')">
                        <div class="app-indicator" style="background-color: ${archetypeInfo?.color || '#64748b'}"></div>
                        <div style="flex-grow: 1;">
                            <div style="font-weight: 600;">${app.name}</div>
                            <div style="font-size: 10px; color: #94a3b8;">
                                ${app.id} • ${flowCount} flows • ${app.status}
                            </div>
                        </div>
                    </div>
                `;
            });
            
            dropdownHTML += '</div>';
        });
        
        if (dropdownHTML === '') {
            dropdownHTML = '<div class="dropdown-item">No applications found</div>';
        }
        
        dropdown.innerHTML = dropdownHTML;
    }
    
    showSearchDropdown() {
        this.updateSearchDropdown();
        const dropdown = document.getElementById('searchDropdown');
        if (dropdown) {
            dropdown.classList.add('show');
        }
    }
    
    hideSearchDropdown() {
        const dropdown = document.getElementById('searchDropdown');
        if (dropdown) {
            dropdown.classList.remove('show');
        }
    }
    
    updateSelectedAppsDisplay() {
        const container = document.querySelector('.selected-apps-container');
        const list = document.getElementById('selectedAppsList');
        
        if (!container || !list) return;
        
        if (this.selectedApps.size === 0) {
            container.classList.remove('show');
            return;
        }
        
        container.classList.add('show');
        
        const selectedAppsArray = Array.from(this.selectedApps).map(id => 
            this.applications.find(app => app.id === id)
        ).filter(Boolean);
        
        let tagsHTML = '';
        selectedAppsArray.forEach(app => {
            tagsHTML += `<div class="selected-app-tag"><span>${app.name}</span><button class="remove-btn" onclick="removeAppSelection('${app.id}')">×</button></div>`;
        });
        
        list.innerHTML = tagsHTML;
    }
    
    toggleAppSelection(appId) {
        if (this.selectedApps.has(appId)) {
            this.selectedApps.delete(appId);
        } else {
            this.selectedApps.add(appId);
        }
        
        this.updateSearchDropdown();
        this.updateSelectedAppsDisplay();
        this.applyFilters();
    }
    
    selectAllFilteredApps() {
        const filteredApps = this.searchTerm ? 
            this.applications.filter(app => 
                app.name.toLowerCase().includes(this.searchTerm) ||
                app.archetype.toLowerCase().includes(this.searchTerm)
            ) : this.applications;
        
        filteredApps.forEach(app => {
            this.selectedApps.add(app.id);
        });
        
        this.updateSearchDropdown();
        this.updateSelectedAppsDisplay();
        this.applyFilters();
        this.hideSearchDropdown();
    }
    
    clearAllSelectedApps() {
        this.selectedApps.clear();
        this.updateSearchDropdown();
        this.updateSelectedAppsDisplay();
        this.applyFilters();
    }
    
    removeAppSelection(appId) {
        this.selectedApps.delete(appId);
        this.updateSearchDropdown();
        this.updateSelectedAppsDisplay();
        this.applyFilters();
    }
    
    setInitialButtonState() {
        document.querySelectorAll('.view-controls .btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        const cardsBtn = document.getElementById('cardsBtn');
        if (cardsBtn) {
            cardsBtn.classList.add('active');
        }
    }
    
    setupCanvas() {
        if (!this.canvas || this.currentView === 'cards') return;
        
        const rect = this.canvas.getBoundingClientRect();
        
        if (rect.width === 0 || rect.height === 0) {
            // Set fallback dimensions
            this.canvasWidth = 800;
            this.canvasHeight = 600;
        } else {
            this.canvas.width = rect.width * window.devicePixelRatio;
            this.canvas.height = rect.height * window.devicePixelRatio;
            this.ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
            this.canvasWidth = rect.width;
            this.canvasHeight = rect.height;
        }
        
        this.canvas.style.width = this.canvasWidth + 'px';
        this.canvas.style.height = this.canvasHeight + 'px';
    }
    
    setupEventListeners() {
        if (this.canvas) {
            this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
            this.canvas.addEventListener('click', (e) => this.handleClick(e));
            this.canvas.addEventListener('mouseleave', () => this.hideAppDetails());
        }
    }
    
    render() {
        this.filteredApps = this.applications.filter(app => {
            const matchesSearch = this.searchTerm === '' || 
                app.name.toLowerCase().includes(this.searchTerm) ||
                app.id.toLowerCase().includes(this.searchTerm) ||
                app.archetype.toLowerCase().includes(this.searchTerm);
            
            const matchesArchetype = this.selectedArchetypes.size === 0 || 
                this.selectedArchetypes.has(app.archetype);
            
            const matchesAppSelection = this.selectedApps.size === 0 || 
                this.selectedApps.has(app.id);
            
            return matchesSearch && matchesArchetype && matchesAppSelection;
        });
        
        if (this.currentView === 'cards') {
            this.renderArchetypeCards();
        } else {
            this.renderCanvasView();
        }
        
        this.updateStats();
    }
    
    renderArchetypeCards() {
        const canvas = document.getElementById('appCanvas');
        const container = canvas.parentElement;
        
        canvas.style.display = 'none';
        
        let cardsContainer = container.querySelector('.archetype-cards-container');
        if (!cardsContainer) {
            cardsContainer = document.createElement('div');
            cardsContainer.className = 'archetype-cards-container';
            container.appendChild(cardsContainer);
        }
        
        cardsContainer.style.display = 'grid';
        cardsContainer.style.gridTemplateColumns = 'repeat(3, 1fr)';
        cardsContainer.style.gap = '16px';
        cardsContainer.style.padding = '16px';
        cardsContainer.style.height = 'calc(100% - 80px)';
        cardsContainer.style.overflowY = 'auto';
        
        const archetypeGroups = {};
        this.filteredApps.forEach(app => {
            if (!archetypeGroups[app.archetype]) {
                archetypeGroups[app.archetype] = [];
            }
            archetypeGroups[app.archetype].push(app);
        });
        
        cardsContainer.innerHTML = '';
        this.archetypes.forEach(archetype => {
            const apps = archetypeGroups[archetype.name] || [];
            if (apps.length === 0) return;
            
            const card = this.createArchetypeCard(archetype, apps);
            cardsContainer.appendChild(card);
        });
    }
    
    createArchetypeCard(archetype, apps) {
        const card = document.createElement('div');
        card.className = 'archetype-card';
        card.style.borderLeftColor = archetype.color;
        
        const activeApps = apps.filter(app => app.status === 'active').length;
        const definition = this.archetypeDefinitions[archetype.name];
        const totalFlows = apps.reduce((sum, app) => sum + (app.flow_count || 0), 0);
        const avgFlowsPerApp = Math.round(totalFlows / apps.length);
        
        const applicationsGridHTML = apps.map(app => this.createAppNode(app)).join('');
        const evidenceHTML = apps[0]?.network_evidence?.slice(0, 3).map(evidence => 
            `<span class="pattern-tag">${evidence}</span>`
        ).join('') || '';
        
        const trafficPatterns = [...new Set(apps.map(app => app.traffic_pattern))];
        const trafficPatternsHTML = trafficPatterns.map(pattern => 
            `<span class="traffic-pattern-tag">${pattern}</span>`
        ).join('');
        
        card.innerHTML = `
            <div class="archetype-card-header">
                <div class="archetype-card-title">
                    <div class="archetype-icon" style="background-color: ${archetype.color}"></div>
                    <h3>${archetype.name}</h3>
                </div>
                <div class="archetype-count">${apps.length}</div>
            </div>
            <div class="archetype-stats">
                <div class="stat-row">
                    <span>Active:</span>
                    <span class="stat-value active">${activeApps}/${apps.length}</span>
                </div>
                <div class="stat-row">
                    <span>Avg Flows:</span>
                    <span class="stat-value">${avgFlowsPerApp.toLocaleString()}</span>
                </div>
                <div class="stat-row">
                    <span>Pattern:</span>
                    <span class="stat-value">${definition?.traffic_pattern || 'Unknown'}</span>
                </div>
            </div>
            <div class="applications-grid">${applicationsGridHTML}</div>
            <div class="traffic-pattern-tags">
                <div class="traffic-pattern-title">Traffic Patterns:</div>
                <div class="traffic-pattern-list">${trafficPatternsHTML}</div>
            </div>
            <div class="archetype-patterns">
                <div class="pattern-title">Network Evidence:</div>
                <div class="pattern-list">${evidenceHTML}</div>
            </div>
        `;
        
        card.addEventListener('click', (e) => {
            if (e.target.classList.contains('app-node')) {
                const appId = e.target.dataset.appId;
                const app = apps.find(a => a.id === appId);
                if (app) {
                    this.showAppDetails(app, e.target);
                }
            }
        });
        
        return card;
    }
    
    createAppNode(app) {
        const statusClass = app.status === 'active' ? 'active' : 
                           app.status === 'migrating' ? 'migrating' : 'inactive';
        
        const flowVolume = app.flow_count > 4000 ? 'high' : app.flow_count > 2000 ? 'medium' : 'low';
        
        return `<div class="app-node ${statusClass} flow-${flowVolume}" data-app-id="${app.id}" 
                     style="background-color: ${app.color}" 
					 title="${app.name} • ${(app.flow_count || 0).toLocaleString()} flows • Ports: ${app.primary_ports?.length ? app.primary_ports.map(p => `${p.port}(${p.count})`).join(', ') : 'No ports'} • Pattern: ${app.traffic_pattern || 'Unknown'}">
                    <div class="app-node-inner"></div>
                </div>`;
    }
    
    renderCanvasView() {
        const canvas = document.getElementById('appCanvas');
        const container = canvas.parentElement;
        
        canvas.style.display = 'block';
        const cardsContainer = container.querySelector('.archetype-cards-container');
        if (cardsContainer) {
            cardsContainer.style.display = 'none';
        }
        
        this.setupCanvas();
        
        if (this.canvasWidth > 0 && this.canvasHeight > 0) {
            requestAnimationFrame(() => {
                this.positionApplications();
                this.drawVisualization();
            });
        }
    }
    
    positionApplications() {
        if (!this.filteredApps || this.filteredApps.length === 0) return;
        
        const margin = 50;
        const width = Math.max(400, this.canvasWidth - 2 * margin);
        const height = Math.max(300, this.canvasHeight - 2 * margin);
        
        // Simple positioning based on current view
        switch (this.currentView) {
            case 'cluster':
                this.positionClusterView(margin, width, height);
                break;
            case 'network':
                this.positionNetworkView(margin, width, height);
                break;
            case 'hierarchy':
                this.positionHierarchyView(margin, width, height);
                break;
        }
    }
    
    positionClusterView(margin, width, height) {
        const archetypeGroups = {};
        this.filteredApps.forEach(app => {
            if (!archetypeGroups[app.archetype]) {
                archetypeGroups[app.archetype] = [];
            }
            archetypeGroups[app.archetype].push(app);
        });
        
        const groupNames = Object.keys(archetypeGroups);
        const cols = Math.ceil(Math.sqrt(groupNames.length));
        const rows = Math.ceil(groupNames.length / cols);
        
        groupNames.forEach((groupName, index) => {
            const row = Math.floor(index / cols);
            const col = index % cols;
            
            const centerX = margin + (col + 0.5) * (width / cols);
            const centerY = margin + (row + 0.5) * (height / rows);
            const radius = Math.min(width / cols, height / rows) * 0.3;
            
            const apps = archetypeGroups[groupName];
            apps.forEach((app, appIndex) => {
                const angle = (appIndex / apps.length) * 2 * Math.PI;
                const distance = Math.random() * radius;
                app.x = centerX + Math.cos(angle) * distance;
                app.y = centerY + Math.sin(angle) * distance;
            });
        });
    }
    
    positionNetworkView(margin, width, height) {
        // Similar positioning logic but simplified
        const centerX = margin + width / 2;
        const centerY = margin + height / 2;
        
        this.filteredApps.forEach((app, index) => {
            const angle = (index / this.filteredApps.length) * 2 * Math.PI;
            const radius = Math.min(width, height) * 0.4;
            app.x = centerX + Math.cos(angle) * radius;
            app.y = centerY + Math.sin(angle) * radius;
        });
    }
    
    positionHierarchyView(margin, width, height) {
        // Simple layered positioning
        const layers = {};
        this.filteredApps.forEach((app, index) => {
            const layer = index % 4; // Simple layering
            if (!layers[layer]) layers[layer] = [];
            layers[layer].push(app);
        });
        
        Object.keys(layers).forEach(layer => {
            const apps = layers[layer];
            const y = margin + (parseInt(layer) + 0.5) * (height / 4);
            
            apps.forEach((app, index) => {
                app.x = margin + (index + 1) * (width / (apps.length + 1));
                app.y = y;
            });
        });
    }
    
    drawVisualization() {
        if (!this.ctx || !this.canvasWidth || !this.canvasHeight) return;
        
        this.ctx.clearRect(0, 0, this.canvasWidth, this.canvasHeight);
        
        // Draw background
        this.ctx.fillStyle = '#0f172a';
        this.ctx.fillRect(0, 0, this.canvasWidth, this.canvasHeight);
        
        // Draw applications
        if (this.filteredApps && this.filteredApps.length > 0) {
            this.filteredApps.forEach(app => {
                this.drawApplication(app);
            });
        }
    }
    
    drawApplication(app) {
        const isSelected = this.selectedApp === app;
        const baseRadius = 6;
        const radius = baseRadius + (isSelected ? 3 : 0);
        
        this.ctx.beginPath();
        this.ctx.arc(app.x, app.y, radius, 0, 2 * Math.PI);
        this.ctx.fillStyle = app.color;
        this.ctx.fill();
        
        this.ctx.strokeStyle = isSelected ? '#ffffff' : '#ffffff';
        this.ctx.lineWidth = isSelected ? 3 : 2;
        this.ctx.stroke();
    }
    
    showAppDetails(app, element) {
		// Remove any existing detail popups
		const existingPopup = document.querySelector('.app-detail-popup');
		if (existingPopup) {
			existingPopup.remove();
		}
		
		// Create floating detail popup
		const popup = document.createElement('div');
		popup.className = 'app-detail-popup';
		popup.style.cssText = `
			position: fixed;
			background: white;
			border: 1px solid #e5e7eb;
			border-radius: 8px;
			padding: 16px;
			box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
			z-index: 1000;
			max-width: 350px;
			font-size: 14px;
			line-height: 1.4;
		`;
		
		// Format ports with counts
		const formatPorts = (ports) => {
			if (!ports || ports.length === 0) return 'No port data';
			return ports
				.sort((a, b) => (b.count || 0) - (a.count || 0))
				.slice(0, 5)
				.map(p => `${p.port} (${p.count} flows)`)
				.join(', ');
		};
		
		// Format evidence
		const formatEvidence = (evidence) => {
			if (!evidence || evidence.length === 0) return 'No evidence available';
			return evidence.slice(0, 3).map(e => `• ${e}`).join('<br>');
		};
		
		popup.innerHTML = `
			<button onclick="this.parentElement.remove()" style="position: absolute; top: 8px; right: 12px; background: none; border: none; font-size: 18px; cursor: pointer; color: #666;">×</button>
			
			<div style="font-weight: bold; font-size: 16px; margin-bottom: 12px; color: #1f2937; padding-right: 20px;">
				${app.name}
			</div>
			
			<div style="background: #f8fafc; padding: 8px; border-radius: 6px; margin-bottom: 12px;">
				<div style="font-weight: 600; color: #374151; margin-bottom: 8px;">Architecture Details</div>
				<div style="display: grid; grid-template-columns: 1fr 2fr; gap: 6px; font-size: 13px;">
					<div style="color: #6b7280;">Type:</div>
					<div style="font-weight: 500;">${app.archetype}</div>
					
					<div style="color: #6b7280;">Status:</div>
					<div style="font-weight: 500; color: ${app.status === 'active' ? '#059669' : '#d97706'};">${app.status}</div>
					
					<div style="color: #6b7280;">Traffic Flows:</div>
					<div style="font-weight: 500;">${(app.flow_count || 0).toLocaleString()}</div>
					
					<div style="color: #6b7280;">Pattern:</div>
					<div style="font-weight: 500; font-size: 12px;">${app.traffic_pattern || 'Standard Communication'}</div>
				</div>
			</div>
			
			<div style="margin-bottom: 12px;">
				<div style="font-weight: 600; color: #374151; margin-bottom: 6px;">Primary Ports</div>
				<div style="background: #fef3c7; padding: 8px; border-radius: 4px; font-family: monospace; font-size: 12px; color: #92400e;">
					${formatPorts(app.primary_ports)}
				</div>
			</div>
			
			<div>
				<div style="font-weight: 600; color: #374151; margin-bottom: 6px;">Network Evidence</div>
				<div style="font-size: 12px; color: #4b5563; line-height: 1.5;">
					${formatEvidence(app.network_evidence)}
				</div>
			</div>
		`;
		
		document.body.appendChild(popup);
		
		// Position popup near the clicked element
		const rect = element.getBoundingClientRect();
		const popupRect = popup.getBoundingClientRect();
		
		let left = rect.right + 10;
		let top = rect.top;
		
		// Keep popup on screen
		if (left + popupRect.width > window.innerWidth) {
			left = rect.left - popupRect.width - 10;
		}
		if (top + popupRect.height > window.innerHeight) {
			top = window.innerHeight - popupRect.height - 10;
		}
		
		popup.style.left = `${Math.max(10, left)}px`;
		popup.style.top = `${Math.max(10, top)}px`;
		
		// Auto-hide after 15 seconds
		setTimeout(() => {
			if (popup.parentElement) popup.remove();
		}, 15000);
	}
    
    hideAppDetails() {
        const details = document.getElementById('appDetails');
        if (details) {
            details.classList.remove('visible');
        }
    }
    
    renderArchetypeList() {
        const container = document.getElementById('archetypeList');
        if (!container) return;
        
        container.innerHTML = '';
        
        this.archetypes.forEach(archetype => {
            const item = document.createElement('div');
            item.className = 'archetype-item';
            item.onclick = () => this.toggleArchetype(archetype.name);
            
            const visibleCount = this.filteredApps.filter(app => app.archetype === archetype.name).length;
            
            item.innerHTML = `<div class="archetype-name"><div class="archetype-color" style="background-color: ${archetype.color}"></div><span>${archetype.name}</span></div><div class="archetype-count">${visibleCount}</div>`;
            
            container.appendChild(item);
        });
    }
    
    renderLegend() {
        const container = document.getElementById('archetypeLegend');
        if (!container) return;
        
        container.innerHTML = '';
        
        this.archetypes.forEach(archetype => {
            const item = document.createElement('div');
            item.className = 'legend-item';
            item.innerHTML = `<div class="legend-color" style="background-color: ${archetype.color}"></div><span>${archetype.name}</span>`;
            container.appendChild(item);
        });
    }
    
    toggleArchetype(archetypeName) {
        if (this.selectedArchetypes.has(archetypeName)) {
            this.selectedArchetypes.delete(archetypeName);
        } else {
            this.selectedArchetypes.add(archetypeName);
        }
        this.applyFilters();
        this.updateArchetypeSelection();
    }
    
    updateArchetypeSelection() {
        const items = document.querySelectorAll('.archetype-item');
        items.forEach((item, index) => {
            const archetypeName = this.archetypes[index].name;
            if (this.selectedArchetypes.has(archetypeName)) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }
    
    applyFilters() {
        this.render();
    }
    
    updateStats() {
        const totalApps = document.getElementById('totalApps');
        const classifiedApps = document.getElementById('classifiedApps');
        const archetypeCount = document.getElementById('archetypeCount');
        const visibleApps = document.getElementById('visibleApps');
        
        if (totalApps) totalApps.textContent = this.applications.length;
        if (classifiedApps) classifiedApps.textContent = this.applications.filter(app => app.archetype).length;
        if (archetypeCount) archetypeCount.textContent = this.archetypes.length;
        if (visibleApps) visibleApps.textContent = this.filteredApps.length;
    }
    
    handleMouseMove(e) {
        // Simple mouse handling for canvas views
    }
    
    handleClick(e) {
        // Simple click handling for canvas views
    }
}

// Global functions for UI interaction
window.toggleAppSelection = function(appId) {
    if (window.dashboard) {
        window.dashboard.toggleAppSelection(appId);
    }
};

window.selectAllFilteredApps = function() {
    if (window.dashboard) {
        window.dashboard.selectAllFilteredApps();
    }
};

window.clearAllSelectedApps = function() {
    if (window.dashboard) {
        window.dashboard.clearAllSelectedApps();
    }
};

window.removeAppSelection = function(appId) {
    if (window.dashboard) {
        window.dashboard.removeAppSelection(appId);
    }
};

window.setView = function(viewType) {
    if (window.dashboard) {
        console.log(`Switching to ${viewType} view`);
        window.dashboard.currentView = viewType;
        
        document.querySelectorAll('.view-controls .btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        const targetBtn = document.getElementById(viewType + 'Btn');
        if (targetBtn) targetBtn.classList.add('active');
        
        setTimeout(() => {
            window.dashboard.render();
        }, 50);
    }
};

window.resetFilters = function() {
    if (window.dashboard) {
        window.dashboard.selectedArchetypes.clear();
        window.dashboard.selectedApps.clear();
        window.dashboard.searchTerm = '';
        const searchInput = document.getElementById('archetypeSearch');
        if (searchInput) {
            searchInput.value = '';
        }
        window.dashboard.applyFilters();
        window.dashboard.updateArchetypeSelection();
        window.dashboard.updateSelectedAppsDisplay();
    }
};

// Legacy function definitions for backward compatibility
function toggleAppSelection(appId) { window.toggleAppSelection(appId); }
function selectAllFilteredApps() { window.selectAllFilteredApps(); }
function clearAllSelectedApps() { window.clearAllSelectedApps(); }
function removeAppSelection(appId) { window.removeAppSelection(appId); }
function setView(viewType) { window.setView(viewType); }
function resetFilters() { window.resetFilters(); }

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    window.dashboard = new NetworkBasedArchetypeClassificationDashboard();
});