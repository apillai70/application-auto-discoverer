// Sample application data - replace with your actual data
const applications = [
    { app_id: "ACDA", app_name: "ATM Check Card Disputes API" },
    { app_id: "ALE", app_name: "Advisor Locator Engine" },
    { app_id: "AODSVY", app_name: "AOD Survey" },
    { app_id: "APSE", app_name: "Appointment Setting (Timetrade)" },
    { app_id: "ARA", app_name: "Account Analysis Request Application" },
    { app_id: "AV", app_name: "Automated Vault" },
    { app_id: "BCA", app_name: "Branch Customer Authentication" },
    { app_id: "BKO", app_name: "Banko POC" },
    { app_id: "BLND", app_name: "BLEND SSI" },
    { app_id: "BLZD", app_name: "FICO/Blaze Decisioning -Rules Development" },
    { app_id: "CAP", app_name: "Capital Planning System" },
    { app_id: "CCS", app_name: "Customer Communication Service" },
    { app_id: "CDA", app_name: "Customer Data Analytics" },
    { app_id: "CDP", app_name: "Customer Data Platform" },
    { app_id: "CES", app_name: "Customer Experience Suite" },
    { app_id: "CFM", app_name: "Cash Flow Management" },
    { app_id: "CIS", app_name: "Customer Information System" },
    { app_id: "CLP", app_name: "Commercial Lending Platform" },
    { app_id: "CMS", app_name: "Content Management System" },
    { app_id: "CPS", app_name: "Core Processing System" },
    { app_id: "CRM", app_name: "Customer Relationship Management" },
    { app_id: "CSS", app_name: "Customer Service Suite" },
    { app_id: "DAS", app_name: "Data Analytics Service" },
    { app_id: "DBS", app_name: "Digital Banking Suite" },
    { app_id: "DLP", app_name: "Data Loss Prevention" },
    { app_id: "DMS", app_name: "Document Management System" },
    { app_id: "DPS", app_name: "Digital Payment Service" },
    { app_id: "DWH", app_name: "Data Warehouse" },
    { app_id: "EAI", app_name: "Enterprise Application Integration" },
    { app_id: "EBS", app_name: "Enterprise Banking System" },
    { app_id: "ECM", app_name: "Enterprise Content Management" },
    { app_id: "EDS", app_name: "Electronic Document Service" },
    { app_id: "EPS", app_name: "Electronic Payment System" },
    { app_id: "ERM", app_name: "Enterprise Risk Management" },
    { app_id: "ESB", app_name: "Enterprise Service Bus" },
    { app_id: "ETL", app_name: "Extract Transform Load" },
    { app_id: "FDS", app_name: "Fraud Detection System" },
    { app_id: "FMS", app_name: "Financial Management System" },
    { app_id: "FPS", app_name: "Financial Planning System" },
    { app_id: "GRC", app_name: "Governance Risk Compliance" },
    { app_id: "HRM", app_name: "Human Resource Management" },
    { app_id: "IMS", app_name: "Identity Management System" },
    { app_id: "IPS", app_name: "Investment Planning System" },
    { app_id: "KMS", app_name: "Knowledge Management System" },
    { app_id: "LMS", app_name: "Loan Management System" },
    { app_id: "MIS", app_name: "Management Information System" },
    { app_id: "OMS", app_name: "Order Management System" },
    { app_id: "PMS", app_name: "Performance Management System" },
    { app_id: "RMS", app_name: "Risk Management System" },
    { app_id: "SMS", app_name: "Security Management System" },
    { app_id: "WMS", app_name: "Workflow Management System" }
];

// Global variables
let filteredApps = [...applications];
let selectedApps = new Set();
let currentBatchIndex = 0;
const batchSize = 50;
let availableQualityLevels = {};
let availableTemplates = {};

// API Configuration - detect context and set appropriate base URL
// API Configuration - detect context and set appropriate base URL
function getApiBase() {
    const currentPort = window.location.port;
    const currentHost = window.location.hostname;
    
    console.log(`🔧 Detected context: ${currentHost}:${currentPort}`);
    
    // If running on port 8000 (activnet.prutech via redirect), use FastAPI on 8001
    if (currentPort === '8000') {
        return `http://${currentHost}:8001`;
    }
    
    // If running on port 9000 (combined proxy), use same origin - proxy will route API calls
    if (currentPort === '9000') {
        return window.location.origin;
    }
    
    // If running on port 8002 (direct frontend server), route API to port 8001
    if (currentPort === '8002') {
        return `http://${currentHost}:8001`;
    }
    
    // If running through activnet.prutech without explicit port (port 80/443), 
    // assume it's going through the redirect system
    if (currentHost === 'activnet.prutech' && !currentPort) {
        return window.location.origin; // Use same origin, let redirect handle it
    }
    
    // Default: use same origin (for development or other scenarios)
    return window.location.origin;
}

const API_BASE = getApiBase();
console.log('🔧 API Base URL:', API_BASE);
console.log('🔧 Current URL:', window.location.href);

// Safe DOM element access helper
function safeGetElement(id, defaultElement = null) {
    const element = document.getElementById(id);
    if (!element && defaultElement) {
        console.warn(`Element with id '${id}' not found, using default`);
        return defaultElement;
    }
    return element;
}

