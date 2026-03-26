import { apiFetch } from "./api.js";

const shortMonths = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
function getISTDateString(date = new Date()) {
    const ist = new Date(date.getTime() + 5.5 * 60 * 60 * 1000);
    return ist.toISOString().split('T')[0];
}

const token = localStorage.getItem("token");
if (!token) {
    location.href = "index.html";
} else {
    loadMonthly();
}

async function loadMonthly() {
    const today = new Date();
    const todayStr = getISTDateString(today);
    const year = today.getFullYear();
    const month = today.getMonth();
    const monthNames = ["January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"];
    document.getElementById('monthName').innerText = monthNames[month];
    document.getElementById('yearName').innerText = year;
    const monthData = await apiFetch(`/stats/monthly?year=${year}&month=${month + 1}`);
    const todayData = await apiFetch(`/stats/today?date=${todayStr}`);
    const streakEl = document.getElementById('streakNumber');
    if (streakEl) streakEl.innerText = monthData.streak || 0;
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const monthStats = monthData.days || [];
    const liveToday = {
        date: todayStr,
        tasks_done: todayData.tasks_done || 0,
        tasks_total: todayData.tasks_total || 0,
        tasks_pending: todayData.tasks_pending || 0,
        habits_done: todayData.habits_done || 0,
        habits_total: todayData.habits_total || 0,
        habits_pending: todayData.habits_pending || 0,
        mood: todayData.mood || 0,
        energy: todayData.energy || 0,
    };
    function getStatForDate(dateStr) {
        if (dateStr === todayStr) return liveToday;
        const s = monthStats ? monthStats.find(s => String(s.date).split('T')[0] === dateStr) : null;
        return s || null;
    }
    const weeks = [];
    let current = new Date(firstDay);
    const dow = current.getDay();
    current.setDate(current.getDate() + ((dow === 0) ? -6 : 1 - dow));
    while (current <= lastDay) {
        const weekStart = new Date(current);
        const weekEnd = new Date(current);
        weekEnd.setDate(weekEnd.getDate() + 6);
        const weekDays = [];
        for (let i = 0; i < 7; i++) {
            const d = new Date(current);
            d.setDate(current.getDate() + i);
            weekDays.push(d);
        }
        weeks.push({ weekStart, weekEnd, weekDays });
        current.setDate(current.getDate() + 7);
    }
    let totalDone = 0, totalExpected = 0;
    let allMoods = [], allEnergy = [];
    for (let d = new Date(firstDay); d <= today && d <= lastDay; d.setDate(d.getDate() + 1)) {
        const dStr = getISTDateString(new Date(d));
        const stat = getStatForDate(dStr);
        if (stat) {
            totalDone += (stat.tasks_done || 0) + (stat.habits_done || 0);
            totalExpected += (stat.tasks_total || 0) + (stat.habits_total || 0);
            allMoods.push(stat.mood || 0);
            allEnergy.push(stat.energy || 0);
        }
    }
    const weeklyTaskCounts = [];
    const weeklyLabels = [];
    weeks.forEach((week, idx) => {
        let weekTotal = 0;
        week.weekDays.forEach(d => {
            const dStr = getISTDateString(new Date(d));
            const stat = getStatForDate(dStr);
            if (stat) weekTotal += stat.tasks_done || 0;
        });
        weeklyTaskCounts.push(weekTotal);
        weeklyLabels.push('W' + (idx + 1) + ' · ' + week.weekStart.getDate() + ' ' + shortMonths[week.weekStart.getMonth()]);
    });
    const percent = totalExpected > 0 ? Math.round((totalDone / totalExpected) * 100) : 0;
    const circle = document.getElementById('progressCircle');
    circle.innerText = percent + '%';
    circle.style.background = `conic-gradient(#9370cc ${percent}%, #eee ${percent}%)`;
    const avgMood = allMoods.length ? allMoods.reduce((a, b) => a + b, 0) / allMoods.length : 0;
    const avgEnergy = allEnergy.length ? allEnergy.reduce((a, b) => a + b, 0) / allEnergy.length : 0;
    new Chart(document.getElementById('avgMoodChart'), {
        type: 'bar',
        data: {
            labels: ['Mood', 'Energy'],
            datasets: [{ data: [avgMood.toFixed(1), avgEnergy.toFixed(1)], backgroundColor: ['#c3ecd8', '#f9c6d0'], borderRadius: 10 }]
        },
        options: {
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { display: false }, border: { display: false } },
                y: { grid: { display: false }, border: { display: false }, ticks: { display: false }, max: 100 }
            }
        }
    });
    new Chart(document.getElementById('monthlyTaskChart'), {
        type: 'line',
        data: {
            labels: weeklyLabels,
            datasets: [{
                data: weeklyTaskCounts,
                borderColor: '#9370cc',
                backgroundColor: 'rgba(147,112,204,0.15)',
                borderWidth: 3,
                tension: 0.4,
                fill: true,
                pointBackgroundColor: weeklyLabels.map((_, i) => {
                    const isCurrent = weeks[i]?.weekDays.some(d => getISTDateString(new Date(d)) === todayStr);
                    return isCurrent ? '#f08aa1' : '#9370cc';
                }),
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 6,
                pointHoverRadius: 8
            }]
        },
        options: {
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { display: false }, border: { display: false }, ticks: { font: { size: 11 } } },
                y: { grid: { display: false }, border: { display: false }, ticks: { display: false }, beginAtZero: true }
            }
        }
    });
    renderWeeks(weeks, getStatForDate, todayStr);
}
function renderWeeks(weeks, getStatForDate, todayStr) {
    const container = document.getElementById('weeksContainer');
    container.innerHTML = '';
    weeks.forEach((week, idx) => {
        let wTasksDone = 0, wTasksTotal = 0;
        let wHabitsDone = 0, wHabitsTotal = 0;
        let wMoodSum = 0, wEnergySum = 0, wDaysWithData = 0;
        week.weekDays.forEach(d => {
            const dStr = getISTDateString(new Date(d));
            const stat = getStatForDate(dStr);
            if (stat && (stat.tasks_total > 0 || stat.habits_done > 0 || stat.mood > 0)) {
                wTasksDone += stat.tasks_done || 0;
                wTasksTotal += stat.tasks_total || 0;
                wHabitsDone += stat.habits_done || 0;
                wHabitsTotal += stat.habits_total || 0;
                wMoodSum += stat.mood || 0;
                wEnergySum += stat.energy || 0;
                wDaysWithData++;
            }
        });
        const wTasksPending = wTasksTotal - wTasksDone;
        const wHabitsPending = wHabitsTotal - wHabitsDone;
        const avgMood = wDaysWithData > 0 ? (wMoodSum / wDaysWithData).toFixed(0) : 0;
        const avgEnergy = wDaysWithData > 0 ? (wEnergySum / wDaysWithData).toFixed(0) : 0;
        const isCurrentWeek = week.weekDays.some(d => getISTDateString(new Date(d)) === todayStr);
        const startLabel = week.weekStart.getDate() + ' ' + shortMonths[week.weekStart.getMonth()];
        const endLabel = week.weekEnd.getDate() + ' ' + shortMonths[week.weekEnd.getMonth()];
        const card = document.createElement('div');
        card.className = 'card week-card';
        card.innerHTML = `
      <div class="week-info">
        <span class="week-badge ${isCurrentWeek ? 'current-week-badge' : ''}">
          Week ${idx + 1}${isCurrentWeek ? ' · Now' : ''}
        </span>
        <div style="font-size:11px; color:#aaa; margin-bottom:10px;">${startLabel} – ${endLabel}</div>
        <div class="stat-row">
          <span class="stat-label">Tasks</span>
          <span class="stat-value">Total: ${wTasksTotal} &nbsp;|&nbsp; Done: ${wTasksDone} &nbsp;|&nbsp; Pending: ${wTasksPending}</span>
          <span class="stat-label">Habits</span>
          <span class="stat-value">Done: ${wHabitsDone} &nbsp;|&nbsp; Pending: ${wHabitsPending}</span>
        </div>
      </div>
      <div><canvas id="weekTaskChart${idx}"></canvas></div>
      <div><canvas id="weekMoodChart${idx}"></canvas></div>
    `;
        container.appendChild(card);
        new Chart(document.getElementById(`weekTaskChart${idx}`), {
            type: 'bar',
            data: {
                labels: ['Done', 'Pending'],
                datasets: [{ data: [wTasksDone, wTasksPending], backgroundColor: ['#c3ecd8', '#f9c6d0'], borderRadius: 8 }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false }, border: { display: false }, ticks: { font: { size: 11 } } },
                    y: { grid: { display: false }, border: { display: false }, ticks: { display: false }, beginAtZero: true }
                }
            }
        });
        new Chart(document.getElementById(`weekMoodChart${idx}`), {
            type: 'bar',
            data: {
                labels: ['Mood', 'Energy'],
                datasets: [{ data: [avgMood, avgEnergy], backgroundColor: ['#f9c6d0', '#9370cc'], borderRadius: 8 }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false }, border: { display: false }, ticks: { font: { size: 11 } } },
                    y: { grid: { display: false }, border: { display: false }, ticks: { display: false }, max: 100, beginAtZero: true }
                }
            }
        });
    });
}
