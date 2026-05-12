/**
 * SafeHer - Contacts Module
 * Handles emergency contacts management
 */

class ContactsManager {
    constructor() {
        this.contacts = [];
        this.editingContactId = null;
        this.init();
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        // Add contact buttons
        const addContactBtn = document.getElementById('add-contact-btn');
        const addFirstContact = document.getElementById('add-first-contact');

        if (addContactBtn) {
            addContactBtn.addEventListener('click', () => this.showAddContactModal());
        }

        if (addFirstContact) {
            addFirstContact.addEventListener('click', () => this.showAddContactModal());
        }

        // Modal close buttons
        const closeModalBtn = document.getElementById('close-contact-modal');
        const cancelContactBtn = document.getElementById('cancel-contact');

        if (closeModalBtn) {
            closeModalBtn.addEventListener('click', () => this.hideContactModal());
        }

        if (cancelContactBtn) {
            cancelContactBtn.addEventListener('click', () => this.hideContactModal());
        }

        // Contact form submission
        const contactForm = document.getElementById('contact-form');
        if (contactForm) {
            contactForm.addEventListener('submit', (e) => this.handleContactSubmit(e));
        }

        // Close modal on outside click
        const modal = document.getElementById('contact-modal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.hideContactModal();
                }
            });
        }
    }

    async loadContacts() {
        try {
            this.contacts = await api.getEmergencyContacts();
            this.renderContacts();
        } catch (error) {
            console.error('Failed to load contacts:', error);
            this.renderContacts(); // Render empty state
        }
    }

    renderContacts() {
        const contactsList = document.getElementById('contacts-list');
        const noContacts = document.getElementById('no-contacts');

        if (!this.contacts || this.contacts.length === 0) {
            contactsList.innerHTML = '';
            noContacts.classList.remove('hidden');
            return;
        }

        noContacts.classList.add('hidden');
        
        contactsList.innerHTML = this.contacts.map(contact => `
            <div class="contact-card" data-id="${contact.id}">
                <div class="contact-avatar">
                    <i class="fas fa-user"></i>
                </div>
                <div class="contact-info">
                    <span class="contact-name">
                        ${contact.name}
                        ${contact.is_primary ? '<span class="primary-badge">Primary</span>' : ''}
                    </span>
                    <span class="contact-phone">${contact.phone}</span>
                    ${contact.relationship ? `<span class="contact-relationship">${contact.relationship}</span>` : ''}
                </div>
                <div class="contact-actions">
                    <button class="edit-contact" title="Edit">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="delete delete-contact" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');

        // Bind edit and delete events
        contactsList.querySelectorAll('.edit-contact').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const contactId = e.target.closest('.contact-card').dataset.id;
                this.showEditContactModal(contactId);
            });
        });

        contactsList.querySelectorAll('.delete-contact').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const contactId = e.target.closest('.contact-card').dataset.id;
                this.deleteContact(contactId);
            });
        });
    }

    showAddContactModal() {
        this.editingContactId = null;
        const modal = document.getElementById('contact-modal');
        const title = document.getElementById('contact-modal-title');
        const form = document.getElementById('contact-form');

        title.textContent = 'Add Emergency Contact';
        form.reset();
        
        // Set default values
        document.getElementById('contact-sos').checked = true;
        document.getElementById('contact-location').checked = true;

        modal.classList.remove('hidden');
    }

    showEditContactModal(contactId) {
        const contact = this.contacts.find(c => c.id === contactId);
        if (!contact) return;

        this.editingContactId = contactId;
        const modal = document.getElementById('contact-modal');
        const title = document.getElementById('contact-modal-title');

        title.textContent = 'Edit Emergency Contact';

        // Fill form with contact data
        document.getElementById('contact-id').value = contact.id;
        document.getElementById('contact-name').value = contact.name;
        document.getElementById('contact-phone').value = contact.phone;
        document.getElementById('contact-email').value = contact.email || '';
        document.getElementById('contact-relationship').value = contact.relationship || '';
        document.getElementById('contact-primary').checked = contact.is_primary;
        document.getElementById('contact-sos').checked = contact.notify_on_sos;
        document.getElementById('contact-location').checked = contact.share_location;

        modal.classList.remove('hidden');
    }

    hideContactModal() {
        const modal = document.getElementById('contact-modal');
        modal.classList.add('hidden');
        this.editingContactId = null;
    }

    async handleContactSubmit(e) {
        e.preventDefault();

        const contactData = {
            name: document.getElementById('contact-name').value,
            phone: document.getElementById('contact-phone').value,
            email: document.getElementById('contact-email').value || null,
            relationship: document.getElementById('contact-relationship').value || null,
            is_primary: document.getElementById('contact-primary').checked,
            notify_on_sos: document.getElementById('contact-sos').checked,
            share_location: document.getElementById('contact-location').checked
        };

        const submitBtn = e.target.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Saving...';

        try {
            if (this.editingContactId) {
                await api.updateEmergencyContact(this.editingContactId, contactData);
                showToast('Contact updated successfully', 'success');
            } else {
                await api.addEmergencyContact(contactData);
                showToast('Contact added successfully', 'success');
            }

            this.hideContactModal();
            await this.loadContacts();
        } catch (error) {
            showToast(error.message || 'Failed to save contact', 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Save Contact';
        }
    }

    async deleteContact(contactId) {
        const confirmed = confirm('Are you sure you want to delete this contact?');
        if (!confirmed) return;

        try {
            await api.deleteEmergencyContact(contactId);
            showToast('Contact deleted successfully', 'success');
            await this.loadContacts();
        } catch (error) {
            showToast(error.message || 'Failed to delete contact', 'error');
        }
    }
}

// Create global contacts manager instance
const contacts = new ContactsManager();