// Enhanced safeSetTextContent with better error handling
function safeSetTextContent(id, text) {
    const element = safeGetElement(id);
    if (element) {
        element.textContent = text;
        // console.log(`✅ Updated ${id}: ${text}`); // Uncomment for debugging
    } else {
        // Only log warnings for important missing elements
        if (['totalDocuments', 'generatedDocs', 'qualityScore'].includes(id)) {
            console.warn(`⚠️ Important element '${id}' not found`);
        }
        // Don't spam console for status bar elements if they don't exist
    }
}

// Call this to force an immediate status update
function forceStatusUpdate() {
    updateStatusBar();
    updateHeaderStats();
}

// Initialize the application
async function init() {
    console.log('🚀 Initializing Enhanced Document Generator...');
    
    selectAllApps(); // Select all by default
    updateDisplay();
    updateStats();
    setupFileUpload();
    
    // Load enhanced features (with fallbacks)
    await loadQualityLevels();
    await loadTemplates();
    
    // Add filter event listener
    const filterInput = safeGetElement('filterInput');
    if (filterInput) {
        filterInput.addEventListener('input', filterApplications);
    }
    
    // Initialize status bar
    updateStatusBar();
    
    // Add enhanced controls to the interface
    addEnhancedControls();
    
    console.log('✅ Enhanced Document Generator initialized');
}

// Load available quality levels from API with fallback
async function loadQualityLevels() {
    try {
        const response = await fetch(`${API_BASE}/api/v1/diagram/quality-levels`);
        if (response.ok) {
            const data = await response.json();
            availableQualityLevels = data.quality_levels || {};
            console.log('✅ Quality levels loaded:', availableQualityLevels);
        } else {
            throw new Error(`API returned ${response.status}`);
        }
    } catch (error) {
        console.warn('⚠️ Could not load quality levels from API, using fallback:', error.message);
        // Fallback quality levels
        availableQualityLevels = {
            "executive": { "name": "Executive Grade", "quality_percentage": "98%+" },
            "professional": { "name": "Professional Grade", "quality_percentage": "95%+" },
            "technical": { "name": "Technical Grade", "quality_percentage": "90%+" }
        };
    }
}

// Load available templates from API with fallback
async function loadTemplates() {
    try {
        const response = await fetch(`${API_BASE}/api/v1/diagram/templates`);
        if (response.ok) {
            const data = await response.json();
            availableTemplates = data.professional_templates || {};
            console.log('✅ Templates loaded:', availableTemplates);
        } else {
            throw new Error(`API returned ${response.status}`);
        }
    } catch (error) {
        console.warn('⚠️ Could not load templates from API, using fallback:', error.message);
        // Fallback templates
        availableTemplates = {
            "banking_security_architecture": { "name": "Banking Security Architecture" },
            "executive_network_overview": { "name": "Executive Network Overview" }
        };
    }
}

// Add enhanced controls to the interface
function addEnhancedControls() {
    // Check if quality level selector already exists
    const existingQualityLevel = safeGetElement('qualityLevel');
    if (existingQualityLevel) {
        // Add event listener if it exists
        existingQualityLevel.addEventListener('change', updateQualityDescription);
        updateQualityDescription(); // Initialize description
        console.log('✅ Enhanced controls found in HTML');
        return;
    }
    
    console.log('⚠️ Enhanced controls not found in HTML, attempting to add them...');
    
    // Try to find a place to add the controls
    const controlSections = document.querySelectorAll('.control-section');
    if (controlSections.length === 0) {
        console.warn('⚠️ No control sections found to add enhanced controls');
        return;
    }
    
    // Add quality control after the first control section
    const qualityControl = document.createElement('div');
    qualityControl.className = 'control-section';
    qualityControl.innerHTML = `
        <h3>🎯 Quality Level</h3>
        <select class="filter-input" id="qualityLevel">
            <option value="professional">Professional Grade (95%+)</option>
            <option value="executive">Executive Grade (98%+)</option>
            <option value="technical">Technical Grade (90%+)</option>
        </select>
        <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 5px;" id="qualityDescription">
            Professional quality for business stakeholders
        </div>
    `;
    
    // Add format control
    const formatControl = document.createElement('div');
    formatControl.className = 'control-section';
    formatControl.innerHTML = `
        <h3>📊 Output Formats</h3>
        <select class="filter-input" id="outputFormat">
            <option value="all">🚀 All Formats (Complete Package)</option>
            <option value="both">📐 Visio + Lucid Charts</option>
            <option value="visio">📐 Visio XML Only</option>
            <option value="lucid">📊 Lucid Chart Only</option>
        </select>
        <div class="format-options" style="margin-top: 10px;">
            <label style="display: flex; align-items: center; gap: 8px; margin-bottom: 5px;">
                <input type="checkbox" id="includeWord" checked>
                <span>📄 Word Templates</span>
            </label>
            <label style="display: flex; align-items: center; gap: 8px; margin-bottom: 5px;">
                <input type="checkbox" id="includeExcel" checked>
                <span>📊 Excel Mappers</span>
            </label>
            <label style="display: flex; align-items: center; gap: 8px;">
                <input type="checkbox" id="includePDF" checked>
                <span>📑 PDF Reports</span>
            </label>
        </div>
    `;
    
    // Insert after first control section
    const firstSection = controlSections[0];
    firstSection.parentNode.insertBefore(qualityControl, firstSection.nextSibling);
    firstSection.parentNode.insertBefore(formatControl, qualityControl.nextSibling);
    
    // Add event listeners
    document.getElementById('qualityLevel').addEventListener('change', updateQualityDescription);
    updateQualityDescription(); // Initialize description
    
    console.log('✅ Enhanced controls added to interface');
}

