/**
 * SafeHer - Safety Module
 * Handles safety map and safe zones
 */

class SafetyManager {
    constructor() {
        this.map = null;
        this.markers = [];
        this.safeZones = [];
        this.currentFilter = 'all';
        this.init();
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        // Filter buttons
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.currentFilter = btn.dataset.filter;
                this.filterPlaces();
            });
        });

        // History tabs
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                // Load different history based on tab
            });
        });
    }

    async loadSafetyData() {
        this.initMap();
        await this.loadNearbyPlaces();
    }

    initMap() {
        const container = document.getElementById('map-container');
        
        // Check if we have a location
        if (!app.currentLocation) {
            container.innerHTML = `
                <div class="map-placeholder">
                    <i class="fas fa-map-marked-alt"></i>
                    <p>Enable location to view map</p>
                </div>
            `;
            return;
        }

        // Create a simple map visualization using OpenStreetMap embed
        const { latitude, longitude } = app.currentLocation;
        container.innerHTML = `
            <iframe 
                width="100%" 
                height="100%" 
                frameborder="0" 
                scrolling="no" 
                marginheight="0" 
                marginwidth="0" 
                src="https://www.openstreetmap.org/export/embed.html?bbox=${longitude - 0.02}%2C${latitude - 0.02}%2C${longitude + 0.02}%2C${latitude + 0.02}&layer=mapnik&marker=${latitude}%2C${longitude}"
                style="border-radius: 1rem;">
            </iframe>
        `;
    }

    async loadNearbyPlaces() {
        if (!app.currentLocation) return;

        const { latitude, longitude } = app.currentLocation;
        
        // Try to get safe zones from API
        try {
            this.safeZones = await api.getSafeZones(latitude, longitude);
        } catch (error) {
            console.error('Failed to load safe zones from API:', error);
            // Use sample data for demonstration
            this.safeZones = this.getSamplePlaces(latitude, longitude);
        }

        this.renderPlaces();
    }

    getSamplePlaces(lat, lng) {
        // Generate sample nearby places for demonstration
        return [
            {
                id: '1',
                name: 'City Police Station',
                type: 'police',
                latitude: lat + 0.005,
                longitude: lng + 0.003,
                distance: '500m',
                address: '123 Main St',
                contact_phone: '100'
            },
            {
                id: '2',
                name: 'General Hospital',
                type: 'hospital',
                latitude: lat - 0.004,
                longitude: lng + 0.006,
                distance: '800m',
                address: '456 Health Ave',
                contact_phone: '102'
            },
            {
                id: '3',
                name: 'Community Center',
                type: 'safe-zone',
                latitude: lat + 0.002,
                longitude: lng - 0.004,
                distance: '300m',
                address: '789 Community Rd',
                contact_phone: null
            },
            {
                id: '4',
                name: 'Women\'s Shelter',
                type: 'safe-zone',
                latitude: lat - 0.003,
                longitude: lng - 0.002,
                distance: '400m',
                address: '321 Safe Haven St',
                contact_phone: '1091'
            },
            {
                id: '5',
                name: 'Fire Station',
                type: 'police',
                latitude: lat + 0.008,
                longitude: lng - 0.005,
                distance: '1.2km',
                address: '555 Emergency Blvd',
                contact_phone: '101'
            },
            {
                id: '6',
                name: 'Medical Clinic',
                type: 'hospital',
                latitude: lat - 0.006,
                longitude: lng + 0.008,
                distance: '1km',
                address: '777 Care Lane',
                contact_phone: '102'
            }
        ];
    }

    renderPlaces() {
        const container = document.getElementById('nearby-places');
        const filteredPlaces = this.filterPlacesList();

        if (filteredPlaces.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-map-marker-alt"></i>
                    <h3>No Places Found</h3>
                    <p>No nearby places match your filter</p>
                </div>
            `;
            return;
        }

        container.innerHTML = filteredPlaces.map(place => `
            <div class="zone-item" data-id="${place.id}">
                <div class="zone-icon ${place.type}">
                    <i class="fas fa-${this.getPlaceIcon(place.type)}"></i>
                </div>
                <div class="zone-info">
                    <span class="zone-name">${place.name}</span>
                    <span class="zone-distance">${place.distance || 'Nearby'} • ${place.address || ''}</span>
                </div>
                ${place.contact_phone ? `
                    <a href="tel:${place.contact_phone}" class="icon-btn" title="Call">
                        <i class="fas fa-phone"></i>
                    </a>
                ` : ''}
                <button class="icon-btn" onclick="safety.getDirections(${place.latitude}, ${place.longitude})" title="Get Directions">
                    <i class="fas fa-directions"></i>
                </button>
            </div>
        `).join('');
    }

    filterPlacesList() {
        if (this.currentFilter === 'all') {
            return this.safeZones;
        }
        return this.safeZones.filter(place => place.type === this.currentFilter);
    }

    filterPlaces() {
        this.renderPlaces();
    }

    getPlaceIcon(type) {
        const icons = {
            'police': 'shield-alt',
            'hospital': 'hospital',
            'safe-zone': 'map-pin',
            'fire': 'fire-extinguisher',
            'default': 'location-arrow'
        };
        return icons[type] || icons.default;
    }

    getDirections(lat, lng) {
        const url = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`;
        window.open(url, '_blank');
    }

    async reportIncident() {
        if (!app.currentLocation) {
            showToast('Location not available', 'error');
            return;
        }

        // Show report modal (to be implemented)
        showToast('Incident reporting coming soon', 'info');
    }
}

// Create global safety manager instance
const safety = new SafetyManager();
