/**
 * SafeHer - Emergency Module
 * Handles emergency triggers and fake calls
 */

class EmergencyManager {
    constructor() {
        this.activeEmergency = null;
        this.emergencyTimer = null;
        this.emergencySeconds = 0;
        this.fakeCallTimer = null;
        this.fakeCallSeconds = 0;
        this.init();
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        // Emergency type cards
        document.querySelectorAll('.emergency-type-card').forEach(card => {
            card.addEventListener('click', () => {
                const type = card.dataset.type;
                this.triggerEmergency(type);
            });
        });

        // Cancel emergency
        const cancelBtn = document.getElementById('cancel-emergency');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.cancelEmergency());
        }

        // Fake call modal
        const declineBtn = document.getElementById('decline-fake-call');
        const acceptBtn = document.getElementById('accept-fake-call');
        const endBtn = document.getElementById('end-fake-call');

        if (declineBtn) {
            declineBtn.addEventListener('click', () => this.closeFakeCall());
        }

        if (acceptBtn) {
            acceptBtn.addEventListener('click', () => this.acceptFakeCall());
        }

        if (endBtn) {
            endBtn.addEventListener('click', () => this.closeFakeCall());
        }
    }

    async triggerEmergency(type) {
        // Confirm for non-silent emergencies
        if (type !== 'silent_sos') {
            const confirmed = confirm(`Are you sure you want to trigger ${type.replace('_', ' ')} emergency?`);
            if (!confirmed) return;
        }

        // Get current location
        const location = app.currentLocation || null;

        const emergencyData = {
            emergency_type: type,
            location: location,
            trigger_reason: `User triggered ${type}`,
            silent_mode: type === 'silent_sos'
        };

        try {
            showToast('Triggering emergency...', 'warning');
            
            const response = await api.triggerEmergency(emergencyData);
            
            this.activeEmergency = response;
            this.showActiveEmergency();
            this.startEmergencyTimer();

            if (type === 'silent_sos') {
                showToast('Silent SOS activated', 'warning');
            } else {
                showToast('Emergency triggered! Help is on the way.', 'error');
            }

            // Navigate to emergency page
            app.navigateTo('emergency');

        } catch (error) {
            showToast(error.message || 'Failed to trigger emergency', 'error');
        }
    }

    showActiveEmergency() {
        const activeSection = document.getElementById('active-emergency');
        const optionsSection = document.getElementById('emergency-options');
        const statusText = document.getElementById('emergency-status-text');

        activeSection.classList.remove('hidden');
        optionsSection.classList.add('hidden');

        // Update status
        this.updateEmergencyStatus('Alerting emergency contacts...');

        // Simulate status updates
        setTimeout(() => {
            this.updateEmergencyStatus('Contacts notified. Sharing location...');
        }, 3000);

        setTimeout(() => {
            this.updateEmergencyStatus('Location shared. Authorities alerted.');
        }, 6000);
    }

    hideActiveEmergency() {
        const activeSection = document.getElementById('active-emergency');
        const optionsSection = document.getElementById('emergency-options');

        activeSection.classList.add('hidden');
        optionsSection.classList.remove('hidden');
    }

    updateEmergencyStatus(status) {
        const statusText = document.getElementById('emergency-status-text');
        if (statusText) {
            statusText.textContent = status;
        }
    }

    startEmergencyTimer() {
        this.emergencySeconds = 0;
        const timerElement = document.getElementById('emergency-timer');

        this.emergencyTimer = setInterval(() => {
            this.emergencySeconds++;
            const minutes = Math.floor(this.emergencySeconds / 60);
            const seconds = this.emergencySeconds % 60;
            timerElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
    }

    stopEmergencyTimer() {
        if (this.emergencyTimer) {
            clearInterval(this.emergencyTimer);
            this.emergencyTimer = null;
        }
    }

    async cancelEmergency() {
        if (!this.activeEmergency) return;

        const confirmed = confirm('Are you sure you want to cancel this emergency?');
        if (!confirmed) return;

        try {
            await api.cancelEmergency(this.activeEmergency.id);
            
            this.stopEmergencyTimer();
            this.activeEmergency = null;
            this.hideActiveEmergency();
            
            showToast('Emergency cancelled', 'info');
        } catch (error) {
            showToast(error.message || 'Failed to cancel emergency', 'error');
        }
    }

    // Fake Call functionality
    showFakeCall() {
        const modal = document.getElementById('fake-call-modal');
        const incomingCall = modal.querySelector('.incoming-call');
        const activeCall = modal.querySelector('.active-call');

        modal.classList.remove('hidden');
        incomingCall.classList.remove('hidden');
        activeCall.classList.add('hidden');

        // Play ringtone sound (if available)
        this.playRingtone();

        // Vibrate phone
        if (navigator.vibrate) {
            this.vibratePattern = setInterval(() => {
                navigator.vibrate([200, 100, 200]);
            }, 2000);
        }
    }

    acceptFakeCall() {
        const modal = document.getElementById('fake-call-modal');
        const incomingCall = modal.querySelector('.incoming-call');
        const activeCall = modal.querySelector('.active-call');

        incomingCall.classList.add('hidden');
        activeCall.classList.remove('hidden');

        // Stop ringtone and vibration
        this.stopRingtone();
        if (this.vibratePattern) {
            clearInterval(this.vibratePattern);
            navigator.vibrate(0);
        }

        // Start call timer
        this.fakeCallSeconds = 0;
        const timerElement = modal.querySelector('.call-timer');

        this.fakeCallTimer = setInterval(() => {
            this.fakeCallSeconds++;
            const minutes = Math.floor(this.fakeCallSeconds / 60);
            const seconds = this.fakeCallSeconds % 60;
            timerElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
    }

    closeFakeCall() {
        const modal = document.getElementById('fake-call-modal');
        modal.classList.add('hidden');

        // Stop everything
        this.stopRingtone();
        
        if (this.vibratePattern) {
            clearInterval(this.vibratePattern);
            navigator.vibrate(0);
        }

        if (this.fakeCallTimer) {
            clearInterval(this.fakeCallTimer);
            this.fakeCallTimer = null;
        }
    }

    playRingtone() {
        // Create a simple ringtone using Web Audio API
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            const playTone = () => {
                if (!this.audioContext) return;
                
                const oscillator = this.audioContext.createOscillator();
                const gainNode = this.audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(this.audioContext.destination);
                
                oscillator.frequency.value = 440;
                oscillator.type = 'sine';
                
                gainNode.gain.setValueAtTime(0.3, this.audioContext.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + 0.5);
                
                oscillator.start(this.audioContext.currentTime);
                oscillator.stop(this.audioContext.currentTime + 0.5);
            };

            this.ringtoneInterval = setInterval(playTone, 1000);
            playTone();
        } catch (error) {
            console.error('Audio not supported:', error);
        }
    }

    stopRingtone() {
        if (this.ringtoneInterval) {
            clearInterval(this.ringtoneInterval);
            this.ringtoneInterval = null;
        }
        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }
    }
}

// Create global emergency manager instance
const emergency = new EmergencyManager();
