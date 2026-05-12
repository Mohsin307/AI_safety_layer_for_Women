/**
 * SafeHer - Main Application
 * Core application functionality
 */

class App {
    constructor() {
        this.currentPage = 'home';
        this.currentLocation = null;
        this.riskLevel = 'low';
        this.init();
    }

    async init() {
        // Show loading screen
        await this.showLoadingScreen();

        // Check authentication
        if (auth.isAuthenticated()) {
            await this.loadUserData();
            this.showApp();
        } else {
            this.showAuth();
        }

        this.bindEvents();
        this.startLocationTracking();
    }

    async showLoadingScreen() {
        return new Promise((resolve) => {
            setTimeout(() => {
                const loadingScreen = document.getElementById('loading-screen');
                loadingScreen.classList.add('fade-out');
                setTimeout(() => {
                    loadingScreen.classList.add('hidden');
                    resolve();
                }, 500);
            }, 2000);
        });
    }

    showAuth() {
        document.getElementById('auth-container').classList.remove('hidden');
        document.getElementById('app-container').classList.add('hidden');
    }

    showApp() {
        document.getElementById('auth-container').classList.add('hidden');
        document.getElementById('app-container').classList.remove('hidden');
        this.updateUserUI();
        this.loadHomeData();
    }

    async loadUserData() {
        try {
            const user = await api.getCurrentUser();
            auth.user = user;
            localStorage.setItem('user', JSON.stringify(user));
        } catch (error) {
            console.error('Failed to load user data:', error);
            // If unauthorized, show auth
            if (!auth.isAuthenticated()) {
                this.showAuth();
            }
        }
    }

    updateUserUI() {
        const user = auth.getUser();
        if (user) {
            document.getElementById('nav-user-name').textContent = user.full_name;
            document.getElementById('nav-user-email').textContent = user.email;
            
            // Update settings page
            const settingsName = document.getElementById('settings-name');
            const settingsEmail = document.getElementById('settings-email');
            const settingsPhone = document.getElementById('settings-phone');
            
            if (settingsName) settingsName.value = user.full_name;
            if (settingsEmail) settingsEmail.value = user.email;
            if (settingsPhone) settingsPhone.value = user.phone;
            
            // Update safety settings toggles
            const autoSos = document.getElementById('auto-sos');
            const silentMode = document.getElementById('silent-mode');
            const locationSharing = document.getElementById('location-sharing');
            
            if (autoSos) autoSos.checked = user.auto_sos_enabled;
            if (silentMode) silentMode.checked = user.silent_mode_enabled;
            if (locationSharing) locationSharing.checked = user.location_sharing_enabled;
        }
    }

