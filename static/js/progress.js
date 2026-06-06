// 产品经理进化论 - 技能进度页逻辑

document.addEventListener('DOMContentLoaded', () => {
  loadProgress();
});

async function loadProgress() {
  try {
    const resp = await fetch('/api/progress');
    const data = await resp.json();
    renderStats(data);
    renderSkills(data.skills);
  } catch (error) {
    showError('加载进度失败');
  }
}

async function renderStats(data) {
  let totalKp = 0;
  let masteredKp = 0;
  let totalProgress = 0;

  data.skills.forEach(skill => {
    skill.knowledge_points.forEach(kp => {
      totalKp++;
      totalProgress += kp.progress;
      if (kp.progress >= 70) {
        masteredKp++;
      }
    });
  });

  const avgProgress = totalKp > 0 ? Math.round(totalProgress / totalKp) : 0;

  // 获取学习天数
  let totalDays = 0;
  try {
    const histResp = await fetch('/api/history');
    const histData = await histResp.json();
    totalDays = (histData.history || []).length;
  } catch (e) {
    totalDays = 0;
  }

  document.getElementById('stat-kp').textContent = totalKp;
  document.getElementById('stat-pass').textContent = masteredKp;
  document.getElementById('stat-avg').textContent = avgProgress + '%';
  document.getElementById('stat-days').textContent = totalDays;
}

function renderSkills(skills) {
  const container = document.getElementById('skills-container');
  container.innerHTML = '';

  skills.forEach(skill => {
    const masteredCount = skill.knowledge_points.filter(kp => kp.progress >= 70).length;
    const totalCount = skill.knowledge_points.length;
    const avgRate = skill.avg_progress || 0;

    const skillCard = document.createElement('div');
    skillCard.className = 'skill-card fade-in';
    skillCard.innerHTML = `
      <div class="skill-header" onclick="toggleSkill(this.parentElement)">
        <div style="flex: 1;">
          <div class="skill-name">${skill.name}</div>
          <div class="skill-meta">
            <span>已掌握 ${masteredCount}/${totalCount} 个知识点</span>
            <span>连续学习 ${skill.consecutive_days} 天</span>
          </div>
        </div>
        <div style="font-size: 0.75rem;">▼</div>
      </div>
      <div class="progress-bar">
        <div class="progress-fill" style="width: ${Math.min(avgRate, 100)}%;"></div>
      </div>
      <div class="skill-points">
        ${skill.knowledge_points.map(kp => {
          const isMastered = kp.progress >= 70;
          return `
            <div class="skill-point-item">
              <span class="skill-point-name">${kp.name}</span>
              <span class="skill-point-badge ${isMastered ? 'badge-mastered' : 'badge-pending'}">
                ${Math.round(kp.progress)}%
              </span>
            </div>
          `;
        }).join('')}
      </div>
    `;

    container.appendChild(skillCard);
  });
}

function toggleSkill(card) {
  card.classList.toggle('expanded');
}

function showError(message) {
  const container = document.getElementById('skills-container');
  container.innerHTML = `
    <div class="card fade-in">
      <div class="card-title">
        <span>❌</span> 出错了
      </div>
      <div class="card-content">
        <p style="color: #ef4444;">${message}</p>
        <div style="text-align: center; margin-top: 1.5rem;">
          <button class="btn btn-primary" onclick="loadProgress()">
            重试
          </button>
        </div>
      </div>
    </div>
  `;
}

