class EnhancedTopologyFilters {
    constructor(topologyDashboard) {
        this.dashboard = topologyDashboard;
        this.currentFilters = {
            selectedApps: ['all'],
            archetype: 'all',
            businessFunction: 'all',
            criticality: 'all',
            searchQuery: '',
            showUpstream: false,
            showDownstream: false
        };
    }

    // ================================================================================
    // ENHANCED APPLICATION FILTER SETUP
    // ================================================================================
    
    setupEnhancedApplicationFilter() {
        const leftPanel = document.getElementById('left-panel');
        if (!leftPanel) return;
        
        // Remove existing filter section if present
        const existingFilter = leftPanel.querySelector('.filter-section');
        if (existingFilter) {
            existingFilter.remove();
        }
        
        const filterSection = document.createElement('div');
        filterSection.className = 'filter-section enhanced-filters';
        filterSection.innerHTML = `
            <h4>🎯 Enhanced Application Filters</h4>
            
            <!-- Search across all applications -->
            <div class="filter-group">
                <label class="filter-label">🔍 Search Applications</label>
                <input type="text" 
                       id="app-search-enhanced" 
                       class="filter-input" 
                       placeholder="Search by name, archetype, business function..." 
                       style="width: 100%; margin-bottom: 8px;">
                <div id="search-results-count" class="filter-stats"></div>
            </div>
            
            <!-- Multi-dimensional filters -->
            <div class="filter-group">
                <label class="filter-label">🏗️ Architecture Type</label>
                <select id="archetype-filter" class="filter-select">
                    <option value="all">All Archetypes</option>
                    <!-- Will be populated dynamically -->
                </select>
            </div>
            
            <div class="filter-group">
                <label class="filter-label">🏢 Business Function</label>
                <select id="business-function-filter" class="filter-select">
                    <option value="all">All Functions</option>
                    <!-- Will be populated dynamically -->
                </select>
            </div>
            
            <div class="filter-group">
                <label class="filter-label">⚡ Criticality Level</label>
                <select id="criticality-filter" class="filter-select">
                    <option value="all">All Levels</option>
                    <option value="critical">Critical</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                </select>
            </div>
            
            <!-- Main application selector with enhanced grouping -->
            <div class="filter-group">
                <label class="filter-label">📱 Select Applications</label>
                <select id="app-filter-enhanced" 
                        class="filter-select" 
                        multiple 
                        size="8" 
                        style="height: 160px;">
                    <option value="all" selected>🔄 Loading Applications...</option>
                </select>
                
                <!-- Quick selection buttons -->
                <div class="quick-filter-buttons" style="margin-top: 8px; display: grid; grid-template-columns: 1fr 1fr; gap: 4px;">
                    <button class="filter-btn-small" onclick="selectAllAppsEnhanced()">All</button>
                    <button class="filter-btn-small" onclick="clearAllAppsEnhanced()">None</button>
                    <button class="filter-btn-small" onclick="selectCriticalAppsEnhanced()">Critical</button>
                    <button class="filter-btn-small" onclick="selectByCurrentFilters()">Filtered</button>
                </div>
            </div>
            
            <!-- Dependency options -->
            <div class="filter-group">
                <label class="filter-label">🔄 Include Dependencies</label>
                <div class="checkbox-group">
                    <label class="checkbox-label">
                        <input type="checkbox" id="show-upstream-enhanced">
                        ⬆️ Upstream (Providers)
                    </label>
                    <label class="checkbox-label">
                        <input type="checkbox" id="show-downstream-enhanced">
                        ⬇️ Downstream (Consumers)
                    </label>
                </div>
            </div>
            
            <!-- Apply filters button -->
            <button class="filter-btn-apply" onclick="applyEnhancedFilters()" style="width: 100%; margin-top: 12px;">
                🔍 Apply Enhanced Filters
            </button>
            
            <!-- Filter summary -->
            <div id="enhanced-filter-stats" class="filter-summary" style="margin-top: 8px;">
                Ready to filter applications...
            </div>
            
            <!-- Quick reset -->
            <button class="filter-btn-reset" onclick="resetAllFilters()" style="width: 100%; margin-top: 8px;">
                🔄 Reset All Filters
            </button>
        `;
        
        // Insert the enhanced filter section
        const firstInfo = leftPanel.querySelector('.info-panel');
        if (firstInfo) {
            leftPanel.insertBefore(filterSection, firstInfo.nextSibling);
        } else {
            leftPanel.appendChild(filterSection);
        }
        
        this.setupEnhancedEventListeners();
        this.populateEnhancedFilters();
        
        console.log('✅ Enhanced application filters setup complete');
    }

