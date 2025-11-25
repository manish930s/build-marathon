const API_BASE_URL = ""; // Relative path for production

// Switch between login and signup forms
function switchToSignup() {
    document.getElementById('login-form').classList.remove('active');
    document.getElementById('signup-form').classList.add('active');
}

function switchToLogin() {
    document.getElementById('signup-form').classList.remove('active');
    document.getElementById('login-form').classList.add('active');
}

// Handle Login
async function handleLogin() {
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;

    if (!username || !password) {
        showMessage('error', 'Please enter both username and password');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            // Store user session
            localStorage.setItem('username', data.username);
            localStorage.setItem('fullName', data.full_name);
            localStorage.setItem('role', data.role);

            showMessage('success', 'Login successful! Redirecting...');

            // Redirect to main app
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 1000);
        } else {
            showMessage('error', data.detail || 'Login failed');
        }
    } catch (error) {
        console.error('Login error:', error);
        showMessage('error', 'Connection error. Please try again.');
    }
}

// Handle Signup
async function handleSignup() {
    console.log('🔵 Signup button clicked!'); // Debug log

    const username = document.getElementById('signup-username').value.trim();
    const fullName = document.getElementById('signup-fullname').value.trim();
    const password = document.getElementById('signup-password').value;
    const confirmPassword = document.getElementById('signup-confirm-password').value;
    const role = document.getElementById('signup-role').value;

    console.log('📝 Form data:', { username, fullName, password: '***', role }); // Debug log

    // Validation
    if (!username || !fullName || !password || !confirmPassword) {
        console.log('❌ Validation failed: Missing fields');
        showMessage('error', 'Please fill in all fields');
        return;
    }

    if (username.length < 3) {
        console.log('❌ Validation failed: Username too short');
        showMessage('error', 'Username must be at least 3 characters');
        return;
    }

    if (password.length < 6) {
        console.log('❌ Validation failed: Password too short');
        showMessage('error', 'Password must be at least 6 characters');
        return;
    }

    if (password !== confirmPassword) {
        console.log('❌ Validation failed: Passwords do not match');
        showMessage('error', 'Passwords do not match');
        return;
    }

    console.log('✅ Validation passed, sending request...');

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/auth/signup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username,
                full_name: fullName,
                password,
                role
            })
        });

        const data = await response.json();
        console.log('📡 Server response:', data);

        if (response.ok) {
            console.log('✅ Signup successful!');
            showMessage('success', 'Account created! Please sign in.');

            // Switch to login form after 1.5 seconds
            setTimeout(() => {
                switchToLogin();
                // Pre-fill username
                document.getElementById('login-username').value = username;
            }, 1500);
        } else {
            console.log('❌ Signup failed:', data.detail);
            showMessage('error', data.detail || 'Signup failed');
        }
    } catch (error) {
        console.error('❌ Signup error:', error);
        showMessage('error', 'Connection error. Please try again.');
    }
}

// Show error/success messages
function showMessage(type, text) {
    // Remove existing messages
    const existingMessage = document.querySelector('.message');
    if (existingMessage) {
        existingMessage.remove();
    }

    // Create new message
    const message = document.createElement('div');
    message.className = `message ${type} show`;
    message.textContent = text;

    // Insert at the top of active form
    const activeForm = document.querySelector('.auth-form.active');
    activeForm.insertBefore(message, activeForm.firstChild);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        message.classList.remove('show');
        setTimeout(() => message.remove(), 300);
    }, 5000);
}

// Handle Enter key press
document.addEventListener('DOMContentLoaded', () => {
    // Login form enter key
    document.getElementById('login-password').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleLogin();
    });

    // Signup form enter key
    document.getElementById('signup-confirm-password').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSignup();
    });
});
