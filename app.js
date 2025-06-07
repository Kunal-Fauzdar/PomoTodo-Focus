
document.addEventListener("DOMContentLoaded", function () {
    let video = document.getElementById("logoVideo");
    let animationContainer = document.getElementById("logo-animation");
    let mainContent = document.getElementById("main-content");

    video.onended = function () {
        animationContainer.style.display = "none";  // Hide animation
        mainContent.classList.remove("d-none");  // Show main content
    };
});



// Timer variables
let timeLeft = 25 * 60;
let timerId = null;
let isRunning = false;
let currentTimerType = 'pomodoro';
let focusTime = 0;
let pauseTime = 0;
let focusSessions = 0;
let taskStats = {
    completed: 0,
    totalTime: 0
};

// Analytics data
let analyticsData = {
    focusHours: [],
    taskDistribution: {
        'urgent-important': 0,
        'not-urgent-important': 0,
        'urgent-not-important': 0,
        'not-urgent-not-important': 0
    },
    weeklyProgress: Array(7).fill(0)
};

// Timer settings
const timerSettings = {
    pomodoro: 25 * 60,
    shortBreak: 5 * 60,
    longBreak: 15 * 60
};

const timerColors = {
    pomodoro: '#ba4949',
    shortBreak: '#38858a',
    longBreak: '#397097'
};

const timerLabels = {
    pomodoro: 'Focus Time',
    shortBreak: 'Short Break',
    longBreak: 'Long Break'
};

// Show/hide pages


function showTimer() {
    document.getElementById('timer-section').classList.remove('d-none');
    document.getElementById('tasks-section').classList.add('d-none');
    document.getElementById('analytics-section').classList.add('d-none');
    updateActiveNav('timer');
}

function showTasks() {
    document.getElementById('timer-section').classList.add('d-none');
    document.getElementById('tasks-section').classList.remove('d-none');
    document.getElementById('analytics-section').classList.add('d-none');
    updateActiveNav('tasks');
    updateEisenhowerMatrix();
}

function showAnalytics() {
    document.getElementById('timer-section').classList.add('d-none');
    document.getElementById('tasks-section').classList.add('d-none');
    document.getElementById('analytics-section').classList.remove('d-none');
    updateActiveNav('analytics');
    updateAnalytics();
}

function updateActiveNav(section) {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    document.querySelector(`[onclick="show${section.charAt(0).toUpperCase() + section.slice(1)}()"]`).classList.add('active');
}

