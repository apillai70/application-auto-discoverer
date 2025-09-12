// /ui/js/shared-state.js
window.PortScopeShared = {
    currentJob: null,
    
    // Set job data from either page
    setCurrentJob: function(jobId, source = 'excel') {
        this.currentJob = { jobId, source, timestamp: Date.now() };
        localStorage.setItem('portscope_current_job', JSON.stringify(this.currentJob));
        this.notifyPages();
    },
    
    // Get current job
    getCurrentJob: function() {
        const stored = localStorage.getItem('portscope_current_job');
        return stored ? JSON.parse(stored) : null;
    },
    
    // Cross-page communication
    notifyPages: function() {
        window.postMessage({ type: 'PORTSCOPE_JOB_UPDATE', job: this.currentJob }, '*');
    },
    
    // Navigate between pages with context
    goToArchetype: function(jobId) {
        window.open(`/ui/html/archetype.html?source=excel&job_id=${jobId}`, '_blank');
    },
    
    goToDocumentation: function(jobId) {
        window.open(`/ui/html/documentation.html?job_id=${jobId}`, '_blank');
    }
};