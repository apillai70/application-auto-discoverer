# JavaScript fetch configuration for CORS
// static/ui/js/api-client.js
class APIClient {
    constructor(baseURL = window.location.origin) {
        this.baseURL = baseURL;
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };
		this.checkHealth();
    }
    
	async checkHealth() {
        try {
            await this.get('/health');
            console.log('✅ API connected at', this.baseURL);
        } catch (error) {
            console.warn('⚠️ API not responding at', this.baseURL);
        }
    }
	
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            ...options,
            headers: {
                ...this.defaultHeaders,
                ...options.headers
            },
            credentials: 'include', // Include cookies for CORS
            mode: 'cors' // Explicitly set CORS mode
        };
        
        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }
    
    async get(endpoint, headers = {}) {
        return this.request(endpoint, { method: 'GET', headers });
    }
    
    async post(endpoint, data, headers = {}) {
        return this.request(endpoint, {
            method: 'POST',
            headers,
            body: JSON.stringify(data)
        });
    }
    
    async put(endpoint, data, headers = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            headers,
            body: JSON.stringify(data)
        });
    }
    
    async delete(endpoint, headers = {}) {
        return this.request(endpoint, { method: 'DELETE', headers });
    }
}

// Initialize API client
const apiClient = new APIClient();

// Example usage in your existing JavaScript modules
// integration.js
const Integration = {
    async connectSplunk() {
        try {
            const response = await apiClient.post('/api/integration/connect/splunk', {
                url: document.getElementById('splunkUrl').value,
                username: document.getElementById('splunkUser').value,
                password: document.getElementById('splunkPass').value
            });
            
            AppDiscoverer.showToast('Connected to Splunk', 'success');
            return response;
        } catch (error) {
            AppDiscoverer.showToast('Splunk connection failed', 'error');
            throw error;
        }
    }
};