    setupEnhancedEventListeners() {
        // Enhanced search with real-time filtering
        const searchInput = document.getElementById('app-search-enhanced');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.handleSearchInput(e.target.value);
                }, 300);
            });
        }
        
        // Archetype filter
        const archetypeFilter = document.getElementById('archetype-filter');
        if (archetypeFilter) {
            archetypeFilter.addEventListener('change', (e) => {
                this.currentFilters.archetype = e.target.value;
                this.updateApplicationList();
            });
        }
        
        // Business function filter
        const businessFunctionFilter = document.getElementById('business-function-filter');
        if (businessFunctionFilter) {
            businessFunctionFilter.addEventListener('change', (e) => {
                this.currentFilters.businessFunction = e.target.value;
                this.updateApplicationList();
            });
        }
        
        // Criticality filter
        const criticalityFilter = document.getElementById('criticality-filter');
        if (criticalityFilter) {
            criticalityFilter.addEventListener('change', (e) => {
                this.currentFilters.criticality = e.target.value;
                this.updateApplicationList();
            });
        }
        
        // Application selector
        const appFilter = document.getElementById('app-filter-enhanced');
        if (appFilter) {
            appFilter.addEventListener('change', () => {
                this.updateSelectedApps();
            });
        }
        
        // Dependency checkboxes
        const upstreamCheck = document.getElementById('show-upstream-enhanced');
        const downstreamCheck = document.getElementById('show-downstream-enhanced');
        
        if (upstreamCheck) {
            upstreamCheck.addEventListener('change', (e) => {
                this.currentFilters.showUpstream = e.target.checked;
                this.updateFilterStats();
            });
        }
        
        if (downstreamCheck) {
            downstreamCheck.addEventListener('change', (e) => {
                this.currentFilters.showDownstream = e.target.checked;
                this.updateFilterStats();
            });
        }
    }

    populateEnhancedFilters() {
        if (!window.AppData || !window.AppData.isDataLoaded) {
            console.warn('⚠️ AppData not ready for enhanced filter population');
            setTimeout(() => this.populateEnhancedFilters(), 500);
            return;
        }
        
        const apps = window.AppData.getApplicationNamesForFilter();
        console.log('📊 Populating enhanced filters with', apps.length, 'applications');
        
        // Populate archetype filter
        this.populateArchetypeFilter(apps);
        
        // Populate business function filter
        this.populateBusinessFunctionFilter(apps);
        
        // Populate main application list
        this.updateApplicationList();
        
        console.log('✅ Enhanced filters populated successfully');
    }

    populateArchetypeFilter(apps) {
        const archetypeFilter = document.getElementById('archetype-filter');
        if (!archetypeFilter) return;
        
        const archetypes = [...new Set(apps.map(app => app.archetype).filter(a => a && a !== 'All'))];
        archetypes.sort();
        
        // Clear existing options except "All"
        archetypeFilter.innerHTML = '<option value="all">All Archetypes</option>';
        
        archetypes.forEach(archetype => {
            const count = apps.filter(app => app.archetype === archetype).length;
            const option = document.createElement('option');
            option.value = archetype;
            option.textContent = `${archetype} (${count})`;
            archetypeFilter.appendChild(option);
        });
        
        console.log(`📊 Populated ${archetypes.length} archetypes`);
    }

    populateBusinessFunctionFilter(apps) {
        const businessFunctionFilter = document.getElementById('business-function-filter');
        if (!businessFunctionFilter) return;
        
        const functions = [...new Set(apps.map(app => app.businessFunction).filter(f => f && f !== 'All'))];
        functions.sort();
        
        // Clear existing options except "All"
        businessFunctionFilter.innerHTML = '<option value="all">All Functions</option>';
        
        functions.forEach(func => {
            const count = apps.filter(app => app.businessFunction === func).length;
            const option = document.createElement('option');
            option.value = func;
            option.textContent = `${func} (${count})`;
            businessFunctionFilter.appendChild(option);
        });
        
        console.log(`📊 Populated ${functions.length} business functions`);
    }

    updateApplicationList() {
        if (!window.AppData || !window.AppData.isDataLoaded) return;
        
        const appFilter = document.getElementById('app-filter-enhanced');
        if (!appFilter) return;
        
        // Get all applications
        let apps = window.AppData.getApplicationNamesForFilter();
        
        // Apply current filters
        apps = this.applyCurrentFilters(apps);
        
        // Group applications for better organization
        const grouped = this.groupApplicationsEnhanced(apps.filter(app => app.id !== 'all'));
        
        // Clear and rebuild the list
        appFilter.innerHTML = '';
        
        // Add "All" option
        const allOption = document.createElement('option');
        allOption.value = 'all';
        allOption.textContent = `ALL Applications (${apps.length - 1})`;
        allOption.selected = this.currentFilters.selectedApps.includes('all');
        appFilter.appendChild(allOption);
        
        // Add grouped applications
        Object.entries(grouped).forEach(([groupName, groupApps]) => {
            if (groupApps.length === 0) return;
            
            const optgroup = document.createElement('optgroup');
            optgroup.label = `${groupName} (${groupApps.length})`;
            
            groupApps.forEach(app => {
                const option = document.createElement('option');
                option.value = app.id;
                option.textContent = this.formatApplicationOption(app);
                option.selected = this.currentFilters.selectedApps.includes(app.id);
                
                // Add metadata for enhanced filtering
                option.dataset.archetype = app.archetype || '';
                option.dataset.businessFunction = app.businessFunction || '';
                option.dataset.criticality = app.criticality || '';
                option.dataset.recordCount = app.recordCount || 0;
                
                // Color code by criticality
                if (app.criticality === 'critical') {
                    option.style.color = '#ef4444';
                    option.style.fontWeight = 'bold';
                } else if (app.criticality === 'high') {
                    option.style.color = '#f59e0b';
                }
                
                optgroup.appendChild(option);
            });
            
            appFilter.appendChild(optgroup);
        });
        
        this.updateFilterStats();
    }

    applyCurrentFilters(apps) {
        let filtered = apps;
        
        // Apply search query
        if (this.currentFilters.searchQuery) {
            const query = this.currentFilters.searchQuery.toLowerCase();
            filtered = filtered.filter(app => 
                app.searchText?.includes(query) ||
                app.name.toLowerCase().includes(query) ||
                app.displayName?.toLowerCase().includes(query) ||
                app.archetype?.toLowerCase().includes(query) ||
                app.businessFunction?.toLowerCase().includes(query)
            );
        }
        
        // Apply archetype filter
        if (this.currentFilters.archetype !== 'all') {
            filtered = filtered.filter(app => app.archetype === this.currentFilters.archetype);
        }
        
        // Apply business function filter
        if (this.currentFilters.businessFunction !== 'all') {
            filtered = filtered.filter(app => app.businessFunction === this.currentFilters.businessFunction);
        }
        
        // Apply criticality filter
        if (this.currentFilters.criticality !== 'all') {
            filtered = filtered.filter(app => app.criticality === this.currentFilters.criticality);
        }
        
        return filtered;
    }

    groupApplicationsEnhanced(apps) {
        const grouped = {
            'Critical Systems': [],
            'Core Banking': [],
            'Customer Services': [],
            'Payment Processing': [],
            'Risk & Compliance': [],
            'Data Management': [],
            'Digital Services': [],
            'Integration Services': [],
            'Operations': [],
            'Other': []
        };
        
        apps.forEach(app => {
            // Group by criticality first for critical systems
            if (app.criticality === 'critical') {
                grouped['Critical Systems'].push(app);
            } 
            // Then by business function
            else if (app.businessFunction && grouped[app.businessFunction]) {
                grouped[app.businessFunction].push(app);
            }
            // Then by archetype patterns
            else if (app.archetype === 'Database-Centric') {
                grouped['Data Management'].push(app);
            }
            else if (app.archetype === 'Microservices' || app.archetype === 'Cloud-Native') {
                grouped['Digital Services'].push(app);
            }
            else if (app.archetype === 'API-Centric (General)') {
                grouped['Integration Services'].push(app);
            }
            else {
                grouped['Other'].push(app);
            }
        });
        
        // Remove empty groups and sort apps within groups
        Object.keys(grouped).forEach(groupName => {
            if (grouped[groupName].length === 0) {
                delete grouped[groupName];
            } else {
                grouped[groupName].sort((a, b) => {
                    // Sort by criticality, then by record count, then by name
                    const critOrder = { 'critical': 4, 'high': 3, 'medium': 2, 'low': 1 };
                    const aCrit = critOrder[a.criticality] || 1;
                    const bCrit = critOrder[b.criticality] || 1;
                    
                    if (aCrit !== bCrit) return bCrit - aCrit;
                    
                    const aRecords = a.recordCount || 0;
                    const bRecords = b.recordCount || 0;
                    if (aRecords !== bRecords) return bRecords - aRecords;
                    
                    return a.name.localeCompare(b.name);
                });
            }
        });
        
        return grouped;
    }

    formatApplicationOption(app) {
        let name = app.displayName || app.name;
        
        // Add record count indicator for CSV data
        if (app.recordCount && app.recordCount > 0) {
            name += ` [${app.recordCount.toLocaleString()}]`;
        }
        
        // Add archetype indicator
        if (app.archetype && app.archetype !== 'Unknown') {
            const shortArchetype = this.getShortArchetype(app.archetype);
            name += ` • ${shortArchetype}`;
        }
        
        return name;
    }

    getShortArchetype(archetype) {
        const shortNames = {
            'Database-Centric': 'DB-Centric',
            'Web + API Headless': 'Web+API',
            'API-Centric (General)': 'API-Centric',
            'Microservices': 'μServices',
            'Cloud-Native': 'Cloud',
            'Event-Driven': 'Event',
            'ETL/Data Pipeline': 'ETL',
            'SOA with Message Broker': 'SOA+MQ'
        };
        return shortNames[archetype] || archetype;
    }

    handleSearchInput(query) {
        this.currentFilters.searchQuery = query.trim();
        this.updateApplicationList();
        
        // Update search results count
        const resultsCount = document.getElementById('search-results-count');
        if (resultsCount) {
            if (query.trim()) {
                const apps = window.AppData ? window.AppData.searchApplications(query) : [];
                resultsCount.textContent = `${apps.length} applications match "${query}"`;
                resultsCount.style.color = apps.length > 0 ? 'var(--accent-green)' : 'var(--accent-orange)';
            } else {
                resultsCount.textContent = '';
            }
        }
    }

    updateSelectedApps() {
        const appFilter = document.getElementById('app-filter-enhanced');
        if (!appFilter) return;
        
        const selectedOptions = Array.from(appFilter.selectedOptions);
        this.currentFilters.selectedApps = selectedOptions.map(option => option.value);
        
        // Handle "all" selection logic
        if (this.currentFilters.selectedApps.includes('all')) {
            this.currentFilters.selectedApps = ['all'];
            Array.from(appFilter.options).forEach(option => {
                option.selected = option.value === 'all';
            });
        } else if (this.currentFilters.selectedApps.length === 0) {
            this.currentFilters.selectedApps = ['all'];
            const allOption = appFilter.querySelector('option[value="all"]');
            if (allOption) allOption.selected = true;
        }
        
        this.updateFilterStats();
    }

    updateFilterStats() {
        const statsEl = document.getElementById('enhanced-filter-stats');
        if (!statsEl || !window.AppData) return;
        
        const totalApps = window.AppData.applications?.length || 0;
        const selectedCount = this.currentFilters.selectedApps.includes('all') ? 
            totalApps : this.currentFilters.selectedApps.length;
        
        let statsText = `${selectedCount}/${totalApps} applications`;
        
        // Add filter indicators
        const activeFilters = [];
        if (this.currentFilters.archetype !== 'all') activeFilters.push(`Arch: ${this.currentFilters.archetype}`);
        if (this.currentFilters.businessFunction !== 'all') activeFilters.push(`Func: ${this.currentFilters.businessFunction}`);
        if (this.currentFilters.criticality !== 'all') activeFilters.push(`Crit: ${this.currentFilters.criticality}`);
        if (this.currentFilters.searchQuery) activeFilters.push(`Search: "${this.currentFilters.searchQuery}"`);
        if (this.currentFilters.showUpstream) activeFilters.push('↑Upstream');
        if (this.currentFilters.showDownstream) activeFilters.push('↓Downstream');
        
        if (activeFilters.length > 0) {
            statsText += `\nFilters: ${activeFilters.join(', ')}`;
        }
        
        statsEl.textContent = statsText;
    }
}

