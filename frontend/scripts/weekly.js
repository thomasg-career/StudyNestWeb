import { apiFetch } from "./api.js";

function goBack() {
    window.location.href = "dashboard.html";
}

const token = localStorage.getItem("token");
if (!token) {
    location.href = "index.html";
} else {
    loadWeekly();
}

async function loadWeekly() {
    const today = new Date();
    const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    const month = monthNames[today.getMonth()];
    const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
    const dayOfWeek = firstDay.getDay();
    const weekNumber = Math.ceil((today.getDate() + dayOfWeek) / 7);
    const weekInfoEl = document.getElementById("weekInfo");
    if (weekInfoEl) {
        weekInfoEl.innerHTML = `<span style="font-size: 13px; font-weight: 500; color: #888;">${month}</span><br>Week ${weekNumber}`;
    }
    const dayOfWeekToday = today.getDay(); 
    const diffToMonday = (dayOfWeekToday === 0) ? -6 : 1 - dayOfWeekToday;
    const monday = new Date(today);
    monday.setDate(today.getDate() + diffToMonday);
    const days = [];
    for (let i = 0; i < 7; i++) {
        let d = new Date(monday);
        d.setDate(monday.getDate() + i);
        days.push(d);
    }
    let todayY = today.getFullYear();
    let todayM = String(today.getMonth() + 1).padStart(2, '0');
    let todayD = String(today.getDate()).padStart(2, '0');
    let todayStr = `${todayY}-${todayM}-${todayD}`;
    const weeklyData = await apiFetch("/stats/weekly");
    const todayData = await apiFetch(`/stats/today?date=${todayStr}`);
    const allStats = weeklyData.days || [];
    let currentStreakCount = weeklyData.streak || 0;
    let taskCounts = [];
    let taskTotals = [];
    let habitCounts = [];
    let habitTotals = [];
    let moods = [];
    let energy = [];
    for (let d of days) {
        let y = d.getFullYear();
        let m = String(d.getMonth() + 1).padStart(2, '0');
        let dNum = String(d.getDate()).padStart(2, '0');
        let dateStr = `${y}-${m}-${dNum}`;
        let stat = allStats
            ? allStats.find(s => {
                const dbDate = String(s.date).split("T")[0];
                return dbDate === dateStr;
            })
            : null;
        if (dateStr === todayStr) {
            taskCounts.push(todayData.tasks_done || 0);
            taskTotals.push(todayData.tasks_total || 0);
            habitCounts.push(todayData.habits_done || 0);
            habitTotals.push(todayData.habits_total || 0);
            moods.push(todayData.mood || 0);
            energy.push(todayData.energy || 0);
        } else if (stat) {
            taskCounts.push(stat.tasks_done || 0);
            taskTotals.push(stat.tasks_total || 0);
            habitCounts.push(stat.habits_done || 0);
            habitTotals.push(stat.habits_total || 0);
            moods.push(stat.mood || 0);
            energy.push(stat.energy || 0);
        } else {
            taskCounts.push(0);
            taskTotals.push(0);
            habitCounts.push(0);
            habitTotals.push(0);
            moods.push(0);
            energy.push(0);
        }
    }
    const todayIndex = (today.getDay() === 0) ? 6 : today.getDay() - 1; 
    renderStreak(taskCounts, currentStreakCount, todayIndex);
    renderCharts(days, taskCounts, taskTotals, habitCounts, habitTotals, moods, energy);
    renderDays(days, taskCounts, taskTotals, habitCounts, habitTotals, moods, energy);
}
function renderStreak(tasks, globalStreak, todayIndex) {
    const container = document.getElementById("streakRow");
    if (!container) return;
    container.innerHTML = "";
    const streakNumEl = document.getElementById("streakNumber");
    if (streakNumEl) streakNumEl.innerText = globalStreak;
    const dayLabels = ["M", "T", "W", "T", "F", "S", "S"];
    const bgLine = document.createElement("div");
    bgLine.className = "streak-line-bg";
    container.appendChild(bgLine);
    const fillLine = document.createElement("div");
    fillLine.className = "streak-line-fill";
    let streakStartIndex = -1;
    let lastActiveInStreak = -1;
    let missedToday = tasks[todayIndex] === 0;
    for (let i = 0; i <= todayIndex; i++) {
        let distance = missedToday ? (todayIndex - 1 - i) : (todayIndex - i);
        if (distance >= 0 && distance < globalStreak) {
            if (streakStartIndex === -1) streakStartIndex = i;
            lastActiveInStreak = i;
        }
    }
    if (globalStreak > 1 && streakStartIndex !== -1) {
        let actualStreakLength = lastActiveInStreak - streakStartIndex;
        if (actualStreakLength > 0) {
            let startPercent = (streakStartIndex / 6);
            let widthPercent = (actualStreakLength / 6);
            fillLine.style.left = `calc(22px + (100% - 44px) * ${startPercent})`;
            fillLine.style.width = `calc((100% - 44px) * ${widthPercent})`;
        } else {
            fillLine.style.width = "0";
        }
    } else {
        fillLine.style.width = "0";
    }
    container.appendChild(fillLine);
    const daysContainer = document.createElement("div");
    daysContainer.className = "streak-days-container";
    tasks.forEach((t, i) => {
        const wrap = document.createElement("div");
        wrap.className = "streak-day-wrap";
        const label = document.createElement("div");
        label.className = "streak-day-label";
        label.innerText = dayLabels[i];
        const circle = document.createElement("div");
        circle.className = "streak-circle";
        let distance = missedToday ? (todayIndex - 1 - i) : (todayIndex - i);
        if (distance >= 0 && distance < globalStreak) {
            circle.classList.add("active");
        }
        wrap.appendChild(label);
        wrap.appendChild(circle);
        daysContainer.appendChild(wrap);
    });
    container.appendChild(daysContainer);
}
let myTaskChart;
let myAvgChart;
function renderCharts(days, tasks, taskTotals, habits, habitTotals, mood, energy) {
    const labels = days.map(d =>
        ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][d.getDay()]
    );
    if (myTaskChart) {
        myTaskChart.destroy();
    }
    myTaskChart = new Chart(document.getElementById("taskChart"), {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: "Tasks Completed",
                data: tasks,
                borderColor: '#9370cc',
                backgroundColor: 'rgba(147, 112, 204, 0.2)',
                borderWidth: 3,
                tension: 0.4,
                fill: true,
                pointBackgroundColor: '#fff',
                pointBorderColor: '#9370cc',
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { stepSize: 1, precision: 0 }
                },
                x: {
                    grid: { display: false }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
    let totalDone = tasks.reduce((a, b) => a + b, 0) + habits.reduce((a, b) => a + b, 0);
    let totalExpected = taskTotals.reduce((a, b) => a + b, 0) + habitTotals.reduce((a, b) => a + b, 0);
    let percent = totalExpected > 0 ? Math.round((totalDone / totalExpected) * 100) : 0;
    let circle = document.getElementById("progressCircle");
    if (circle) {
        circle.innerText = percent + "%";
        circle.style.background = `conic-gradient(#9370cc ${percent}%, #eee ${percent}%)`;
    }
    let avgMood = mood.reduce((a, b) => a + b, 0) / 7;
    let avgEnergy = energy.reduce((a, b) => a + b, 0) / 7;
    let avgTasks = tasks.reduce((a, b) => a + b, 0) / 7;
    let avgHabits = habits.reduce((a, b) => a + b, 0) / 7;
    const avgContainer = document.getElementById("avgChart").parentElement;
    let avgText = document.getElementById("avgTextDetails");
    if (!avgText) {
        avgText = document.createElement("div");
        avgText.id = "avgTextDetails";
        avgText.style = "text-align: center; margin-top: 15px; font-size: 13px; color: #555; background: rgba(255,255,255,0.6); padding: 8px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);";
        avgContainer.appendChild(avgText);
    }
    avgText.innerHTML = `<b>Tasks:</b> ${avgTasks.toFixed(1)}/day &nbsp; | &nbsp; <b>Habits:</b> ${avgHabits.toFixed(1)}/day`;
    if (myAvgChart) {
        myAvgChart.destroy();
    }
    myAvgChart = new Chart(document.getElementById("avgChart"), {
        type: 'bar',
        data: {
            labels: ["Mood", "Energy"],
            datasets: [{
                data: [avgMood, avgEnergy],
                backgroundColor: ['#c3ecd8', '#f9c6d0'],
                borderRadius: 8
            }]
        },
        options: {
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { display: false }, border: { display: false } },
                y: { grid: { display: false }, border: { display: false }, ticks: { display: false }, max: 100 }
            }
        }
    });
}