// Update quality description when quality level changes
function updateQualityDescription() {
    const qualityLevelElement = safeGetElement('qualityLevel');
    const descriptionElement = safeGetElement('qualityDescription');
    
    if (!qualityLevelElement || !descriptionElement) {
        return;
    }
    
    const qualityLevel = qualityLevelElement.value;
    
    const qualityDescriptions = {
        "executive": "98%+ quality for C-Suite presentations with executive metadata",
        "professional": "95%+ quality for business stakeholders with professional layouts", 
        "technical": "90%+ quality for technical teams with detailed annotations"
    };
    
    descriptionElement.textContent = qualityDescriptions[qualityLevel] || "Professional quality documentation";
}

// Status bar update function
function updateStatusBar() {
	
	const time = new Date().toLocaleTimeString();
    
    // Check if status bar elements exist
    const hasStatusBar = document.getElementById('lastUpdate');
    
    if (hasStatusBar) {
        // Update status bar if it exists
        safeSetTextContent('lastUpdate', `Last Update: ${time}`);
        safeSetTextContent('connectionStatus', '🟢 Connected');
        safeSetTextContent('systemStatus', 'System: Ready');
        
        // Update document count
        const docCount = document.querySelectorAll('.app-item, .document-item').length;
        safeSetTextContent('documentCount', `Documents: ${docCount}`);
        
        console.log('✅ Status bar updated');
    } else {
        // Update existing header stats instead
        console.log(`📊 Status Update: ${time} - Updating header stats`);
        updateHeaderStats();
    }
    
    // Schedule next update (every minute)
    setTimeout(updateStatusBar, 60000);
}

// Update the header stats that exist in your HTML
function updateHeaderStats() {
    try {
        // Update total documents count
        safeSetTextContent('totalDocuments', applications.length.toString());
        
        // Update selected/generated count
        safeSetTextContent('generatedDocs', selectedApps.size.toString());
        
        // Update in-progress count based on processing state
        const processingPanel = document.getElementById('processingPanel');
        const inProgress = processingPanel && processingPanel.classList.contains('active') ? 1 : 0;
        safeSetTextContent('inProgressDocs', inProgress.toString());
        
        // Update quality score based on selected quality level
        const qualityLevel = document.getElementById('qualityLevel');
        if (qualityLevel) {
            const qualityScores = {
                'executive': '98%',
                'professional': '95%',
                'technical': '90%'
            };
            safeSetTextContent('qualityScore', qualityScores[qualityLevel.value] || '95%');
        }
        
        console.log('✅ Header stats updated');
    } catch (error) {
        console.warn('⚠️ Error updating header stats:', error);
    }
}

// Application selection functions
function selectAllApps() {
    filteredApps.forEach(app => selectedApps.add(app.app_id));
}

function filterApplications() {
    const filterInput = safeGetElement('filterInput');
    if (!filterInput) return;
    
    const query = filterInput.value.toLowerCase();
    filteredApps = applications.filter(app => 
        app.app_name.toLowerCase().includes(query) ||
        app.app_id.toLowerCase().includes(query)
    );
    
    currentBatchIndex = 0;
    updateDisplay();
    updateStats();
}

// Display update functions
function updateDisplay() {
    const totalBatches = Math.ceil(filteredApps.length / batchSize);
    const start = currentBatchIndex * batchSize;
    const end = Math.min(start + batchSize, filteredApps.length);
    const currentBatch = filteredApps.slice(start, end);
    
    // Update batch info (with safety checks)
    safeSetTextContent('batchRange', `${start + 1}-${end}`);
    safeSetTextContent('batchTotal', filteredApps.length.toString());
    
    // Update batch controls
    const prevBtn = safeGetElement('prevBtn');
    const nextBtn = safeGetElement('nextBtn');
    
    if (prevBtn) prevBtn.disabled = currentBatchIndex === 0;
    if (nextBtn) nextBtn.disabled = currentBatchIndex >= totalBatches - 1;
    
    // Render applications in list format
    const list = safeGetElement('appList');
    if (list) {
        list.innerHTML = '';
        
        currentBatch.forEach(app => {
            const item = document.createElement('div');
            item.className = `app-item ${selectedApps.has(app.app_id) ? 'selected' : ''}`;
            item.onclick = () => toggleAppSelection(app.app_id);
            
            item.innerHTML = `
                <div>
                    <div class="app-name">${app.app_name}</div>
                    <div class="app-id">${app.app_id}</div>
                </div>
            `;
            
            list.appendChild(item);
        });
    }
    
    // Update topology canvas status
    updateTopologyCanvas();
}

