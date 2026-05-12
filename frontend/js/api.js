/**
 * SafeHer - API Service
 * Handles all API calls to the backend
 */

const API_BASE_URL = 'http://localhost:8000/api/v1';

class APIService {
    constructor() {
        this.baseUrl = API_BASE_URL;
        this.token = localStorage.getItem('accessToken');
    }

    /**
     * Get authorization headers
     */
    getHeaders(includeAuth = true) {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (includeAuth && this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        
        return headers;
    }

    /**
     * Set authentication token
     */
    setToken(token) {
        this.token = token;
        localStorage.setItem('accessToken', token);
    }

    /**
     * Clear authentication token
     */
    clearToken() {
        this.token = null;
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('user');
    }

    /**
     * Handle API response
     */
    async handleResponse(response) {
        const data = await response.json().catch(() => ({}));
        
        if (!response.ok) {
            if (response.status === 401) {
                // Try to refresh token
                const refreshed = await this.refreshToken();
                if (!refreshed) {
                    this.clearToken();
                    window.location.reload();
                }
            }
            throw new Error(data.detail || data.message || 'An error occurred');
        }
        
        return data;
    }

    /**
     * Refresh access token
     */
    async refreshToken() {
        const refreshToken = localStorage.getItem('refreshToken');
        if (!refreshToken) return false;

        try {
            const response = await fetch(`${this.baseUrl}/auth/refresh`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: refreshToken })
            });

            if (response.ok) {
                const data = await response.json();
                this.setToken(data.access_token);
                localStorage.setItem('refreshToken', data.refresh_token);
                return true;
            }
        } catch (error) {
            console.error('Token refresh failed:', error);
        }
        
        return false;
    }

    // ==================== Auth Endpoints ====================

    /**
     * Login user
     */
    async login(email, password) {
        const response = await fetch(`${this.baseUrl}/auth/login`, {
            method: 'POST',
            headers: this.getHeaders(false),
            body: JSON.stringify({ email, password })
        });
        
        const data = await this.handleResponse(response);
        this.setToken(data.access_token);
        localStorage.setItem('refreshToken', data.refresh_token);
        
        return data;
    }

    /**
     * Logout user
     */
    async logout() {
        try {
            await fetch(`${this.baseUrl}/auth/logout`, {
                method: 'POST',
                headers: this.getHeaders()
            });
        } catch (error) {
            console.error('Logout error:', error);
        }
        this.clearToken();
    }

    // ==================== User Endpoints ====================

    /**
     * Register new user
     */
    async register(userData) {
        const response = await fetch(`${this.baseUrl}/users/register`, {
            method: 'POST',
            headers: this.getHeaders(false),
            body: JSON.stringify(userData)
        });
        
        return this.handleResponse(response);
    }

    /**
     * Get current user profile
     */
    async getCurrentUser() {
        const response = await fetch(`${this.baseUrl}/users/me`, {
            method: 'GET',
            headers: this.getHeaders()
        });
        
        return this.handleResponse(response);
    }

    /**
     * Update user profile
     */
    async updateProfile(userData) {
        const response = await fetch(`${this.baseUrl}/users/me`, {
            method: 'PUT',
            headers: this.getHeaders(),
            body: JSON.stringify(userData)
        });
        
        return this.handleResponse(response);
    }

    // ==================== Emergency Contacts Endpoints ====================

    /**
     * Get all emergency contacts
     */
    async getEmergencyContacts() {
        const response = await fetch(`${this.baseUrl}/users/contacts`, {
            method: 'GET',
            headers: this.getHeaders()
        });
        
        return this.handleResponse(response);
    }

    /**
     * Add emergency contact
     */
    async addEmergencyContact(contactData) {
        const response = await fetch(`${this.baseUrl}/users/contacts`, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify(contactData)
        });
        
        return this.handleResponse(response);
    }

    /**
     * Update emergency contact
     */
    async updateEmergencyContact(contactId, contactData) {
        const response = await fetch(`${this.baseUrl}/users/contacts/${contactId}`, {
            method: 'PUT',
            headers: this.getHeaders(),
            body: JSON.stringify(contactData)
        });
        
        return this.handleResponse(response);
    }

    /**
     * Delete emergency contact
     */
    async deleteEmergencyContact(contactId) {
        const response = await fetch(`${this.baseUrl}/users/contacts/${contactId}`, {
            method: 'DELETE',
            headers: this.getHeaders()
        });
        
        return this.handleResponse(response);
    }

    // ==================== Emergency Endpoints ====================

    /**
     * Trigger emergency
     */
    async triggerEmergency(emergencyData) {
        const response = await fetch(`${this.baseUrl}/emergency/trigger`, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify(emergencyData)
        });
        
        return this.handleResponse(response);
    }

    /**
     * Cancel emergency
     */
    async cancelEmergency(emergencyId) {
        const response = await fetch(`${this.baseUrl}/emergency/${emergencyId}/cancel`, {
            method: 'POST',
            headers: this.getHeaders()
        });
        
        return this.handleResponse(response);
    }

    /**
     * Get emergency history
     */
    async getEmergencyHistory() {
        const response = await fetch(`${this.baseUrl}/emergency/history`, {
            method: 'GET',
            headers: this.getHeaders()
        });
        
        return this.handleResponse(response);
    }

    /**
     * Request fake call
     */
    async requestFakeCall(callData) {
        const response = await fetch(`${this.baseUrl}/emergency/fake-call`, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify(callData)
        });
        
        return this.handleResponse(response);
    }

    // ==================== Safety Endpoints ====================

    /**
     * Assess risk for location
     */
    async assessRisk(locationData) {
        const response = await fetch(`${this.baseUrl}/safety/assess-risk`, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify(locationData)
        });
        
        return this.handleResponse(response);
    }

    /**
     * Get nearby safe zones
     */
    async getSafeZones(latitude, longitude, radius = 2000) {
        const params = new URLSearchParams({
            latitude: latitude.toString(),
            longitude: longitude.toString(),
            radius: radius.toString()
        });
        
        const response = await fetch(`${this.baseUrl}/safety/safe-zones?${params}`, {
            method: 'GET',
            headers: this.getHeaders()
        });
        
        return this.handleResponse(response);
    }

    /**
     * Report crime/incident
     */
    async reportCrime(reportData) {
        const response = await fetch(`${this.baseUrl}/safety/report-crime`, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify(reportData)
        });
        
        return this.handleResponse(response);
    }

    /**
     * Get crime reports for area
     */
    async getCrimeReports(latitude, longitude, radius = 2000) {
        const params = new URLSearchParams({
            latitude: latitude.toString(),
            longitude: longitude.toString(),
            radius: radius.toString()
        });
        
        const response = await fetch(`${this.baseUrl}/safety/crime-reports?${params}`, {
            method: 'GET',
            headers: this.getHeaders()
        });
        
        return this.handleResponse(response);
    }

    /**
     * Update location
     */
    async updateLocation(locationData) {
        const response = await fetch(`${this.baseUrl}/safety/location`, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify(locationData)
        });
        
        return this.handleResponse(response);
    }

    /**
     * Get location history
     */
    async getLocationHistory(limit = 50) {
        const response = await fetch(`${this.baseUrl}/safety/location/history?limit=${limit}`, {
            method: 'GET',
            headers: this.getHeaders()
        });
        
        return this.handleResponse(response);
    }
}

// Create global API instance
const api = new APIService();