// Timer functions
function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${String(minutes).padStart(2, '0')}:${String(remainingSeconds).padStart(2, '0')}`;
}

function updateTimerDisplay() {
    document.getElementById('timer-display').textContent = formatTime(timeLeft);
    document.title = `${formatTime(timeLeft)} - TaskFlow`;
}

function setTimer(type) {
    timeLeft = timerSettings[type];
    currentTimerType = type;
    updateTimerDisplay();
    
    document.getElementById('timer-type').textContent = timerLabels[type];
    document.body.style.backgroundColor = timerColors[type];
    
    document.querySelectorAll('.btn-mode').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    if (timerId) {
        clearInterval(timerId);
        isRunning = false;
        document.getElementById('start-timer').textContent = 'Start';
    }
}

function toggleTimer() {
    const startButton = document.getElementById('start-timer');
    if (!isRunning) {
        isRunning = true;
        startButton.textContent = 'Pause';
        const startTime = Date.now();
        
        timerId = setInterval(() => {
            timeLeft--;
            updateTimerDisplay();
            
            if (currentTimerType === 'pomodoro') {
                focusTime++;
            } else {
                pauseTime++;
            }
            
            if (timeLeft === 0) {
                clearInterval(timerId);
                isRunning = false;
                startButton.textContent = 'Start';
                if (currentTimerType === 'pomodoro') {
                    focusSessions++;
                    updateAnalyticsData();
                }
                playNotification();
                showNotification();
            }
        }, 1000);
    } else {
        clearInterval(timerId);
        isRunning = false;
        startButton.textContent = 'Start';
    }
}

function resetTimer() {
    if (timerId) {
        clearInterval(timerId);
    }
    timeLeft = timerSettings[currentTimerType];
    isRunning = false;
    document.getElementById('start-timer').textContent = 'Start';
    updateTimerDisplay();
}

// Task functions
function addTask() {
    const input = document.getElementById('task-input');
    const priority = document.getElementById('task-priority');
    const taskText = input.value.trim();
    
    if (taskText) {
        const task = {
            text: taskText,
            priority: priority.value,
            completed: false,
            timestamp: Date.now()
        };
        
        const taskList = document.getElementById('task-list');
        const taskItem = createTaskElement(task);
        taskList.appendChild(taskItem);
        
        input.value = '';
        analyticsData.taskDistribution[priority.value]++;
        updateEisenhowerMatrix();
        saveTasks();
        updateAnalytics();
    }
}

function createTaskElement(task) {
    const taskItem = document.createElement('li');
    taskItem.className = `list-group-item task-item ${task.priority}`;
    if (task.completed) {
        taskItem.classList.add('completed');
    }
    
    taskItem.innerHTML = `
        <input type="checkbox" class="form-check-input" onclick="toggleTask(this)" ${task.completed ? 'checked' : ''}>
        <span>${task.text}</span>
        <div class="task-priority-badge">${getPriorityLabel(task.priority)}</div>
        <div class="task-actions">
            <button class="btn btn-delete" onclick="deleteTask(this)">
                <i class="bi bi-trash"></i>
            </button>
        </div>
    `;
    
    return taskItem;
}

function getPriorityLabel(priority) {
    const labels = {
        'urgent-important': 'Do First',
        'not-urgent-important': 'Schedule',
        'urgent-not-important': 'Delegate',
        'not-urgent-not-important': 'Don\'t Do'
    };
    return labels[priority];
}

function toggleTask(checkbox) {
    const taskItem = checkbox.closest('.task-item');
    taskItem.classList.toggle('completed');
    
    if (taskItem.classList.contains('completed')) {
        taskStats.completed++;
        const priorityClass = Array.from(taskItem.classList).find(cls => cls.includes('urgent') || cls.includes('not-urgent'));
        analyticsData.taskDistribution[priorityClass]--;
    }
    
    updateEisenhowerMatrix();
    saveTasks();
    updateAnalytics();
}

function deleteTask(button) {
    const taskItem = button.closest('.task-item');
    const priorityClass = Array.from(taskItem.classList).find(cls => cls.includes('urgent') || cls.includes('not-urgent'));
    
    if (!taskItem.classList.contains('completed')) {
        analyticsData.taskDistribution[priorityClass]--;
    }
    
    taskItem.remove();
    updateEisenhowerMatrix();
    saveTasks();
    updateAnalytics();
}

function updateEisenhowerMatrix() {
    const matrix = {
        'urgent-important': document.getElementById('urgent-important-list'),
        'not-urgent-important': document.getElementById('not-urgent-important-list'),
        'urgent-not-important': document.getElementById('urgent-not-important-list'),
        'not-urgent-not-important': document.getElementById('not-urgent-not-important-list')
    };
    
    // Clear all quadrants
    Object.values(matrix).forEach(list => list.innerHTML = '');
    
    // Populate matrix
    document.querySelectorAll('.task-item:not(.completed)').forEach(task => {
        const priority = Array.from(task.classList).find(cls => cls.includes('urgent') || cls.includes('not-urgent'));
        if (priority && matrix[priority]) {
            const matrixItem = document.createElement('li');
            matrixItem.textContent = task.querySelector('span').textContent;
            matrix[priority].appendChild(matrixItem);
        }
    });
}

// Analytics functions
function updateAnalyticsData() {
    const today = new Date();
    const dayOfWeek = today.getDay();
    
    analyticsData.focusHours.push(focusTime / 3600);
    analyticsData.weeklyProgress[dayOfWeek] = focusTime / 3600;
    
    localStorage.setItem('analyticsData', JSON.stringify(analyticsData));
}

function updateAnalytics() {
    // Update stats cards
    document.getElementById('total-focus-time').textContent = formatHours(focusTime);
    document.getElementById('focus-sessions').textContent = focusSessions;
    document.getElementById('tasks-completed').textContent = taskStats.completed;
    
    // Update charts
    updateFocusChart();
    updateTaskDistributionChart();
    updateWeeklyProgressChart();
}

function formatHours(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
}

function updateFocusChart() {
    const ctx = document.getElementById('focusChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array(analyticsData.focusHours.length).fill('').map((_, i) => `Session ${i + 1}`),
            datasets: [{
                label: 'Focus Hours',
                data: analyticsData.focusHours,
                borderColor: '#6366f1',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                }
            }
        }
    });
}

function updateTaskDistributionChart() {
    const ctx = document.getElementById('taskDistributionChart').getContext('2d');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Do First', 'Schedule', 'Delegate', 'Don\'t Do'],
            datasets: [{
                data: Object.values(analyticsData.taskDistribution),
                backgroundColor: ['#ef4444', '#6366f1', '#f59e0b', '#10b981']
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right',
                }
            }
        }
    });
}

function updateWeeklyProgressChart() {
    const ctx = document.getElementById('weeklyProgressChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
            datasets: [{
                label: 'Focus Hours',
                data: analyticsData.weeklyProgress,
                backgroundColor: '#6366f1'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                }
            }
        }
    });
}

// Storage functions
function saveTasks() {
    const taskList = document.getElementById('task-list');
    const tasks = [];
    taskList.querySelectorAll('.task-item').forEach(taskItem => {
        const priorityClass = Array.from(taskItem.classList).find(cls => cls.includes('urgent') || cls.includes('not-urgent'));
        tasks.push({
            text: taskItem.querySelector('span').textContent,
            completed: taskItem.classList.contains('completed'),
            priority: priorityClass,
            timestamp: Date.now()
        });
    });
    localStorage.setItem('tasks', JSON.stringify(tasks));
}

function loadTasks() {
    const tasks = JSON.parse(localStorage.getItem('tasks') || '[]');
    const taskList = document.getElementById('task-list');
    
    tasks.forEach(task => {
        const taskItem = createTaskElement(task);
        taskList.appendChild(taskItem);
        
        if (!task.completed) {
            analyticsData.taskDistribution[task.priority]++;
        }
    });
    
    updateEisenhowerMatrix();
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Initialize AOS
    AOS.init({
        duration: 1000,
        once: true,
        offset: 100,
        delay: 100,
        easing: 'ease-out'
    });
    
    // Load saved data
    const savedAnalytics = localStorage.getItem('analyticsData');
    if (savedAnalytics) {
        analyticsData = JSON.parse(savedAnalytics);
    }
    
    // Initialize UI
    updateTimerDisplay();
    loadTasks();
    updateAnalytics();
    
    // Add enter key support
    document.getElementById('task-input')?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            addTask();
        }
    });
    
    // Navbar scroll effect
    const navbar = document.querySelector('.navbar-glass');
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.style.background = 'rgba(15, 23, 42, 0.8)';
        } else {
            navbar.style.background = 'rgba(15, 23, 42, 0.1)';
        }
    });
});