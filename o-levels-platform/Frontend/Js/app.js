const API_BASE = "http://192.168.0.35:5000/api";

// Main Application
const app = {
    // App state
    state: {
        currentUser: null,
        subjects: [],
        currentSubject: null,
        resources: {},
        theme: 'light'
    },

    // Initialize the application
init() {
    this.loadTheme();
    this.setupEventListeners();
    this.router.init();
    
    // Load data and hide loading screen
    Promise.all([
        this.checkAuth(),
        this.loadSubjects()
    ]).finally(() => {
        // Always hide loading screen after 1 second
        setTimeout(() => {
            document.getElementById('loading-screen').style.display = 'none';
        }, 1000);
    });
},

    // Load theme from localStorage
    loadTheme() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        this.state.theme = savedTheme;
        document.documentElement.setAttribute('data-theme', savedTheme);
        this.updateThemeToggle();
    },

    // Toggle theme
    toggleTheme() {
        this.state.theme = this.state.theme === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', this.state.theme);
        localStorage.setItem('theme', this.state.theme);
        this.updateThemeToggle();
    },

    // Update theme toggle button
    updateThemeToggle() {
        const toggle = document.getElementById('theme-toggle');
        const icon = toggle.querySelector('i');
        icon.className = this.state.theme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
    },
async handleSignup() {
    const username = 'student';
    const password = 'student123';
    const email = 'student@school.com';
    const full_name = 'Demo Student';

    try {
        const response = await fetch('http://localhost:5000/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, email, full_name }),
            credentials: 'include'
        });

        const data = await response.json();
        
        if (data.success) {
            this.showToast('Account created! Use: student/student123', 'success');
        } else {
            this.showToast(data.error || 'Signup failed', 'error');
        }
    } catch (error) {
        this.showToast('Network error', 'error');
    }
},
    // Setup event listeners
    setupEventListeners() {

        document.getElementById('show-register').addEventListener('click', (e) => {
    e.preventDefault();
    this.handleSignup();
});

        // Theme toggle
        document.getElementById('theme-toggle').addEventListener('click', () => {
            this.toggleTheme();
        });

        // Sidebar toggle
        document.getElementById('sidebar-toggle').addEventListener('click', () => {
            document.getElementById('sidebar').classList.toggle('active');
        });

        // Logout
        document.getElementById('logout-btn').addEventListener('click', () => {
            this.logout();
        });

        // Login form
        document.getElementById('login-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });

        // Test maker form
        document.getElementById('test-maker-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleTestGeneration();
        });

        // Test maker navigation
        document.getElementById('next-to-step2').addEventListener('click', () => {
            this.nextTestStep(2);
        });
        document.getElementById('next-to-step3').addEventListener('click', () => {
            this.nextTestStep(3);
        });
        document.getElementById('next-to-step4').addEventListener('click', () => {
            this.nextTestStep(4);
        });
        document.getElementById('back-to-step1').addEventListener('click', () => {
            this.previousTestStep(1);
        });
        document.getElementById('back-to-step2').addEventListener('click', () => {
            this.previousTestStep(2);
        });
        document.getElementById('back-to-step3').addEventListener('click', () => {
            this.previousTestStep(3);
        });

        // Resource tabs
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('tab-btn')) {
                this.switchResourceTab(e.target.dataset.tab);
            }
        });

        // Global search
        document.getElementById('global-search').addEventListener('input', (e) => {
            this.handleSearch(e.target.value);
        });
    },

    // Check authentication status
  async checkAuth() {
    try {
        const response = await fetch('http://localhost:5000/api/auth/me', {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            this.state.currentUser = data.user;
            this.updateUI();
            return true;
        } else {
            this.showAuthModal();
            return false;
        }
    } catch (error) {
        console.log('Not authenticated, showing login modal');
        this.showAuthModal();
        return false;
    }
},
    // Handle user login
 async handleLogin() {
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    try {
        const response = await fetch('http://localhost:5000/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
            credentials: 'include'
        });

        const data = await response.json();

        if (data.success) {
            this.state.currentUser = data.user;
            this.hideAuthModal();
            this.updateUI();
            this.showToast('Login successful!', 'success');
            this.router.navigate('dashboard');
            
            // Reload subjects after login
            this.loadSubjects();
        } else {
            this.showToast(data.error || 'Login failed', 'error');
        }
    } catch (error) {
        this.showToast('Network error. Please try again.', 'error');
    }
},
    // Handle user logout
    async logout() {
        try {
            await fetch(`${API_BASE}/auth/logout`, { method: 'POST' });
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            this.state.currentUser = null;
            this.showAuthModal();
            this.showToast('Logged out successfully', 'success');
        }
    },

    // Load subjects from backend