// ================================================================================
// GLOBAL FUNCTIONS FOR ENHANCED FILTERS
// ================================================================================

// Initialize enhanced filters when topology is ready
function initializeEnhancedFilters() {
    if (window.topologyDashboard && !window.topologyDashboard.enhancedFilters) {
        window.topologyDashboard.enhancedFilters = new EnhancedTopologyFilters(window.topologyDashboard);
        window.topologyDashboard.enhancedFilters.setupEnhancedApplicationFilter();
        console.log('✅ Enhanced filters initialized');
    }
}

// Enhanced filter action functions
function selectAllAppsEnhanced() {
    if (window.topologyDashboard?.enhancedFilters) {
        const appFilter = document.getElementById('app-filter-enhanced');
        if (appFilter) {
            Array.from(appFilter.options).forEach(option => {
                option.selected = option.value === 'all';
            });
            window.topologyDashboard.enhancedFilters.updateSelectedApps();
            createToast('All applications selected', 'info');
        }
    }
}

function clearAllAppsEnhanced() {
    if (window.topologyDashboard?.enhancedFilters) {
        const appFilter = document.getElementById('app-filter-enhanced');
        if (appFilter) {
            Array.from(appFilter.options).forEach(option => {
                option.selected = false;
            });
            window.topologyDashboard.enhancedFilters.currentFilters.selectedApps = [];
            window.topologyDashboard.enhancedFilters.updateSelectedApps(); // This will set back to 'all'
            createToast('Application selection cleared', 'info');
        }
    }
}

