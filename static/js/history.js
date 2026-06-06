// 产品经理进化论 - 学习历史页逻辑

// 生成/获取用户唯一ID
function getUserId() {
  let userId = localStorage.getItem('pm_evolution_user_id');
  if (!userId) {
    userId = 'user_' + Date.now() + '_' + Math.random().toString(36).substring(2, 8);
    localStorage.setItem('pm_evolution_user_id', userId);
  }
  return userId;
}

const currentUserId = getUserId();

// 封装 fetch 请求，自动带上 user_id
async function fetchWithUserId(url, options = {}) {
  const separator = url.includes('?') ? '&' : '?';
  const urlWithUserId = `${url}${separator}user_id=${currentUserId}`;
  
  if (options.headers) {
    options.headers['X-User-Id'] = currentUserId;
  } else {
    options.headers = { 'X-User-Id': currentUserId };
  }
  
  return fetch(urlWithUserId, options);
}

document.addEventListener('DOMContentLoaded', () => {
  loadHistory();
});

async function loadHistory() {
  try {
    const resp = await fetchWithUserId('/api/history');
    const data = await resp.json();
    renderStats(data);
    renderCalendar(data.grouped);
    renderHistory(data.grouped);
  } catch (error) {
    showError('加载历史失败');
  }
}

function renderStats(data) {
  const history = data.history || [];

  if (history.length === 0) {
    document.getElementById('h-stat-days').textContent = '0';
    document.getElementById('h-stat-avg').textContent = '-';
    document.getElementById('h-stat-max').textContent = '-';
    document.getElementById('h-stat-duration').textContent = '0分钟';
    return;
  }

  const totalDays = Object.keys(data.grouped || {}).length;
  const avgScore = (history.reduce((sum, h) => sum + h.score, 0) / history.length).toFixed(1);
  const maxScore = Math.max(...history.map(h => h.score));
  const totalDuration = data.total_duration || 0;

  document.getElementById('h-stat-days').textContent = totalDays;
  document.getElementById('h-stat-avg').textContent = avgScore;
  document.getElementById('h-stat-max').textContent = maxScore;
  document.getElementById('h-stat-duration').textContent = formatDuration(totalDuration);
}

function formatDuration(minutes) {
  if (minutes < 60) {
    return `${minutes}分钟`;
  }
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return `${hours}小时${mins > 0 ? mins + '分钟' : ''}`;
}

function calculateStreak(dates) {
  if (!dates || dates.length === 0) {
    return 0;
  }

  const sortedDates = dates.sort().reverse();
  let streak = 0;
  let prevDate = new Date();

  for (let i = 0; i < sortedDates.length; i++) {
    const currDate = new Date(sortedDates[i]);
    const diffDays = Math.floor((prevDate - currDate) / (1000 * 60 * 60 * 24));

    if (i === 0) {
      streak = 1;
    } else if (diffDays === 1) {
      streak++;
    } else {
      break;
    }
    prevDate = currDate;
  }

  return streak;
}

function renderCalendar(grouped) {
  const calendar = document.getElementById('calendar-container');
  const now = new Date();
  const currentYear = now.getFullYear();
  const currentMonth = now.getMonth();

  // 获取学习的日期集合
  const learningDates = Object.keys(grouped || {});

  // 生成日历HTML
  const monthNames = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];

  // 获取当月第一天和最后一天
  const firstDay = new Date(currentYear, currentMonth, 1);
  const lastDay = new Date(currentYear, currentMonth + 1, 0);
  const startWeekday = firstDay.getDay();
  const daysInMonth = lastDay.getDate();

  let html = `
    <div class="calendar-header">
      <div class="calendar-month">${currentYear}年 ${monthNames[currentMonth]}</div>
    </div>
    <div class="calendar-weekdays">
      <div>日</div><div>一</div><div>二</div><div>三</div><div>四</div><div>五</div><div>六</div>
    </div>
    <div class="calendar-grid">
  `;

  // 填充空白
  for (let i = 0; i < startWeekday; i++) {
    html += '<div class="calendar-day empty"></div>';
  }

  // 填充日期
  for (let day = 1; day <= daysInMonth; day++) {
    const dateStr = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    const hasLearning = learningDates.includes(dateStr);
    const isToday = dateStr === now.toISOString().split('T')[0];
    const learningCount = hasLearning ? grouped[dateStr].length : 0;

    html += `
      <div class="calendar-day ${hasLearning ? 'has-learning' : ''} ${isToday ? 'today' : ''}">
        <span class="day-number">${day}</span>
      </div>
    `;
  }

  html += '</div>';
  calendar.innerHTML = html;
}

function renderHistory(grouped) {
  const container = document.getElementById('history-container');

  if (!grouped || Object.keys(grouped).length === 0) {
    container.innerHTML = `
      <div class="card fade-in">
        <div class="card-title">
          <span>📝</span> 学习历史
        </div>
        <div class="card-content" style="text-align: center; padding: 2rem;">
          <span style="font-size: 3rem;">📚</span>
          <p style="margin-top: 1rem; color: #64748b;">还没有学习记录</p>
          <div style="margin-top: 1.5rem;">
            <a href="/" class="btn btn-primary">开始第一次学习</a>
          </div>
        </div>
      </div>
    `;
    return;
  }

  // 按日期排序（最新在前）
  const sortedDates = Object.keys(grouped).sort().reverse();
  container.innerHTML = '';

  sortedDates.forEach(date => {
    const records = grouped[date];

    // 创建日期卡片
    const dateCard = document.createElement('div');
    dateCard.className = 'date-card fade-in';
    dateCard.innerHTML = `
      <div class="date-header">
        <span class="date-title">📅 ${date}</span>
        <span class="date-count">${records.length}个知识点</span>
      </div>
    `;

    // 添加该日期的所有学习记录
    records.forEach(record => {
      const scoreColor = record.score >= 8 ? '#10b981' : record.score >= 6 ? '#f59e0b' : '#ef4444';

      const recordDiv = document.createElement('div');
      recordDiv.className = 'learning-record';
      recordDiv.innerHTML = `
        <div class="record-main">
          <div class="record-info">
            <span class="record-skill">📚 ${record.skill}</span>
            <span class="record-kp">🎯 ${record.knowledge}</span>
          </div>
          <div class="record-score" style="color: ${scoreColor};">
            ⭐ ${record.score}/10
          </div>
        </div>
        <div class="record-diary">
          📝 ${record.diary || '无学习日记'}
        </div>
      `;

      dateCard.appendChild(recordDiv);
    });

    container.appendChild(dateCard);
  });
}

function showError(message) {
  const container = document.getElementById('history-container');
  container.innerHTML = `
    <div class="card fade-in">
      <div class="card-title">
        <span>❌</span> 出错了
      </div>
      <div class="card-content">
        <p style="color: #ef4444;">${message}</p>
        <div style="text-align: center; margin-top: 1.5rem;">
          <button class="btn btn-primary" onclick="loadHistory()">
            重试
          </button>
        </div>
      </div>
    </div>
  `;
}
