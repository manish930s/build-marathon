// Check authentication
const username = localStorage.getItem('username');
if (!username) {
    // Redirect to login if not authenticated
    window.location.href = 'auth.html';
}

const API_BASE_URL = ""; // Relative path for production deployment
const USERNAME = (username || "grandpa_joe").toLowerCase();

// --- Navigation ---
function showSection(sectionId) {
    document.querySelectorAll('.section').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));

    document.getElementById(sectionId).classList.add('active');

    // Highlight nav button
    const navBtn = Array.from(document.querySelectorAll('.nav-btn')).find(btn => btn.innerText.toLowerCase().includes(sectionId.replace('chat', 'companion')));
    if (navBtn) navBtn.classList.add('active');

    if (sectionId === 'dashboard') {
        loadDashboard();
    }
}

// --- Chat ---
const chatWindow = document.getElementById('chat-window');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');

function addMessage(text, sender) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender}`;
    msgDiv.innerHTML = `<div class="bubble">${text}</div>`;
    chatWindow.appendChild(msgDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    addMessage(text, 'user');
    userInput.value = '';

    // Add temporary thinking message
    const thinkingId = 'thinking-' + Date.now();
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message bot';
    msgDiv.id = thinkingId;
    msgDiv.innerHTML = `<div class="bubble" style="opacity:0.7">Thinking...</div>`;
    chatWindow.appendChild(msgDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: USERNAME, message: text })
        });
        const data = await response.json();

        // Remove thinking message
        const thinkingMsg = document.getElementById(thinkingId);
        if (thinkingMsg) thinkingMsg.remove();

        addMessage(data.response, 'bot');
    } catch (error) {
        // Remove thinking message
        const thinkingMsg = document.getElementById(thinkingId);
        if (thinkingMsg) thinkingMsg.remove();

        addMessage("Sorry, I'm having trouble connecting. Please try again.", 'bot');
        console.error(error);
    }
}

sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

// --- Dashboard ---
async function loadDashboard() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/${USERNAME}`);
        const data = await response.json();

        // Update Vitals (Simplified mapping)
        if (data.vitals && data.vitals.length > 0) {
            // Find latest of each type
            const latest = {};
            data.vitals.forEach(v => {
                if (!latest[v.type]) latest[v.type] = v;
            });

            updateStat('Heart Rate', latest['heart_rate']);

            // Handle Blood Pressure (Composite)
            const bpSys = latest['blood_pressure_sys'];
            const bpDia = latest['blood_pressure_dia'];

            const bpCard = Array.from(document.querySelectorAll('.stat-card')).find(c => c.querySelector('h3').innerText.includes('Blood Pressure'));
            if (bpCard) {
                if (bpSys && bpDia) {
                    bpCard.querySelector('.value').innerHTML = `${bpSys.value}/${bpDia.value} <span class="unit">mmHg</span>`;
                    const isAbnormal = bpSys.is_abnormal || bpDia.is_abnormal;
                    const status = bpCard.querySelector('.status');
                    status.innerText = isAbnormal ? 'Abnormal' : 'Normal';
                    status.className = `status ${isAbnormal ? 'warning' : 'normal'}`;
                    status.style.background = isAbnormal ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)';
                } else if (bpSys) {
                    bpCard.querySelector('.value').innerHTML = `${bpSys.value}/-- <span class="unit">mmHg</span>`;
                } else if (bpDia) {
                    bpCard.querySelector('.value').innerHTML = `--/${bpDia.value} <span class="unit">mmHg</span>`;
                }
            }

            updateStat('SpO2', latest['spo2']);
            updateStat('Glucose', latest['glucose']);
            updateStat('Temperature', latest['temperature']);
        }

        // Update Alerts
        const alertsList = document.getElementById('alerts-list');
        alertsList.innerHTML = '';
        if (data.alerts && data.alerts.length > 0) {
            data.alerts.forEach(alert => {
                const li = document.createElement('li');
                li.className = 'alert-item warning';

                // Format time - Backend sends UTC, need to handle timezone
                let alertTime;
                try {
                    const timestamp = alert.created_at;
                    // Add 'Z' if not present to indicate UTC
                    if (!timestamp.endsWith('Z') && !timestamp.includes('+')) {
                        alertTime = new Date(timestamp + 'Z');
                    } else {
                        alertTime = new Date(timestamp);
                    }
                } catch (e) {
                    alertTime = new Date(alert.created_at);
                }

                const now = new Date();
                const diffMs = now - alertTime;
                const diffMins = Math.floor(diffMs / 60000);
                const diffHours = Math.floor(diffMs / 3600000);
                const diffDays = Math.floor(diffMs / 86400000);

                let timeDisplay;
                if (diffMs < 0 || diffMins < 1) {
                    timeDisplay = 'Just now';
                } else if (diffMins < 60) {
                    timeDisplay = `${diffMins} min${diffMins > 1 ? 's' : ''} ago`;
                } else if (diffHours < 24) {
                    timeDisplay = `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
                } else if (diffDays < 7) {
                    timeDisplay = `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
                } else {
                    timeDisplay = alertTime.toLocaleDateString() + ' ' + alertTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                }

                li.innerHTML = `
                    <span class="icon">!</span>
                    <div class="msg">${alert.message}</div>
                    <div class="time">${timeDisplay}</div>
                `;
                alertsList.appendChild(li);
            });
        } else {
            alertsList.innerHTML = '<li style="color:var(--text-secondary)">No recent alerts.</li>';
        }

        // Create/Update Weekly Trends Chart
        createTrendsChart(data.vitals);

    } catch (error) {
        console.error("Failed to load dashboard", error);
    }
}