async loadSubjects() {
    try {
        const response = await fetch('http://localhost:5000/api/subjects');
        if (response.ok) {
            const data = await response.json();
            this.state.subjects = data.subjects || [];
            this.renderSubjects();
        }
    } catch (error) {
        console.log('Using demo subjects data');
        // Fallback to demo data
        this.state.subjects = this.getDemoSubjects();
        this.renderSubjects();
    }
},

getDemoSubjects() {
    return [
        { id: 1, name: 'Mathematics', code: 'maths', description: 'Comprehensive mathematics curriculum', icon: 'calculator', color: '#ff6b6b' },
        { id: 2, name: 'Computer Science', code: 'computer', description: 'Programming and algorithms', icon: 'laptop-code', color: '#4ecdc4' },
        { id: 3, name: 'Chemistry', code: 'chemistry', description: 'Elements and compounds', icon: 'flask', color: '#45b7d1' },
        { id: 4, name: 'Physics', code: 'physics', description: 'Laws of the universe', icon: 'atom', color: '#ffa726' },
        { id: 5, name: 'English', code: 'english', description: 'Language and literature', icon: 'book-open', color: '#ba68c8' },
        { id: 6, name: 'Islamiat', code: 'islamiat', description: 'Islamic studies', icon: 'mosque', color: '#66bb6a' },
        { id: 7, name: 'Pakistan Studies', code: 'pst', description: 'History and geography', icon: 'globe-asia', color: '#78909c' }
    ];
},

    // Render subjects grid
    renderSubjects() {
        const grid = document.getElementById('subjects-grid');
        if (!grid) return;

        grid.innerHTML = this.state.subjects.map(subject => `
            <div class="subject-card ${subject.code.toLowerCase()}" onclick="app.router.navigate('subject-detail', '${subject.code.toLowerCase()}')">
                <div class="subject-card-header">
                    <i class="fas fa-${subject.icon}"></i>
                </div>
                <div class="subject-card-body">
                    <h3 class="subject-card-title">${subject.name}</h3>
                    <p class="subject-card-description">${subject.description}</p>
                    <div class="subject-progress">
                        <div class="progress-label">
                            <span>Progress</span>
                            <span>65%</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: 65%"></div>
                        </div>
                    </div>
                    <div class="subject-stats">
                        <div class="stat-item">
                            <span class="stat-number">24</span>
                            <span class="stat-label">Topics</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-number">156</span>
                            <span class="stat-label">Resources</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-number">12</span>
                            <span class="stat-label">Tests</span>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    },

    // Load subject details
    async loadSubjectDetail(subjectCode) {
        try {
            const response = await fetch(`${API_BASE}/subjects/${subjectCode}`);
            if (response.ok) {
                const data = await response.json();
                this.state.currentSubject = data.subject;
                this.state.resources = data.resources;
                this.renderSubjectDetail();
            }
        } catch (error) {
            console.error('Failed to load subject details:', error);
        }
    },

    // Render subject detail view
    renderSubjectDetail() {
        const subject = this.state.currentSubject;
        if (!subject) return;

        // Update header
        const header = document.getElementById('subject-detail-header');
        header.innerHTML = `
            <div class="subject-icon-large">
                <i class="fas fa-${subject.icon}"></i>
            </div>
            <h1 class="subject-title-large">${subject.name}</h1>
            <p class="subject-description-large">${subject.description}</p>
        `;

        // Render resources for each tab
        this.renderResources('notes');
        this.renderResources('videos');
        this.renderResources('questions');
        this.renderResources('past-papers');
    },

    // Render resources for a specific type
    renderResources(type) {
        const grid = document.getElementById(`${type}-grid`);
        if (!grid) return;

        const resources = this.state.resources[type] || [];
        
        if (resources.length === 0) {
            grid.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">
                        <i class="fas fa-inbox"></i>
                    </div>
                    <h3 class="empty-state-title">No ${type} available</h3>
                    <p class="empty-state-description">Check back later for new resources</p>
                </div>
            `;
            return;
        }

        grid.innerHTML = resources.map(resource => `
            <div class="resource-card">
                <div class="resource-icon">
                    <i class="fas fa-${this.getResourceIcon(type)}"></i>
                </div>
                <h4 class="resource-title">${resource.title}</h4>
                <p class="resource-description">${resource.description || 'No description available'}</p>
                <div class="resource-meta">
                    <span><i class="fas fa-file"></i> ${resource.file_size || 'N/A'}</span>
                    <span><i class="fas fa-clock"></i> ${resource.duration || 'N/A'}</span>
                </div>
                <div class="resource-actions">
                    <button class="btn btn-primary btn-sm" onclick="app.downloadResource(${resource.id})">
                        <i class="fas fa-download"></i> Download
                    </button>
                    <button class="btn btn-secondary btn-sm">
                        <i class="fas fa-eye"></i> Preview
                    </button>
                </div>
            </div>
        `).join('');
    },

    // Get icon for resource type
    getResourceIcon(type) {
        const icons = {
            'notes': 'file-alt',
            'videos': 'play-circle',
            'questions': 'question-circle',
            'past-papers': 'paste'
        };
        return icons[type] || 'file';
    },

    // Switch resource tabs
    switchResourceTab(tab) {
        // Update active tab
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tab}"]`).classList.add('active');

        // Update active content
        document.querySelectorAll('.resource-section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(`${tab}-content`).classList.add('active');
    },

    // Test maker navigation
    nextTestStep(step) {
        this.updateTestSteps(step);
    },

    previousTestStep(step) {
        this.updateTestSteps(step);
    },

    updateTestSteps(activeStep) {
        // Update step indicators
        document.querySelectorAll('.test-step').forEach((step, index) => {
            step.classList.remove('active', 'completed');
            if (index + 1 === activeStep) {
                step.classList.add('active');
            } else if (index + 1 < activeStep) {
                step.classList.add('completed');
            }
        });

        // Update form steps
        document.querySelectorAll('.form-step').forEach(step => {
            step.classList.remove('active');
        });
        document.getElementById(`step${activeStep}-form`).classList.add('active');
    },

    // Handle test generation
    async handleTestGeneration() {
        const formData = new FormData(document.getElementById('test-maker-form'));
        const testData = {
            subject_id: formData.get('subject'),
            paper: formData.get('paper'),
            difficulty: formData.get('difficulty'),
            total_marks: document.getElementById('total-marks').value,
            question_types: Array.from(document.querySelectorAll('input[name="question-type"]:checked')).map(input => input.value)
        };

        try {
            const response = await fetch(`${API_BASE}/tests/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(testData),
            });

            const data = await response.json();

            if (data.success) {
                this.showToast('Test generated successfully!', 'success');
                // Here you would typically redirect to the test taking interface
                console.log('Generated test:', data);
            } else {
                this.showToast(data.error || 'Failed to generate test', 'error');
            }
        } catch (error) {
            this.showToast('Network error. Please try again.', 'error');
        }
    },

    // Download resource
    async downloadResource(resourceId) {
        try {
            const response = await fetch(`${API_BASE}/resources/${resourceId}/download`);
            if (response.ok) {
                // Create a temporary link to trigger download
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `resource-${resourceId}.pdf`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                this.showToast('Download started', 'success');
            } else {
                this.showToast('Failed to download resource', 'error');
            }
        } catch (error) {
            this.showToast('Network error. Please try again.', 'error');
        }
    },

    // Handle global search
    handleSearch(query) {
        if (query.length < 2) return;
        
        // Implement search functionality
        console.log('Searching for:', query);
        // This would typically make an API call to search endpoints
    },

    // Update UI based on user state
    updateUI() {
        if (this.state.currentUser) {
            document.getElementById('user-name').textContent = this.state.currentUser.full_name || this.state.currentUser.username;
            document.getElementById('welcome-user').textContent = this.state.currentUser.full_name || this.state.currentUser.username;
            document.getElementById('user-avatar').innerHTML = `<i class="fas fa-user"></i>`;
        }
    },

    // Show authentication modal
    showAuthModal() {
        document.getElementById('auth-modal').classList.add('active');
    },
hideLoading() {
    const loader = document.getElementById('loading');
    if (loader) loader.style.display = 'none';
},

    // Hide authentication modal
    hideAuthModal() {
        document.getElementById('auth-modal').classList.remove('active');
    },

    // Show toast notification
    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <i class="fas fa-${this.getToastIcon(type)}"></i>
            <span>${message}</span>
        `;
        
        container.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    },

    // Get icon for toast type
    getToastIcon(type) {
        const icons = {
            'success': 'check-circle',
            'error': 'exclamation-circle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }
};

// Router for SPA navigation - FIXED VERSION
// SIMPLE ROUTER FIX
app.router = {
    init() {
        this.handleRoute();
        
        window.addEventListener('popstate', () => this.handleRoute());
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-route]')) {
                e.preventDefault();
                const route = e.target.getAttribute('data-route');
                this.navigate(route);
            }
        });
    },

    navigate(route) {
        window.location.hash = route;
        this.handleRoute();
    },

    handleRoute() {
        const route = window.location.hash.slice(1) || 'dashboard';
        
        // Hide all views
        document.querySelectorAll('.content-view').forEach(view => {
            view.classList.remove('active');
        });
        
        // Show current view
        const viewId = route + '-view';
        document.getElementById(viewId)?.classList.add('active');
        
        // Update nav
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-route="${route}"]`)?.classList.add('active');
        
        // Update title
        document.getElementById('page-title').textContent = 
            route.charAt(0).toUpperCase() + route.slice(1);
    }
};

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    app.init();
});

// Export for global access
window.app = app;