import { apiFetch } from "./api.js";

const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'];
const shortMonths = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
function getISTDateString(date = new Date()) {
    const ist = new Date(date.getTime() + 5.5 * 60 * 60 * 1000);
    return ist.toISOString().split('T')[0];
}

const token = localStorage.getItem("token");
if (!token) {
    location.href = "index.html";
} else {
    loadYearly();
}

async function loadYearly() {
    const today = new Date();
    const todayStr = getISTDateString(today);
    const year = today.getFullYear();
    const currentMonth = today.getMonth();
    document.getElementById('yearLabel').innerText = year;
    document.getElementById('yearSub').innerText = 'Jan – ' + shortMonths[currentMonth] + ' ' + year;
    const yearData = await apiFetch(`/stats/yearly?year=${year}`);
    const todayData = await apiFetch(`/stats/today?date=${todayStr}`);
    document.getElementById('streakNumber').innerText = yearData.streak || 0;
    const yearStats = yearData.days || [];
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
        const s = yearStats ? yearStats.find(s => String(s.date).split('T')[0] === dateStr) : null;
        return s || null;
    }
    let totalDone = 0, totalExpected = 0;
    let allMoods = [], allEnergy = [];
    const monthlyTaskCounts = [];
    const monthlyLabels = [];
    for (let m = 0; m <= currentMonth; m++) {
        const firstDay = new Date(year, m, 1);
        const lastDay = new Date(year, m + 1, 0);
        let monthTotal = 0;
        for (let d = new Date(firstDay); d <= lastDay && d <= today; d.setDate(d.getDate() + 1)) {
            const dStr = getISTDateString(new Date(d));
            const stat = getStatForDate(dStr);
            if (stat) {
                totalDone += (stat.tasks_done || 0) + (stat.habits_done || 0);
                totalExpected += (stat.tasks_total || 0) + (stat.habits_total || 0);
                allMoods.push(stat.mood || 0);
                allEnergy.push(stat.energy || 0);
                monthTotal += stat.tasks_done || 0;
            }
        }
        monthlyTaskCounts.push(monthTotal);
        monthlyLabels.push(shortMonths[m]);
    }
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
            datasets: [{
                data: [avgMood.toFixed(1), avgEnergy.toFixed(1)],
                backgroundColor: ['#c3ecd8', '#f9c6d0'],
                borderRadius: 10
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
    new Chart(document.getElementById('yearlyTaskChart'), {
        type: 'line',
        data: {
            labels: monthlyLabels,
            datasets: [{
                data: monthlyTaskCounts,
                borderColor: '#9370cc',
                backgroundColor: 'rgba(147,112,204,0.15)',
                borderWidth: 3,
                tension: 0.4,
                fill: true,
                pointBackgroundColor: monthlyLabels.map((_, i) => i === currentMonth ? '#f08aa1' : '#9370cc'),
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
    renderMonths(year, currentMonth, today, todayStr, getStatForDate);
}
function renderMonths(year, currentMonth, today, todayStr, getStatForDate) {
    const container = document.getElementById('monthsContainer');
    container.innerHTML = '';
    for (let m = 0; m <= currentMonth; m++) {
        const firstDay = new Date(year, m, 1);
        const lastDay = new Date(year, m + 1, 0);
        let mTasksDone = 0, mTasksTotal = 0;
        let mHabitsDone = 0, mHabitsTotal = 0;
        let mMoodSum = 0, mEnergySum = 0, mDaysWithData = 0;
        for (let d = new Date(firstDay); d <= lastDay && d <= today; d.setDate(d.getDate() + 1)) {
            const dStr = getISTDateString(new Date(d));
            const stat = getStatForDate(dStr);
            if (stat && (stat.tasks_total > 0 || stat.habits_done > 0 || stat.mood > 0)) {
                mTasksDone += stat.tasks_done || 0;
                mTasksTotal += stat.tasks_total || 0;
                mHabitsDone += stat.habits_done || 0;
                mHabitsTotal += stat.habits_total || 0;
                mMoodSum += stat.mood || 0;
                mEnergySum += stat.energy || 0;
                mDaysWithData++;
            }
        }
        const mTasksPending = mTasksTotal - mTasksDone;
        const mHabitsPending = mHabitsTotal - mHabitsDone;
        const avgMood = mDaysWithData > 0 ? (mMoodSum / mDaysWithData).toFixed(0) : 0;
        const avgEnergy = mDaysWithData > 0 ? (mEnergySum / mDaysWithData).toFixed(0) : 0;
        const isCurrentMonth = m === currentMonth;
        const startLabel = '1 ' + shortMonths[m];
        const endLabel = lastDay.getDate() + ' ' + shortMonths[m];
        const card = document.createElement('div');
        card.className = 'card month-card';
        card.innerHTML = `
      <div class="month-info">
        <span class="month-badge ${isCurrentMonth ? 'current-month-badge' : ''}">
          ${monthNames[m]}${isCurrentMonth ? ' · Now' : ''}
        </span>
        <div style="font-size:11px; color:#aaa; margin-bottom:10px;">${startLabel} – ${endLabel}</div>
        <div class="stat-row">
          <span class="stat-label">Tasks</span>
          <span class="stat-value">Total: ${mTasksTotal} &nbsp;|&nbsp; Done: ${mTasksDone} &nbsp;|&nbsp; Pending: ${mTasksPending}</span>
          <span class="stat-label">Habits</span>
          <span class="stat-value">Done: ${mHabitsDone} &nbsp;|&nbsp; Pending: ${mHabitsPending}</span>
        </div>
      </div>
      <div><canvas id="monthTaskChart${m}"></canvas></div>
      <div><canvas id="monthMoodChart${m}"></canvas></div>
    `;
        container.appendChild(card);
        new Chart(document.getElementById(`monthTaskChart${m}`), {
            type: 'bar',
            data: {
                labels: ['Done', 'Pending'],
                datasets: [{
                    data: [mTasksDone, mTasksPending],
                    backgroundColor: ['#c3ecd8', '#f9c6d0'],
                    borderRadius: 8
                }]
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
        new Chart(document.getElementById(`monthMoodChart${m}`), {
            type: 'bar',
            data: {
                labels: ['Mood', 'Energy'],
                datasets: [{
                    data: [avgMood, avgEnergy],
                    backgroundColor: ['#f9c6d0', '#9370cc'],
                    borderRadius: 8
                }]
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
    }
}
