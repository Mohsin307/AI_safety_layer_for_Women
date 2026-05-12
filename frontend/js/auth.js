/**
 * SafeHer - Authentication Module
 * Handles user authentication
 */

class AuthManager {
    constructor() {
        this.user = null;
        this.init();
    }

    init() {
        // Check if user is logged in
        const savedUser = localStorage.getItem('user');
        if (savedUser) {
            this.user = JSON.parse(savedUser);
        }

        this.bindEvents();
    }

    bindEvents() {
        // Login form
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }

        // Register form
        const registerForm = document.getElementById('register-form');
        if (registerForm) {
            registerForm.addEventListener('submit', (e) => this.handleRegister(e));
        }

        // Toggle between login and register
        const showRegister = document.getElementById('show-register');
        const showLogin = document.getElementById('show-login');

        if (showRegister) {
            showRegister.addEventListener('click', (e) => {
                e.preventDefault();
                this.showPage('register');
            });
        }

        if (showLogin) {
            showLogin.addEventListener('click', (e) => {
                e.preventDefault();
                this.showPage('login');
            });
        }

        // Password toggle
        document.querySelectorAll('.toggle-password').forEach(btn => {
            btn.addEventListener('click', (e) => this.togglePassword(e));
        });

        // Logout button
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.logout());
        }
    }

    showPage(page) {
        const loginPage = document.getElementById('login-page');
        const registerPage = document.getElementById('register-page');

        if (page === 'login') {
            loginPage.classList.remove('hidden');
            registerPage.classList.add('hidden');
        } else {
            loginPage.classList.add('hidden');
            registerPage.classList.remove('hidden');
        }
    }

    togglePassword(e) {
        const btn = e.currentTarget;
        const input = btn.parentElement.querySelector('input');
        const icon = btn.querySelector('i');

        if (input.type === 'password') {
            input.type = 'text';
            icon.classList.remove('fa-eye');
            icon.classList.add('fa-eye-slash');
        } else {
            input.type = 'password';
            icon.classList.remove('fa-eye-slash');
            icon.classList.add('fa-eye');
        }
    }

    async handleLogin(e) {
        e.preventDefault();

        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        const submitBtn = e.target.querySelector('button[type="submit"]');

        // Disable button and show loading
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging in...';

        try {
            await api.login(email, password);
            
            // Get user profile
            const user = await api.getCurrentUser();
            this.user = user;
            localStorage.setItem('user', JSON.stringify(user));
            
            showToast('Login successful! Welcome back.', 'success');
            
            // Redirect to app
            setTimeout(() => {
                app.showApp();
            }, 500);
        } catch (error) {
            showToast(error.message || 'Login failed. Please check your credentials.', 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-sign-in-alt"></i> Login';
        }
    }

    async handleRegister(e) {
        e.preventDefault();

        const name = document.getElementById('register-name').value;
        const email = document.getElementById('register-email').value;
        const phone = document.getElementById('register-phone').value;
        const password = document.getElementById('register-password').value;
        const confirmPassword = document.getElementById('register-confirm').value;
        const submitBtn = e.target.querySelector('button[type="submit"]');

        // Validate passwords match
        if (password !== confirmPassword) {
            showToast('Passwords do not match', 'error');
            return;
        }

        // Validate password strength
        if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(password)) {
            showToast('Password must contain uppercase, lowercase, and number', 'error');
            return;
        }

        // Disable button and show loading
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating account...';

        try {
            await api.register({
                full_name: name,
                email: email,
                phone: phone,
                password: password
            });
            
            showToast('Account created successfully! Please login.', 'success');
            
            // Switch to login page
            this.showPage('login');
            document.getElementById('login-email').value = email;
            
            // Clear registration form
            e.target.reset();
        } catch (error) {
            showToast(error.message || 'Registration failed. Please try again.', 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-user-plus"></i> Create Account';
        }
    }

    async logout() {
        try {
            await api.logout();
        } catch (error) {
            console.error('Logout error:', error);
        }
        
        this.user = null;
        showToast('Logged out successfully', 'info');
        
        // Redirect to auth
        app.showAuth();
    }

    isAuthenticated() {
        return !!localStorage.getItem('accessToken');
    }

    getUser() {
        return this.user;
    }
}

// Create global auth manager instance
const auth = new AuthManager();