// Chart instance (global to allow updates)
let trendsChart = null;

function createTrendsChart(vitals) {
    if (!vitals || vitals.length === 0) {
        console.log('No vitals data for chart');
        return;
    }

    // Group vitals by date and type
    const last7Days = [];
    const today = new Date();
    for (let i = 6; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);
        last7Days.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
    }

    // Organize data by type and date
    const dataByType = {
        heart_rate: new Array(7).fill(null),
        spo2: new Array(7).fill(null),
        glucose: new Array(7).fill(null)
    };

    vitals.forEach(v => {
        const vitalDate = new Date(v.timestamp + 'Z'); // Add Z for UTC
        const daysDiff = Math.floor((today - vitalDate) / (1000 * 60 * 60 * 24));

        if (daysDiff >= 0 && daysDiff < 7) {
            const index = 6 - daysDiff;
            if (dataByType[v.type]) {
                // Take average if multiple readings per day
                if (dataByType[v.type][index] === null) {
                    dataByType[v.type][index] = v.value;
                } else {
                    dataByType[v.type][index] = (dataByType[v.type][index] + v.value) / 2;
                }
            }
        }
    });

    const ctx = document.getElementById('trendsChart');
    if (!ctx) return;

    // Destroy existing chart if it exists
    if (trendsChart) {
        trendsChart.destroy();
    }

    trendsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: last7Days,
            datasets: [
                {
                    label: 'Heart Rate',
                    data: dataByType.heart_rate,
                    backgroundColor: 'rgba(239, 68, 68, 0.7)',
                    borderColor: '#ef4444',
                    borderWidth: 1,
                    borderRadius: 4
                },
                {
                    label: 'SpO2',
                    data: dataByType.spo2,
                    backgroundColor: 'rgba(59, 130, 246, 0.7)',
                    borderColor: '#3b82f6',
                    borderWidth: 1,
                    borderRadius: 4
                },
                {
                    label: 'Glucose',
                    data: dataByType.glucose,
                    backgroundColor: 'rgba(16, 185, 129, 0.7)',
                    borderColor: '#10b981',
                    borderWidth: 1,
                    borderRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: '#94a3b8',
                        font: {
                            family: 'Outfit',
                            size: 11
                        },
                        usePointStyle: true,
                        padding: 10,
                        boxWidth: 12,
                        boxHeight: 12
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.95)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#cbd5e1',
                    borderColor: '#334155',
                    borderWidth: 1,
                    padding: 10,
                    displayColors: true,
                    callbacks: {
                        label: function (context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += context.parsed.y.toFixed(1);
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(148, 163, 184, 0.08)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#94a3b8',
                        font: {
                            family: 'Outfit',
                            size: 10
                        },
                        padding: 5
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#94a3b8',
                        font: {
                            family: 'Outfit',
                            size: 10
                        },
                        padding: 5
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            },
            barPercentage: 0.7,
            categoryPercentage: 0.8
        }
    });
}