function updateTopologyCanvas() {
    const canvas = document.querySelector('.canvas-placeholder');
    if (!canvas) return;
    
    const selectedCount = selectedApps.size;
    const qualityLevelElement = safeGetElement('qualityLevel');
    const outputFormatElement = safeGetElement('outputFormat');
    
    const qualityLevel = qualityLevelElement ? qualityLevelElement.value : 'professional';
    const outputFormat = outputFormatElement ? outputFormatElement.value : 'all';
    
    if (selectedCount > 0) {
        canvas.innerHTML = `
            <div class="icon">📊</div>
            <h3>Ready for Enhanced Document Generation</h3>
            <p>${selectedCount} applications selected for processing</p>
            <div style="margin-top: 20px; color: #00d4ff;">
                <div>🎯 Quality: ${qualityLevel.charAt(0).toUpperCase() + qualityLevel.slice(1)} Grade</div>
                <div>📊 Format: ${outputFormat.charAt(0).toUpperCase() + outputFormat.slice(1)}</div>
                <div style="margin-top: 10px;">Click "Generate Enhanced Documents" to begin generation</div>
            </div>
        `;
    } else {
        canvas.innerHTML = `
            <div class="icon">🔗</div>
            <h3>Enhanced Document Generator</h3>
            <p>Select applications and generate professional documents</p>
            <div style="margin-top: 20px; color: #64748b; font-size: 0.9rem;">
                • Choose applications from the left panel<br>
                • Select quality level and output formats<br>
                • Generate enterprise-ready documentation
            </div>
        `;
    }
}

// File upload handling
function setupFileUpload() {
    const uploadArea = document.querySelector('.file-upload-area');
    const fileInput = safeGetElement('fileInput');
    
    if (!uploadArea || !fileInput) {
        console.warn('⚠️ File upload elements not found');
        return;
    }
    
    // Drag and drop functionality
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const files = e.dataTransfer.files;
        handleFileUpload(files);
    });
    
    fileInput.addEventListener('change', (e) => {
        handleFileUpload(e.target.files);
    });
}

function handleFileUpload(files) {
    if (files.length > 0) {
        const fileNames = Array.from(files).map(f => f.name).join(', ');
        alert(`📁 Files uploaded: ${fileNames}\n\nProcessing new application data...`);
        
        // Simulate loading new data
        // In real implementation, this would parse the uploaded files
        // and update the applications array
    }
}

// Statistics update with safety checks
function updateStats() {
    const totalBatches = Math.ceil(filteredApps.length / batchSize);
    
    safeSetTextContent('totalApps', filteredApps.length.toString());
    safeSetTextContent('selectedApps', selectedApps.size.toString());
    safeSetTextContent('currentBatch', (currentBatchIndex + 1).toString());
    safeSetTextContent('batchSize', batchSize.toString());
    
    // Update totalBatches if element exists
    const totalBatchesElement = safeGetElement('totalBatches');
    if (totalBatchesElement) {
        totalBatchesElement.textContent = totalBatches.toString();
    }
}

// Selection control functions
function toggleAppSelection(appId) {
    if (selectedApps.has(appId)) {
        selectedApps.delete(appId);
    } else {
        selectedApps.add(appId);
    }
    updateDisplay();
    updateStats();
}

function selectAll() {
    filteredApps.forEach(app => selectedApps.add(app.app_id));
    updateDisplay();
    updateStats();
}

function clearSelection() {
    selectedApps.clear();
    updateDisplay();
    updateStats();
}

function resetFilter() {
    const filterInput = safeGetElement('filterInput');
    if (filterInput) {
        filterInput.value = '';
    }
    filteredApps = [...applications];
    currentBatchIndex = 0;
    updateDisplay();
    updateStats();
}

// Batch navigation
function previousBatch() {
    if (currentBatchIndex > 0) {
        currentBatchIndex--;
        updateDisplay();
        updateStats();
    }
}

function nextBatch() {
    const totalBatches = Math.ceil(filteredApps.length / batchSize);
    if (currentBatchIndex < totalBatches - 1) {
        currentBatchIndex++;
        updateDisplay();
        updateStats();
    }
}

// Enhanced processing functions using fallback APIs
function processApplications() {
    if (selectedApps.size === 0) {
        alert('Please select at least one application to process.');
        return;
    }
    
    const selectedAppData = applications.filter(app => selectedApps.has(app.app_id));
    const processingModeElement = safeGetElement('processingMode');
    const qualityLevelElement = safeGetElement('qualityLevel');
    const outputFormatElement = safeGetElement('outputFormat');
    
    const processingMode = processingModeElement ? processingModeElement.value : 'topology';
    const qualityLevel = qualityLevelElement ? qualityLevelElement.value : 'professional';
    const outputFormat = outputFormatElement ? outputFormatElement.value : 'all';
    
    // Update processing panel
    const panel = safeGetElement('processingPanel');
    if (panel) {
        panel.classList.add('active');
        panel.innerHTML = `
            <h3>🔄 Processing ${selectedApps.size} Applications</h3>
            <p>Mode: ${processingMode.toUpperCase()} | Quality: ${qualityLevel.toUpperCase()}</p>
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <div class="processing-status" id="processingStatusText">Initializing enhanced document generation...</div>
        `;
    }
    
    // Update status bar
    safeSetTextContent('processingStatus', '🔄 Processing...');
    
    // Start topology visualization
    simulateTopologyVisualization(selectedAppData, processingMode);
    
    // Call enhanced document generation with fallback
    callEnhancedDocumentGeneration(selectedAppData, qualityLevel, outputFormat);
}