function selectCriticalAppsEnhanced() {
    if (window.topologyDashboard?.enhancedFilters && window.AppData) {
        const criticalApps = window.AppData.getApplicationsByCriticality('critical');
        const appFilter = document.getElementById('app-filter-enhanced');
        
        if (appFilter && criticalApps.length > 0) {
            Array.from(appFilter.options).forEach(option => {
                option.selected = criticalApps.some(app => app.id === option.value);
            });
            window.topologyDashboard.enhancedFilters.updateSelectedApps();
            createToast(`Selected ${criticalApps.length} critical applications`, 'success');
        } else {
            createToast('No critical applications found', 'warning');
        }
    }
}

function selectByCurrentFilters() {
    if (window.topologyDashboard?.enhancedFilters && window.AppData) {
        const filters = window.topologyDashboard.enhancedFilters.currentFilters;
        let apps = window.AppData.getApplicationNamesForFilter();
        
        // Apply current filters
        apps = window.topologyDashboard.enhancedFilters.applyCurrentFilters(apps);
        const filteredAppIds = apps.filter(app => app.id !== 'all').map(app => app.id);
        
        const appFilter = document.getElementById('app-filter-enhanced');
        if (appFilter && filteredAppIds.length > 0) {
            Array.from(appFilter.options).forEach(option => {
                option.selected = filteredAppIds.includes(option.value);
            });
            window.topologyDashboard.enhancedFilters.updateSelectedApps();
            createToast(`Selected ${filteredAppIds.length} filtered applications`, 'success');
        } else {
            createToast('No applications match current filters', 'warning');
        }
    }
}