function updateStat(label, vital) {
    // Helper to find the card and update it
    const cards = document.querySelectorAll('.stat-card');
    cards.forEach(card => {
        if (card.querySelector('h3').innerText.includes(label) && !label.includes('Blood Pressure')) {
            if (vital) {
                card.querySelector('.value').innerHTML = `${vital.value} <span class="unit">${vital.unit}</span>`;
                const status = card.querySelector('.status');
                status.innerText = vital.is_abnormal ? 'Abnormal' : 'Normal';
                status.className = `status ${vital.is_abnormal ? 'warning' : 'normal'} `;
                if (vital.is_abnormal) status.style.background = 'rgba(239, 68, 68, 0.2)';
                else status.style.background = 'rgba(16, 185, 129, 0.2)';
            }
        }
    });
}

// --- Simulation & Manual Input ---
async function sendVital(type, value, unit) {
    try {
        console.log(`Sending ${type} for user ${USERNAME}...`);
        const response = await fetch(`${API_BASE_URL}/api/v1/ingest`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: USERNAME,
                type: type,
                value: parseFloat(value),
                unit: unit
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `Server error: ${response.status} `);
        }
        console.log(`Successfully sent ${type} `);
    } catch (e) {
        console.error("Error sending vital:", e);
        alert(`Failed to save ${type}: ${e.message} `);
    }
}

async function simulateData() {
    const vitals = [
        { type: 'heart_rate', value: Math.floor(Math.random() * (110 - 60) + 60), unit: 'bpm' },
        { type: 'spo2', value: Math.floor(Math.random() * (100 - 90) + 90), unit: '%' },
        { type: 'glucose', value: Math.floor(Math.random() * (160 - 80) + 80), unit: 'mg/dL' },
        { type: 'temperature', value: (Math.random() * (101 - 97) + 97).toFixed(1), unit: '°F' }
    ];

    for (const v of vitals) {
        await sendVital(v.type, v.value, v.unit);
    }
    alert("Random simulated data sent!");
    loadDashboard();
}

// Improvement 4: Clear All Inputs Function
function clearAllInputs() {
    document.getElementById('manual-hr').value = '';
    document.getElementById('manual-bp-sys').value = '';
    document.getElementById('manual-bp-dia').value = '';
    document.getElementById('manual-spo2').value = '';
    document.getElementById('manual-glucose').value = '';
    document.getElementById('manual-temp').value = '';
}

async function submitManualData() {
    const hr = document.getElementById('manual-hr').value;
    const bpSys = document.getElementById('manual-bp-sys').value;
    const bpDia = document.getElementById('manual-bp-dia').value;
    const spo2 = document.getElementById('manual-spo2').value;
    const glucose = document.getElementById('manual-glucose').value;
    const temp = document.getElementById('manual-temp').value;

    console.log('📋 Form values captured:', { hr, bpSys, bpDia, spo2, glucose, temp });

    if (!hr && !bpSys && !bpDia && !spo2 && !glucose && !temp) {
        alert("Please enter at least one value.");
        return;
    }

    console.log('✅ Starting data submission...');

    if (hr) await sendVital('heart_rate', hr, 'bpm');
    if (bpSys) await sendVital('blood_pressure_sys', bpSys, 'mmHg');
    if (bpDia) await sendVital('blood_pressure_dia', bpDia, 'mmHg');
    if (spo2) await sendVital('spo2', spo2, '%');
    if (glucose) await sendVital('glucose', glucose, 'mg/dL');
    if (temp) await sendVital('temperature', temp, '°F');

    alert("Manual data submitted successfully!");

    // Use the new clear function
    clearAllInputs();

    loadDashboard();
}

// Improvement 3: Dynamic Date Display
function updateDate() {
    const dateElement = document.getElementById('current-date');
    if (dateElement) {
        const now = new Date();
        const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        dateElement.textContent = now.toLocaleDateString('en-US', options);
    }
}

// Initial Load
loadDashboard();
updateDate();

// Update user profile from localStorage
function updateUserProfile() {
    const fullName = localStorage.getItem('fullName') || 'User';
    const role = localStorage.getItem('role') || 'User';

    // Update profile display
    document.getElementById('user-name').textContent = fullName;
    document.getElementById('user-role').textContent = role.charAt(0).toUpperCase() + role.slice(1);

    // Update avatar with initials
    const initials = fullName.split(' ').map(n => n[0]).join('').toUpperCase();
    document.getElementById('user-avatar').textContent = initials;
}

// Logout function
function handleLogout() {
    if (confirm('Are you sure you want to logout?')) {
        localStorage.clear();
        window.location.href = 'auth.html';
    }
}

// Update profile on load
updateUserProfile();