// Enhanced document generation with fallback to legacy APIs
async function callEnhancedDocumentGeneration(appData, qualityLevel, outputFormat) {
    const statusElement = safeGetElement('processingStatusText');
    const progressElement = safeGetElement('progressFill');
    
    try {
        if (statusElement) statusElement.textContent = 'Calling enhanced document generation API...';
        if (progressElement) progressElement.style.width = '20%';
        
        // Try enhanced API first
        const enhancedPayload = {
            diagram_type: "network_topology",
            data: {
                applications: appData.map(app => ({
                    id: app.app_id,
                    name: app.app_name,
                    type: "application"
                }))
            },
            quality_level: qualityLevel,
            output_format: outputFormat
        };
        
        if (statusElement) statusElement.textContent = 'Generating enhanced documents...';
        if (progressElement) progressElement.style.width = '40%';
        
        let result;
        let usingFallback = false;
        
        try {
            // Try the enhanced API
            const response = await fetch(`${API_BASE}/api/v1/diagram/generate-enhanced-diagram-by-format`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(enhancedPayload)
            });
            
            if (response.ok) {
                result = await response.json();
            } else {
                throw new Error(`Enhanced API failed with status: ${response.status}`);
            }
        } catch (enhancedError) {
            console.warn('⚠️ Enhanced API not available, trying fallback:', enhancedError.message);
            usingFallback = true;
            
            // Fallback to legacy API
            const legacyPayload = {
                output_type: outputFormat,
                data: {
                    applications: appData,
                    metadata: {
                        total_count: appData.length,
                        processing_mode: 'documentation',
                        generated_at: new Date().toISOString()
                    }
                },
                user_preferences: {
                    theme: 'corporate',
                    include_metadata: true,
                    quality_level: qualityLevel
                }
            };
            
            const legacyResponse = await fetch(`${API_BASE}/api/v1/diagram/generate-document`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(legacyPayload)
            });
            
            if (legacyResponse.ok) {
                result = await legacyResponse.json();
                // Adapt legacy response to enhanced format
                result = adaptLegacyResponse(result, qualityLevel, outputFormat);
            } else {
                throw new Error(`Legacy API also failed with status: ${legacyResponse.status}`);
            }
        }
        
        if (statusElement) statusElement.textContent = 'Processing server response...';
        if (progressElement) progressElement.style.width = '60%';
        
        if (result && result.success) {
            if (statusElement) statusElement.textContent = 'Enhanced documents generated successfully!';
            if (progressElement) progressElement.style.width = '100%';
            
            if (usingFallback) {
                showSuccessNotification(
                    'Documents Generated (Legacy Mode)', 
                    'Documents generated using legacy API. Some enhanced features may not be available.'
                );
            }
            
            // Show enhanced results
            showEnhancedDocumentResults(result);
        } else {
            throw new Error(result?.error || 'Document generation failed');
        }
        
    } catch (error) {
        console.error('❌ Document generation error:', error);
        if (statusElement) statusElement.textContent = `Error: ${error.message}`;
        if (progressElement) {
            progressElement.style.width = '100%';
            progressElement.style.background = 'linear-gradient(90deg, #dc2626, #ff4444)';
        }
        
        // Show error notification
        showErrorNotification('Document Generation Failed', error.message);
        
        // Try simulation as last resort
        setTimeout(() => {
            console.log('🔄 Falling back to simulation...');
            simulateDocumentGeneration(appData, qualityLevel, outputFormat);
        }, 2000);
    }
}
// Demo functions for buttons
	function refreshDocumentation() {
		console.log('Refreshing documentation...');
		updateStatusBar();
	}
	
	function exportDocuments() {
		console.log('Exporting documents...');
		safeSetTextContent('systemStatus', 'System: Exporting...');
		setTimeout(() => {
			safeSetTextContent('systemStatus', 'System: Export Complete');
		}, 2000);
	}
	
	function validateCompliance() {
		console.log('Validating compliance...');
		safeSetTextContent('connectionStatus', '🔍 Validating...');
		setTimeout(() => {
			safeSetTextContent('connectionStatus', '✅ Compliant');
		}, 1500);
	}

	// Update document count based on actual documents in page
	function updateDocumentCount() {
		const documentItems = document.querySelectorAll('.document-item');
		safeSetTextContent('documentCount', `Documents: ${documentItems.length}`);
	}

	// Initialize document count when page loads
	document.addEventListener('DOMContentLoaded', function() {
		updateDocumentCount();
	});