function applyEnhancedFilters() {
    if (window.topologyDashboard?.enhancedFilters) {
        const filters = window.topologyDashboard.enhancedFilters.currentFilters;
        
        // Update topology with current selections
        window.topologyDashboard.selectedApps = filters.selectedApps;
        window.topologyDashboard.showUpstream = filters.showUpstream;
        window.topologyDashboard.showDownstream = filters.showDownstream;
        
        // Update network data and render
        window.topologyDashboard.updateNetworkData();
        window.topologyDashboard.render();
        window.topologyDashboard.updateStats();
        //window.topologyDashboard.broadcastFilterChange();
        
        // Show feedback
        const selectedCount = filters.selectedApps.includes('all') ? 
            'All' : filters.selectedApps.length;
        createToast(`Enhanced filters applied: ${selectedCount} applications`, 'success');
        
        console.log('🔍 Enhanced filters applied:', filters);
    }
}

function resetAllFilters() {
    if (window.topologyDashboard?.enhancedFilters) {
        const filters = window.topologyDashboard.enhancedFilters;
        
        // Reset all filter states
        filters.currentFilters = {
            selectedApps: ['all'],
            archetype: 'all',
            businessFunction: 'all',
            criticality: 'all',
            searchQuery: '',
            showUpstream: false,
            showDownstream: false
        };
        
        // Reset UI elements
        const searchInput = document.getElementById('app-search-enhanced');
        const archetypeFilter = document.getElementById('archetype-filter');
        const businessFunctionFilter = document.getElementById('business-function-filter');
        const criticalityFilter = document.getElementById('criticality-filter');
        const upstreamCheck = document.getElementById('show-upstream-enhanced');
        const downstreamCheck = document.getElementById('show-downstream-enhanced');
        
        if (searchInput) searchInput.value = '';
        if (archetypeFilter) archetypeFilter.value = 'all';
        if (businessFunctionFilter) businessFunctionFilter.value = 'all';
        if (criticalityFilter) criticalityFilter.value = 'all';
        if (upstreamCheck) upstreamCheck.checked = false;
        if (downstreamCheck) downstreamCheck.checked = false;
        
        // Update application list and stats
        filters.updateApplicationList();
        
        createToast('All filters reset', 'info');
        console.log('🔄 All filters reset');
    }
}

// Auto-initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    // Wait for AppData to be ready
    const initWhenReady = () => {
        if (window.AppData && window.AppData.isDataLoaded && window.topologyDashboard) {
            setTimeout(initializeEnhancedFilters, 1000);
        } else {
            setTimeout(initWhenReady, 500);
        }
    };
    initWhenReady();
});

// Listen for AppData updates
window.addEventListener('activnetDataUpdated', () => {
    setTimeout(() => {
        if (window.topologyDashboard?.enhancedFilters) {
            window.topologyDashboard.enhancedFilters.populateEnhancedFilters();
        }
    }, 500);
});

console.log('✅ Enhanced Filter Integration loaded');
console.log('🎯 Features: Advanced search, multi-dimensional filtering, smart grouping');
console.log('📊 Supports: CSV data integration, real application names, enhanced UX');