window.goBack = goBack;
function renderDays(days, tasks, taskTotals, habits, habitTotals, mood, energy) {
    const container = document.getElementById("daysContainer");
    container.innerHTML = "";
    days.forEach((d, i) => {
        const done = tasks[i] || 0;
        const total = taskTotals[i] || 0;
        const pending = Math.max(0, total - done);
        const hDone = habits[i] || 0;
        const hTotal = habitTotals[i] || 0;
        const hPending = Math.max(0, hTotal - hDone);
        const div = document.createElement("div");
        div.className = "card day-card";
        div.innerHTML = `
        <div>
            <h3 style="margin-bottom: 8px;">${d.toDateString()}</h3>
            <p style="margin: 4px 0; color: #555; font-weight: bold;">Tasks</p>
            <p style="margin: 2px 0 8px 10px; color: #555; font-size: 13px;">Done: ${done} | Pending: ${pending}</p>
            <p style="margin: 4px 0; color: #555; font-weight: bold;">Habits</p>
            <p style="margin: 2px 0 0 10px; color: #555; font-size: 13px;">Done: ${hDone} | Pending: ${hPending}</p>
        </div>
        <div style="position: relative;">
            <canvas id="taskChart${i}"></canvas>
        </div>
        <div style="position: relative;">
            <canvas id="moodChart${i}"></canvas>
        </div>
        `;
        container.appendChild(div);
        new Chart(document.getElementById(`taskChart${i}`), {
            type: 'bar',
            data: {
                labels: ["Done", "Pending"],
                datasets: [{
                    data: [done, pending],
                    backgroundColor: ['#c3ecd8', '#f9c6d0'],
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { grid: { display: false }, border: { display: false }, ticks: { font: { size: 10 } } },
                    y: { grid: { display: false }, border: { display: false }, ticks: { display: false } }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
        new Chart(document.getElementById(`moodChart${i}`), {
            type: 'bar',
            data: {
                labels: ["Mood", "Energy"],
                datasets: [{
                    data: [mood[i], energy[i]],
                    backgroundColor: ['#f9c6d0', '#9370cc'],
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { grid: { display: false }, border: { display: false }, ticks: { font: { size: 10 } } },
                    y: { grid: { display: false }, border: { display: false }, ticks: { display: false }, max: 100 }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    });
}