// Adapt legacy API response to enhanced format
function adaptLegacyResponse(legacyResult, qualityLevel, outputFormat) {
    return {
        success: legacyResult.success,
        job_id: legacyResult.job_id || 'legacy_' + Date.now(),
        quality_level: `${qualityLevel.charAt(0).toUpperCase() + qualityLevel.slice(1)} Grade (Legacy)`,
        processing_time: 2.5,
        files: [{
            format: outputFormat,
            filename: legacyResult.result?.filename || `document_${Date.now()}`,
            file_path: legacyResult.result?.file_path,
            target_audience: "Professional Users",
            content_size: "2.1 MB"
        }],
        professional_features: {
            legacy_mode: true,
            basic_quality: true
        }
    };
}

// Simulation fallback for when APIs aren't available
function simulateDocumentGeneration(appData, qualityLevel, outputFormat) {
    console.log('🎭 Simulating document generation...');
    
    const formats = outputFormat === 'all' ? ['visio', 'lucid', 'pdf', 'word', 'excel'] :
                   outputFormat === 'both' ? ['visio', 'lucid'] : [outputFormat];
    
    const simulatedResult = {
        success: true,
        job_id: 'simulated_' + Date.now(),
        quality_level: `${qualityLevel.charAt(0).toUpperCase() + qualityLevel.slice(1)} Grade (Simulated)`,
        processing_time: 3.2,
        files: formats.map(format => ({
            format: format,
            filename: `${format}_document_${Date.now()}.${getFileExtension(format)}`,
            file_path: `/simulated/${format}_document_${Date.now()}.${getFileExtension(format)}`,
            target_audience: getTargetAudience(format),
            content_size: `${(Math.random() * 3 + 1).toFixed(1)} MB`
        })),
        professional_features: {
            simulation_mode: true,
            demo_quality: true
        }
    };
    
    showEnhancedDocumentResults(simulatedResult);
    showSuccessNotification(
        'Documents Simulated', 
        'Demo mode: Document generation simulated. In production, real files would be generated.'
    );
}

function getFileExtension(format) {
    const extensions = {
        'visio': 'vsdx',
        'lucid': 'lucid',
        'pdf': 'pdf',
        'word': 'docx',
        'excel': 'xlsx'
    };
    return extensions[format] || 'txt';
}

function getTargetAudience(format) {
    const audiences = {
        'visio': 'Technical Teams',
        'lucid': 'Collaborative Teams',
        'pdf': 'Executive Presentations',
        'word': 'Business Documentation',
        'excel': 'Operational Analysis'
    };
    return audiences[format] || 'Professional Users';
}

// Show enhanced document results
function showEnhancedDocumentResults(result) {
    // Generate enhanced output
    const output = {
        metadata: {
            job_id: result.job_id,
            quality_level: result.quality_level,
            formats_generated: result.files?.map(f => f.format) || [],
            processing_time: result.processing_time,
            professional_features: result.professional_features,
            generated_at: new Date().toISOString()
        },
        files: result.files || [],
        service_info: result.service_info
    };
    
    // Show results panel with enhanced information
    const resultPanel = safeGetElement('resultPanel');
    if (resultPanel) {
        resultPanel.classList.add('show');
    }
    
    // Update JSON preview with enhanced results
    const jsonPreview = safeGetElement('jsonPreview');
    if (jsonPreview) {
        jsonPreview.textContent = JSON.stringify(output, null, 2);
    }
    
    // Update processing panel
    const processingPanel = safeGetElement('processingPanel');
    if (processingPanel) {
        processingPanel.innerHTML = `
            <h3>✅ Enhanced Document Generation Complete!</h3>
            <p>Successfully generated ${result.files?.length || 0} professional documents</p>
            <div style="background: rgba(0, 255, 136, 0.1); padding: 10px; border-radius: 6px; margin-top: 10px;">
                <div style="font-size: 0.85rem; color: #00ff88;">
                    <div>🎯 Quality Level: ${result.quality_level}</div>
                    <div>⏱️ Processing Time: ${result.processing_time?.toFixed(1) || 'N/A'}s</div>
                    <div>📁 Job ID: ${result.job_id}</div>
                </div>
            </div>
        `;
    }
    
    // Store enhanced results for download
    window.lastProcessingResults = output;
    window.enhancedResults = result;
    
    // Add enhanced download options
    addEnhancedDownloadButtons(result);
}

// Add enhanced download buttons
function addEnhancedDownloadButtons(result) {
    const actionButtons = document.querySelector('.action-buttons');
    if (!actionButtons) return;
    
    // Clear existing enhanced buttons (keep JSON download)
    const existingButtons = actionButtons.querySelectorAll('.enhanced-download-btn');
    existingButtons.forEach(btn => btn.remove());
    
    // Add download buttons for each generated file
    if (result.files && result.files.length > 0) {
        result.files.forEach(file => {
            const button = document.createElement('button');
            button.className = 'btn btn-success enhanced-download-btn';
            button.style.margin = '5px';
            
            const formatIcons = {
                'visio': '📐',
                'lucid': '📊',
                'document': '📄',
                'word': '📄',
                'excel': '📊',
                'pdf': '📑'
            };
            
            button.innerHTML = `
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span>${formatIcons[file.format] || '📥'}</span>
                    <div>
                        <div style="font-weight: bold;">${file.format.toUpperCase()}</div>
                        <div style="font-size: 10px; opacity: 0.8;">${file.target_audience}</div>
                    </div>
                </div>
            `;
            
            button.onclick = () => downloadEnhancedFile(file);
            actionButtons.appendChild(button);
        });
    }
    
    // Add batch download button
    const batchButton = document.createElement('button');
    batchButton.className = 'btn btn-primary enhanced-download-btn';
    batchButton.innerHTML = `
        <div style="display: flex; align-items: center; gap: 8px;">
            <span>📦</span>
            <div>
                <div style="font-weight: bold;">Download All</div>
                <div style="font-size: 10px; opacity: 0.8;">Complete Package</div>
            </div>
        </div>
    `;
    batchButton.onclick = () => downloadAllEnhancedFiles(result);
    actionButtons.appendChild(batchButton);
}

