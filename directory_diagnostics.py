# directory_diagnostics.py
# Script to diagnose missing static files issue

import os
from pathlib import Path

def diagnose_directory_structure():
    """Diagnose the current directory structure and missing files"""
    
    project_root = Path.cwd()
    print(f"🔍 Diagnosing directory structure from: {project_root}")
    print("=" * 60)
    
    # Expected files from the HTML
    expected_files = {
        "CSS Files": [
            "ui/css/common.css",
            "ui/css/topology.css"
        ],
        "JS Files": [
            "ui/js/csv-data-loader.js",
            "ui/js/app-data.js", 
            "ui/js/data-source-manager.js",
            "ui/js/common.js",
            "ui/js/topology.js",
            "ui/js/enhanced-filters.js"
        ]
    }
    
    # Check what actually exists
    print("📁 Expected File Structure:")
    missing_files = []
    existing_files = []
    
    for file_type, files in expected_files.items():
        print(f"\n{file_type}:")
        for file_path in files:
            full_path = project_root / file_path
            status = "✅ EXISTS" if full_path.exists() else "❌ MISSING"
            print(f"  {status} - {file_path}")
            
            if full_path.exists():
                existing_files.append(file_path)
                size = full_path.stat().st_size
                print(f"           Size: {size} bytes")
            else:
                missing_files.append(file_path)
    
    # Check what directories exist
    print("\n📂 Directory Structure:")
    key_dirs = [
        "ui",
        "ui/css", 
        "ui/js",
        "ui/html",
        "static"
    ]
    
    for dir_path in key_dirs:
        full_path = project_root / dir_path
        if full_path.exists():
            files_in_dir = list(full_path.glob("*.*"))
            print(f"  ✅ {dir_path}/ ({len(files_in_dir)} files)")
            for file in files_in_dir[:5]:  # Show first 5 files
                print(f"     - {file.name}")
            if len(files_in_dir) > 5:
                print(f"     ... and {len(files_in_dir) - 5} more files")
        else:
            print(f"  ❌ {dir_path}/ (does not exist)")
    
    # Look for files that might be in wrong locations
    print("\n🔍 Searching for misplaced files:")
    search_patterns = ["*.css", "*.js"]
    found_files = {}
    
    for pattern in search_patterns:
        files = list(project_root.rglob(pattern))
        found_files[pattern] = files
        print(f"\n  Found {pattern} files:")
        for file in files:
            relative_path = file.relative_to(project_root)
            print(f"    📄 {relative_path}")
    
    # Generate solutions
    print("\n" + "=" * 60)
    print("💡 SOLUTIONS:")
    
    if missing_files:
        print(f"\n❌ Missing {len(missing_files)} files:")
        for file in missing_files:
            print(f"  - {file}")
        
        print("\n🛠️  Option 1: Create missing files")
        print("   Run the file creation script to generate basic template files")
        
        print("\n🛠️  Option 2: Move existing files")
        if found_files.get("*.css") or found_files.get("*.js"):
            print("   Found some CSS/JS files in other locations:")
            for pattern, files in found_files.items():
                for file in files:
                    relative_path = file.relative_to(project_root)
                    # Suggest where to move it
                    filename = file.name
                    if filename.endswith('.css'):
                        suggested_path = f"ui/css/{filename}"
                    elif filename.endswith('.js'):
                        suggested_path = f"ui/js/{filename}"
                    else:
                        suggested_path = f"ui/{filename}"
                    print(f"     Move: {relative_path} → {suggested_path}")
        
        print("\n🛠️  Option 3: Update HTML paths")
        print("   Update index.html to point to actual file locations")
    
    else:
        print("✅ All expected files exist!")
        print("The issue might be with the FastAPI mounting. Check the server logs.")
    
    return {
        "missing_files": missing_files,
        "existing_files": existing_files, 
        "found_files": found_files
    }