    bindEvents() {
        // Menu toggle
        const menuToggle = document.getElementById('menu-toggle');
        const sideNav = document.getElementById('side-nav');
        const navOverlay = document.getElementById('nav-overlay');

        menuToggle.addEventListener('click', () => {
            sideNav.classList.toggle('open');
            navOverlay.classList.toggle('active');
        });

        navOverlay.addEventListener('click', () => {
            sideNav.classList.remove('open');
            navOverlay.classList.remove('active');
        });

        // Navigation items
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', () => {
                const page = item.dataset.page;
                this.navigateTo(page);
                sideNav.classList.remove('open');
                navOverlay.classList.remove('active');
            });
        });

        // View all links
        document.querySelectorAll('.view-all').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = link.dataset.page;
                this.navigateTo(page);
            });
        });

        // SOS Button
        this.initSOSButton();

        // Quick Actions
        this.initQuickActions();

        // Settings save
        const saveSettings = document.getElementById('save-settings');
        if (saveSettings) {
            saveSettings.addEventListener('click', () => this.saveSettings());
        }
    }

    navigateTo(page) {
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.toggle('active', item.dataset.page === page);
        });

        // Show page
        document.querySelectorAll('.page').forEach(p => {
            p.classList.remove('active');
        });
        document.getElementById(`page-${page}`).classList.add('active');

        this.currentPage = page;

        // Load page-specific data
        switch (page) {
            case 'contacts':
                contacts.loadContacts();
                break;
            case 'safety':
                safety.loadSafetyData();
                break;
            case 'history':
                this.loadHistory();
                break;
        }
    }

    initSOSButton() {
        const sosButton = document.getElementById('sos-button');
        let pressTimer = null;
        let isPressing = false;

        sosButton.addEventListener('mousedown', () => startPress());
        sosButton.addEventListener('touchstart', (e) => {
            e.preventDefault();
            startPress();
        });

        sosButton.addEventListener('mouseup', () => cancelPress());
        sosButton.addEventListener('mouseleave', () => cancelPress());
        sosButton.addEventListener('touchend', () => cancelPress());
        sosButton.addEventListener('touchcancel', () => cancelPress());

        const startPress = () => {
            isPressing = true;
            sosButton.classList.add('active');
            
            pressTimer = setTimeout(() => {
                if (isPressing) {
                    emergency.triggerEmergency('manual_sos');
                }
            }, 3000);
        };

        const cancelPress = () => {
            isPressing = false;
            sosButton.classList.remove('active');
            if (pressTimer) {
                clearTimeout(pressTimer);
                pressTimer = null;
            }
        };
    }

    initQuickActions() {
        // Silent SOS
        document.getElementById('action-silent-sos').addEventListener('click', () => {
            emergency.triggerEmergency('silent_sos');
        });

        // Fake Call
        document.getElementById('action-fake-call').addEventListener('click', () => {
            emergency.showFakeCall();
        });

        // Share Location
        document.getElementById('action-share-location').addEventListener('click', () => {
            this.shareLocation();
        });

        // Record
        document.getElementById('action-record').addEventListener('click', () => {
            this.startRecording();
        });
    }

    async startLocationTracking() {
        if ('geolocation' in navigator) {
            // Get initial location
            navigator.geolocation.getCurrentPosition(
                (position) => this.updateLocation(position),
                (error) => console.error('Location error:', error),
                { enableHighAccuracy: true }
            );

            // Watch location changes
            navigator.geolocation.watchPosition(
                (position) => this.updateLocation(position),
                (error) => console.error('Location watch error:', error),
                { enableHighAccuracy: true, maximumAge: 30000 }
            );
        }
    }

    async updateLocation(position) {
        this.currentLocation = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy
        };

        // Update UI
        const locationElement = document.getElementById('current-location');
        if (locationElement) {
            // Reverse geocode to get address
            const address = await this.reverseGeocode(
                position.coords.latitude,
                position.coords.longitude
            );
            locationElement.textContent = address || `${position.coords.latitude.toFixed(4)}, ${position.coords.longitude.toFixed(4)}`;
        }

        // Update risk assessment if authenticated
        if (auth.isAuthenticated()) {
            this.assessRisk();
        }
    }

    async reverseGeocode(lat, lng) {
        try {
            const response = await fetch(
                `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json`
            );
            const data = await response.json();
            
            if (data.address) {
                const parts = [];
                if (data.address.road) parts.push(data.address.road);
                if (data.address.suburb) parts.push(data.address.suburb);
                if (data.address.city || data.address.town) {
                    parts.push(data.address.city || data.address.town);
                }
                return parts.join(', ') || data.display_name;
            }
        } catch (error) {
            console.error('Geocoding error:', error);
        }
        return null;
    }

    async assessRisk() {
        if (!this.currentLocation) return;

        try {
            const result = await api.assessRisk({
                location: this.currentLocation,
                include_safe_zones: true
            });

            this.updateRiskIndicator(result.risk_level);
            
            // Update safe zones
            if (result.nearby_safe_zones) {
                this.updateSafeZones(result.nearby_safe_zones);
            }
        } catch (error) {
            console.error('Risk assessment error:', error);
        }
    }

    updateRiskIndicator(level) {
        this.riskLevel = level;
        const indicator = document.getElementById('risk-indicator');
        const riskText = indicator.querySelector('.risk-text');
        const statusBadge = document.getElementById('status-badge');
        const riskLevelText = document.getElementById('risk-level');

        // Remove all risk classes
        indicator.classList.remove('medium', 'high', 'critical');
        statusBadge.classList.remove('safe', 'warning', 'danger');

        // Set appropriate class
        switch (level) {
            case 'low':
                riskText.textContent = 'Safe';
                statusBadge.textContent = 'Safe';
                statusBadge.classList.add('safe');
                riskLevelText.textContent = 'Low';
                riskLevelText.className = 'value risk-level low';
                break;
            case 'medium':
                indicator.classList.add('medium');
                riskText.textContent = 'Caution';
                statusBadge.textContent = 'Caution';
                statusBadge.classList.add('warning');
                riskLevelText.textContent = 'Medium';
                riskLevelText.className = 'value risk-level medium';
                break;
            case 'high':
                indicator.classList.add('high');
                riskText.textContent = 'High Risk';
                statusBadge.textContent = 'High Risk';
                statusBadge.classList.add('danger');
                riskLevelText.textContent = 'High';
                riskLevelText.className = 'value risk-level high';
                break;
            case 'critical':
                indicator.classList.add('critical');
                riskText.textContent = 'DANGER';
                statusBadge.textContent = 'DANGER';
                statusBadge.classList.add('danger');
                riskLevelText.textContent = 'Critical';
                riskLevelText.className = 'value risk-level critical';
                break;
        }

        // Update last check time
        document.getElementById('last-check').textContent = 'Just now';
    }

    updateSafeZones(zones) {
        const container = document.getElementById('safe-zones-list');
        if (!container) return;

        if (zones.length === 0) {
            container.innerHTML = '<p class="no-data">No nearby safe zones found</p>';
            return;
        }

        container.innerHTML = zones.slice(0, 3).map(zone => `
            <div class="zone-item">
                <div class="zone-icon ${zone.type}">
                    <i class="fas fa-${this.getZoneIcon(zone.type)}"></i>
                </div>
                <div class="zone-info">
                    <span class="zone-name">${zone.name}</span>
                    <span class="zone-distance">${zone.distance || 'Nearby'}</span>
                </div>
            </div>
        `).join('');
    }

    getZoneIcon(type) {
        const icons = {
            police: 'shield-alt',
            hospital: 'hospital',
            'safe-zone': 'map-pin',
            default: 'location-arrow'
        };
        return icons[type] || icons.default;
    }

    async loadHomeData() {
        // Load safe zones
        if (this.currentLocation) {
            try {
                const zones = await api.getSafeZones(
                    this.currentLocation.latitude,
                    this.currentLocation.longitude
                );
                this.updateSafeZones(zones);
            } catch (error) {
                console.error('Failed to load safe zones:', error);
            }
        }
    }

    async loadHistory() {
        try {
            const history = await api.getEmergencyHistory();
            const container = document.getElementById('history-list');
            
            if (!history || history.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-history"></i>
                        <h3>No History Yet</h3>
                        <p>Your activity history will appear here</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = history.map(item => `
                <div class="history-item">
                    <div class="history-icon ${item.type}">
                        <i class="fas fa-${this.getHistoryIcon(item.type)}"></i>
                    </div>
                    <div class="history-details">
                        <span class="history-title">${item.title || item.emergency_type}</span>
                        <span class="history-subtitle">${item.location || 'Unknown location'}</span>
                    </div>
                    <span class="history-time">${this.formatTime(item.created_at)}</span>
                </div>
            `).join('');
        } catch (error) {
            console.error('Failed to load history:', error);
        }
    }

    getHistoryIcon(type) {
        const icons = {
            emergency: 'exclamation-triangle',
            location: 'map-marker-alt',
            report: 'flag',
            default: 'clock'
        };
        return icons[type] || icons.default;
    }

    formatTime(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;

        if (diff < 60000) return 'Just now';
        if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
        return date.toLocaleDateString();
    }

    async shareLocation() {
        if (!this.currentLocation) {
            showToast('Location not available', 'error');
            return;
        }

        const shareText = `I'm sharing my location with you:\nhttps://www.google.com/maps?q=${this.currentLocation.latitude},${this.currentLocation.longitude}`;

        if (navigator.share) {
            try {
                await navigator.share({
                    title: 'My Location - SafeHer',
                    text: shareText
                });
                showToast('Location shared successfully', 'success');
            } catch (error) {
                if (error.name !== 'AbortError') {
                    this.copyToClipboard(shareText);
                }
            }
        } else {
            this.copyToClipboard(shareText);
        }
    }

    copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            showToast('Location link copied to clipboard', 'success');
        }).catch(() => {
            showToast('Failed to copy location', 'error');
        });
    }

    startRecording() {
        showToast('Recording feature coming soon', 'info');
        // TODO: Implement audio/video recording
    }

    async saveSettings() {
        const userData = {
            full_name: document.getElementById('settings-name').value,
            phone: document.getElementById('settings-phone').value,
            blood_group: document.getElementById('blood-group').value,
            medical_conditions: document.getElementById('medical-conditions').value,
            auto_sos_enabled: document.getElementById('auto-sos').checked,
            silent_mode_enabled: document.getElementById('silent-mode').checked,
            location_sharing_enabled: document.getElementById('location-sharing').checked
        };

        try {
            await api.updateProfile(userData);
            auth.user = { ...auth.user, ...userData };
            localStorage.setItem('user', JSON.stringify(auth.user));
            this.updateUserUI();
            showToast('Settings saved successfully', 'success');
        } catch (error) {
            showToast(error.message || 'Failed to save settings', 'error');
        }
    }
}

// Toast notification function
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = {
        success: 'check',
        error: 'times',
        warning: 'exclamation',
        info: 'info'
    };

    toast.innerHTML = `
        <div class="toast-icon">
            <i class="fas fa-${icons[type]}"></i>
        </div>
        <span class="toast-message">${message}</span>
        <button class="toast-close">
            <i class="fas fa-times"></i>
        </button>
    `;

    container.appendChild(toast);

    // Close button
    toast.querySelector('.toast-close').addEventListener('click', () => {
        toast.remove();
    });

    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.style.animation = 'toastSlideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});