// Download enhanced file with fallback
async function downloadEnhancedFile(file) {
    try {
        // Check if file is simulated
        if (file.file_path && file.file_path.includes('/simulated/')) {
            showInfoNotification(
                'Simulated Download', 
                `In production, ${file.format.toUpperCase()} document would be downloaded. File: ${file.filename}`
            );
            return;
        }
        
        const response = await fetch(`${API_BASE}/api/v1/diagram/download/${file.filename}`);
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = file.filename;
            a.click();
            window.URL.revokeObjectURL(url);
            
            showSuccessNotification(
                `${file.format.toUpperCase()} Downloaded`, 
                `Professional ${file.format} document ready for use`
            );
        } else {
            throw new Error(`Download failed: ${response.status}`);
        }
    } catch (error) {
        console.warn('Download error:', error);
        showErrorNotification('Download Failed', `Could not download ${file.format}: ${error.message}`);
    }
}

// Download all enhanced files
async function downloadAllEnhancedFiles(result) {
    try {
        // Check if batch download is available
        const response = await fetch(`${API_BASE}/api/v1/diagram/download-batch/${result.job_id}`);
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `enhanced_documents_${result.job_id}.zip`;
            a.click();
            window.URL.revokeObjectURL(url);
            
            showSuccessNotification(
                'Complete Package Downloaded', 
                'All enhanced documents downloaded as ZIP archive'
            );
        } else {
            // Fallback: download files individually
            for (const file of result.files) {
                await downloadEnhancedFile(file);
                await new Promise(resolve => setTimeout(resolve, 500)); // Small delay between downloads
            }
        }
    } catch (error) {
        showErrorNotification('Batch Download Failed', error.message);
    }
}

// Topology visualization functions
function simulateTopologyVisualization(appData, mode) {
    const canvas = document.querySelector('.canvas-placeholder');
    if (!canvas) return;
    
    // Show processing animation
    canvas.innerHTML = `
        <div class="icon pulse">⚡</div>
        <h3>Processing ${appData.length} Applications</h3>
        <p>Generating enhanced documents...</p>
        <div class="progress-bar" style="width: 300px; margin: 20px auto;">
            <div class="progress-fill" id="canvasProgress"></div>
        </div>
    `;
    
    // Animate progress
    let progress = 0;
    const progressBar = safeGetElement('canvasProgress');
    
    const interval = setInterval(() => {
        progress += 10;
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
        }
        
        if (progress >= 100) {
            clearInterval(interval);
            showTopologyResult(appData, mode);
        }
    }, 300);
}

function showTopologyResult(appData, mode) {
    const canvas = document.querySelector('.canvas-placeholder');
    if (!canvas) return;
    
    canvas.innerHTML = `
        <div class="icon" style="color: #00ff88;">✅</div>
        <h3>Enhanced Document Generation Complete</h3>
        <p>Successfully processed ${appData.length} applications</p>
        <div style="margin-top: 20px; color: #e2e8f0; font-size: 0.9rem;">
            <div>📐 Professional Visio XML generated</div>
            <div>📊 Enhanced Lucid Charts created</div>
            <div>📄 Executive documentation prepared</div>
        </div>
        <div style="margin-top: 20px;">
            <button class="btn btn-primary" onclick="showEnhancedResults()">
                🔍 View Generated Documents
            </button>
        </div>
    `;
    
    // Update status bar
    safeSetTextContent('processingStatus', '✅ Documents Generated');
    safeSetTextContent('lastUpdate', `Last Update: ${new Date().toLocaleTimeString()}`);
}

function showEnhancedResults() {
    alert('🎉 Enhanced documents generated successfully!\n\nGenerated files:\n• Professional Visio XML\n• Enhanced Lucid Charts\n• Executive Word Templates\n• Excel Application Mappers\n• Professional PDF Reports\n\nCheck the download section below for access to all files.');
}

// Legacy function compatibility - now calls enhanced APIs with fallback
function generateDocumentation() {
    callEnhancedGenerator('document', 'professional');
}

function generateVisio() {
    callEnhancedGenerator('visio', 'professional');
}

function generatePDF() {
    callEnhancedGenerator('pdf', 'executive');
}

function generateExcel() {
    callEnhancedGenerator('excel', 'professional');
}

function generateWord() {
    callEnhancedGenerator('document', 'professional');
}

function generateLucid() {
    callEnhancedGenerator('lucid', 'professional');
}

function createDiagram() {
    callEnhancedGenerator('both', 'professional');
}