def create_missing_files():
    """Create basic template files for missing CSS/JS files"""
    
    project_root = Path.cwd()
    
    # Create directory structure
    (project_root / "ui" / "css").mkdir(parents=True, exist_ok=True)
    (project_root / "ui" / "js").mkdir(parents=True, exist_ok=True)
    
    # Basic CSS files
    css_files = {
        "ui/css/common.css": """/* Common styles for the application */
:root {
    --bg-primary: #1a1a1a;
    --bg-secondary: #2a2a2a;
    --bg-tertiary: #3a3a3a;
    --text-primary: #ffffff;
    --text-muted: #cccccc;
    --accent-blue: #3b82f6;
    --accent-green: #10b981;
    --accent-orange: #f59e0b;
    --accent-purple: #8b5cf6;
    --border-color: #4a5568;
}

body {
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background-color: var(--bg-primary);
    color: var(--text-primary);
}

.container {
    max-width: 100%;
    margin: 0 auto;
}

/* Loading spinner */
.loading-spinner {
    width: 20px;
    height: 20px;
    border: 2px solid #f3f3f3;
    border-top: 2px solid var(--accent-blue);
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}""",

        "ui/css/topology.css": """/* Topology-specific styles */
.topology-container {
    display: flex;
    height: calc(100vh - 200px);
    gap: 16px;
    padding: 16px;
}

#left-panel, #right-panel {
    width: 300px;
    background: var(--bg-secondary);
    border-radius: 8px;
    padding: 16px;
    overflow-y: auto;
}

#middle-canvas-wrapper {
    flex: 1;
    position: relative;
    background: var(--bg-secondary);
    border-radius: 8px;
}

#viz-canvas {
    width: 100%;
    height: 100%;
    position: relative;
}

#graph {
    width: 100%;
    height: 100%;
}

.filter-section {
    margin-bottom: 20px;
    padding: 12px;
    background: var(--bg-tertiary);
    border-radius: 6px;
}

.topology-btn {
    background: var(--accent-blue);
    color: white;
    border: none;
    padding: 8px 12px;
    border-radius: 4px;
    cursor: pointer;
    margin: 2px;
    font-size: 12px;
}

.topology-btn:hover {
    opacity: 0.8;
}

.topology-btn.active {
    background: var(--accent-green);
}

.topology-select {
    width: 100%;
    padding: 6px;
    background: var(--bg-primary);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
    border-radius: 4px;
}

.file-input {
    width: 100%;
    padding: 6px;
    background: var(--bg-primary);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
    border-radius: 4px;
}"""
    }
    
    # Basic JS files 
    js_files = {
        "ui/js/csv-data-loader.js": """// CSV Data Loader
console.log('CSV Data Loader initialized');

class CSVDataLoader {
    constructor() {
        this.data = null;
        this.metadata = {};
    }
    
    async loadData() {
        console.log('Loading CSV data...');
        // Basic implementation
        return { success: true, message: 'CSV loader ready' };
    }
    
    getData() {
        return this.data || [];
    }
    
    getMetadata() {
        return this.metadata;
    }
}

// Export for global use
window.CSVDataLoader = CSVDataLoader;""",

        "ui/js/app-data.js": """// Application Data Manager
console.log('App Data Manager initialized');

class AppData {
    constructor() {
        this.networkTopology = { nodes: [], links: [] };
        this.applications = [];
        this.ready = false;
    }
    
    static getInstance() {
        if (!window._appDataInstance) {
            window._appDataInstance = new AppData();
        }
        return window._appDataInstance;
    }
    
    async initialize() {
        console.log('Initializing app data...');
        this.ready = true;
        return true;
    }
    
    isReady() {
        return this.ready;
    }
    
    getMetadata() {
        return {
            recordCount: 0,
            applicationCount: this.applications.length,
            nodeCount: this.networkTopology.nodes.length,
            linkCount: this.networkTopology.links.length,
            summaryStats: {}
        };
    }
}

// Initialize global instance
window.AppData = AppData.getInstance();""",

        "ui/js/data-source-manager.js": """// Data Source Manager
console.log('Data Source Manager initialized');

class DataSourceManager {
    constructor() {
        this.currentSource = null;
    }
    
    triggerFileUpload() {
        console.log('Triggering file upload...');
        const input = document.getElementById('csv-upload-input');
        if (input) {
            input.click();
        }
    }
    
    clearAllData() {
        console.log('Clearing all data...');
        this.currentSource = null;
    }
}

// Setup dynamic data source
function setupDynamicDataSource() {
    console.log('Setting up dynamic data source...');
    window.dataSourceManager = new DataSourceManager();
}

// Export
window.DataSourceManager = DataSourceManager;
window.setupDynamicDataSource = setupDynamicDataSource;""",

        "ui/js/common.js": """// Common JavaScript utilities
console.log('Common utilities loaded');

// Toast notifications
function createToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        background: var(--bg-secondary);
        color: var(--text-primary);
        border-radius: 6px;
        z-index: 1000;
        border-left: 4px solid var(--accent-${type === 'success' ? 'green' : type === 'error' ? 'red' : 'blue'});
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Global utility functions
window.createToast = createToast;""",

        "ui/js/topology.js": """// Topology Visualization
console.log('Topology visualization loaded');

class TopologyDashboard {
    constructor() {
        this.svg = null;
        this.simulation = null;
        this.nodes = [];
        this.links = [];
    }
    
    initialize() {
        console.log('Initializing topology dashboard...');
        this.setupSVG();
        this.render();
    }
    
    setupSVG() {
        const container = document.getElementById('graph');
        if (container) {
            // Basic SVG setup
            this.svg = d3.select('#graph')
                .attr('width', '100%')
                .attr('height', '100%');
        }
    }
    
    render() {
        console.log('Rendering topology...');
        // Basic rendering implementation
    }
    
    updateNetworkData() {
        console.log('Updating network data...');
    }
    
    updateStats() {
        console.log('Updating statistics...');
    }
    
    populateApplicationFilter() {
        console.log('Populating application filter...');
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.topologyDashboard = new TopologyDashboard();
    window.topologyDashboard.initialize();
});

// Global functions referenced in HTML
function setLayout(layout) { console.log('Setting layout:', layout); }
function analyzeTraffic() { console.log('Analyzing traffic...'); }
function findCriticalPaths() { console.log('Finding critical paths...'); }
function detectClusters() { console.log('Detecting clusters...'); }
function exportTopology() { console.log('Exporting topology...'); }
function zoomIn() { console.log('Zooming in...'); }
function zoomOut() { console.log('Zooming out...'); }
function resetView() { console.log('Resetting view...'); }
function centerView() { console.log('Centering view...'); }
function panDirection(direction) { console.log('Panning:', direction); }
function closeOverlay() { console.log('Closing overlay...'); }

// Application filter functions
function selectAllApps() { console.log('Selecting all apps...'); }
function clearAllApps() { console.log('Clearing all apps...'); }
function selectCriticalApps() { console.log('Selecting critical apps...'); }
function selectByArchetype(archetype) { console.log('Selecting by archetype:', archetype); }
function applyApplicationFilter() { console.log('Applying application filter...'); }""",

        "ui/js/enhanced-filters.js": """// Enhanced Filters
console.log('Enhanced filters loaded');

class EnhancedFilters {
    constructor() {
        this.activeFilters = {};
    }
    
    initialize() {
        console.log('Initializing enhanced filters...');
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Setup filter event listeners
        const checkboxes = document.querySelectorAll('.topology-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                console.log('Filter changed:', e.target.id, e.target.checked);
            });
        });
    }
    
    applyFilters() {
        console.log('Applying enhanced filters...');
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const enhancedFilters = new EnhancedFilters();
    enhancedFilters.initialize();
});"""
    }
    
    # Create the files
    created_files = []
    for file_path, content in {**css_files, **js_files}.items():
        full_path = project_root / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding='utf-8')
        created_files.append(file_path)
        print(f"✅ Created: {file_path}")
    
    print(f"\n🎉 Created {len(created_files)} files!")
    print("You can now restart your FastAPI server and the 404 errors should be resolved.")
    
    return created_files

if __name__ == "__main__":
    print("🔧 FastAPI Static Files Diagnostic Tool")
    print("=" * 60)
    
    # Run diagnosis
    results = diagnose_directory_structure()
    
    if results["missing_files"]:
        print(f"\n❓ Would you like to create the {len(results['missing_files'])} missing files? (y/n): ", end="")
        response = input().lower().strip()
        
        if response in ['y', 'yes']:
            print("\n🛠️  Creating missing files...")
            create_missing_files()
        else:
            print("\n💡 Run this script again and choose 'y' when you're ready to create the files.")
    else:
        print("\n✅ All files exist! The issue might be with the server configuration.")