// Enhanced generator function with fallback
async function callEnhancedGenerator(format, qualityLevel = 'professional') {
    if (!window.lastProcessingResults && selectedApps.size === 0) {
        alert('Please select applications and process them first.');
        return;
    }
    
    const notification = createProcessingNotification(format);
    document.body.appendChild(notification);
    
    try {
        const selectedAppData = applications.filter(app => selectedApps.has(app.app_id));
        
        // Call the main enhanced generation function
        await callEnhancedDocumentGeneration(selectedAppData, qualityLevel, format);
        
        // The notification will be updated by the main function
        
    } catch (error) {
        console.error('Enhanced generation error:', error);
        updateNotificationError(notification, format, error.message);
    }
}

// Notification functions
function createProcessingNotification(outputType) {
    const notification = document.createElement('div');
    notification.className = 'processing-notification';
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(90deg, #0ea5e9, #00d4ff);
        color: #000;
        padding: 15px 20px;
        border-radius: 8px;
        font-weight: 500;
        z-index: 1000;
        animation: slideIn 0.3s ease;
        min-width: 300px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    `;
    
    notification.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
            <div class="spinner" style="
                width: 20px; 
                height: 20px; 
                border: 2px solid #000; 
                border-top: 2px solid transparent; 
                border-radius: 50%; 
                animation: spin 1s linear infinite;
            "></div>
            <div>
                <div style="font-weight: bold;">🔄 Generating Enhanced ${outputType.toUpperCase()}</div>
                <div style="font-size: 12px; opacity: 0.8;">Using professional document generator...</div>
            </div>
        </div>
    `;
    
    return notification;
}

function updateNotificationSuccess(notification, outputType, result) {
    notification.style.background = 'linear-gradient(90deg, #059669, #00ff88)';
    notification.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="color: #000; font-size: 18px;">✅</div>
            <div>
                <div style="font-weight: bold;">Enhanced ${outputType.toUpperCase()} Generated!</div>
                <div style="font-size: 12px; opacity: 0.8;">
                    ${result.quality_level} quality ready for download
                </div>
            </div>
        </div>
    `;
    
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}

function updateNotificationError(notification, outputType, error) {
    notification.style.background = 'linear-gradient(90deg, #dc2626, #ff4444)';
    notification.style.color = '#fff';
    notification.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="color: #fff; font-size: 18px;">❌</div>
            <div>
                <div style="font-weight: bold;">${outputType.toUpperCase()} Generation Failed</div>
                <div style="font-size: 12px; opacity: 0.9;">${error}</div>
            </div>
        </div>
    `;
    
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 8000);
}

function showSuccessNotification(title, message) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(90deg, #059669, #00ff88);
        color: #000;
        padding: 15px 20px;
        border-radius: 8px;
        font-weight: 500;
        z-index: 1000;
        animation: slideIn 0.3s ease;
        min-width: 300px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    `;
    
    notification.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="color: #000; font-size: 18px;">✅</div>
            <div>
                <div style="font-weight: bold;">${title}</div>
                <div style="font-size: 12px; opacity: 0.8;">${message}</div>
            </div>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}

function showErrorNotification(title, message) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(90deg, #dc2626, #ff4444);
        color: #fff;
        padding: 15px 20px;
        border-radius: 8px;
        font-weight: 500;
        z-index: 1000;
        animation: slideIn 0.3s ease;
        min-width: 300px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    `;
    
    notification.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="color: #fff; font-size: 18px;">❌</div>
            <div>
                <div style="font-weight: bold;">${title}</div>
                <div style="font-size: 12px; opacity: 0.9;">${message}</div>
            </div>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 8000);
}

function showInfoNotification(title, message) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(90deg, #0ea5e9, #00d4ff);
        color: #000;
        padding: 15px 20px;
        border-radius: 8px;
        font-weight: 500;
        z-index: 1000;
        animation: slideIn 0.3s ease;
        min-width: 300px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    `;
    
    notification.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="color: #000; font-size: 18px;">ℹ️</div>
            <div>
                <div style="font-weight: bold;">${title}</div>
                <div style="font-size: 12px; opacity: 0.8;">${message}</div>
            </div>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}

// Utility function to get selected application names
function getSelectedApplicationNames() {
    return applications
        .filter(app => selectedApps.has(app.app_id))
        .map(app => app.app_name);
}

// Export function for JSON download
function downloadJSON() {
    if (!window.lastProcessingResults) {
        alert('No processing results available to download.');
        return;
    }
    
    const dataStr = JSON.stringify(window.lastProcessingResults, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `enhanced_application_results_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    
    URL.revokeObjectURL(url);
}

// Add CSS for animations
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    @keyframes slideIn {
        from { opacity: 0; transform: translateX(100%); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    .control-section h3 {
        color: #00d4ff;
        margin-bottom: 15px;
        font-size: 1rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .format-options label {
        color: #e2e8f0;
        font-size: 0.85rem;
        cursor: pointer;
    }
    
    .format-options input[type="checkbox"] {
        accent-color: #00d4ff;
    }
    
    .pulse {
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
`;
document.head.appendChild(style);

// Initialize the application when page loads
document.addEventListener('DOMContentLoaded', init);