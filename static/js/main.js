// 产品经理进化论 - 主页面逻辑
console.log('main.js 已加载');

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

// 封装 fetch 请求，自动带上 user_id（只通过 Header 传递）
async function fetchWithUserId(url, options = {}) {
  if (!options.headers) {
    options.headers = {};
  }
  options.headers['X-User-Id'] = currentUserId;
  return fetch(url, options);
}

// 当前学习状态（整个流程在同一个页面，不跳转）
let currentData = {
  skillName: '',
  knowledgeName: '',
  knowledgeText: '',
  question: '',
  referenceAnswer: '',
  score: 0,
  evalText: '',
  strengths: [],
  weaknesses: [],
  summary: '',
  suggestions: '',
  todayCount: 0
};

let currentStep = 1;

// 设置当前学习步骤
function setStep(step) {
  currentStep = step;
  const steps = document.querySelectorAll('.step-item');
  
  steps.forEach((s, i) => {
    // 移除所有类
    s.classList.remove('active');
    s.classList.remove('completed');
    
    // 根据步骤添加对应类
    if (i + 1 < step) {
      // 已完成的步骤
      s.classList.add('completed');
    } else if (i + 1 === step) {
      // 当前步骤
      s.classList.add('active');
    }
    // 未到达的步骤不添加任何类
  });
}

// 页面初始化
document.addEventListener('DOMContentLoaded', () => {
  initPage();
});

async function initPage() {
  const mainContent = document.getElementById('main-content');
  mainContent.innerHTML = `
    <div class="card fade-in">
      <div class="card-content">
        <div class="loading" style="justify-content: center; padding: 3rem 0;">
          <div class="spinner"></div>
          <span>正在准备今日学习内容...</span>
        </div>
      </div>
    </div>
  `;

  try {
    // 直接获取今日推荐知识点
    const resp = await fetchWithUserId('/api/today');
    const data = await resp.json();

    currentData.skillName = data.skill_name;
    currentData.knowledgeName = data.knowledge_name;
    currentData.knowledgeText = data.knowledge_text || '';
    currentData.todayCount = data.today_count || 0;
    currentData.question = data.question || '';
    currentData.referenceAnswer = data.reference || '';

    // 显示知识点
    showKnowledgeSection();

    // 如果还没有练习题，异步加载
    if (!currentData.question || currentData.question.length === 0) {
      await preloadQuestion();
    }
  } catch (error) {
    showError('加载失败，请刷新页面重试');
  }
}

// 预加载练习题
async function preloadQuestion() {
  try {
    const resp = await fetchWithUserId('/api/question', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        knowledge_name: currentData.knowledgeName
      })
    });
    const data = await resp.json();
    currentData.question = data.question;
    currentData.referenceAnswer = data.reference;
  } catch (error) {
    console.log('预加载练习题失败');
  }
}

// 显示知识点
function showKnowledgeSection() {
  setStep(1);

  const mainContent = document.getElementById('main-content');
  
  // 检查是否有知识点内容，如果没有则显示加载状态并尝试加载
  const hasContent = currentData.knowledgeText && currentData.knowledgeText.length > 0;
  
  mainContent.innerHTML = `
    <div class="card fade-in">
      <div class="card-title">
        <span>📚</span> 知识点
      </div>
      <div class="card-content">
        <div style="margin-bottom: 1rem; padding: 1rem; background: #f0fdf4; border-radius: 8px;">
          <strong>技能领域：</strong> ${currentData.skillName}<br>
          <strong>知识点：</strong> ${currentData.knowledgeName}
        </div>
        <div id="knowledge-content" style="white-space: pre-wrap; line-height: 1.8;">
          ${hasContent ? currentData.knowledgeText : '<div class="loading"><div class="spinner"></div><span>正在加载知识点内容...</span></div>'}
        </div>
      </div>
    </div>
    <div style="text-align: center; margin: 1rem 0;">
      <button class="btn btn-primary" onclick="showQuizSection()">
        开始答题
      </button>
    </div>
  `;

  // 如果没有知识点内容，尝试加载
  if (!hasContent && currentData.knowledgeName) {
    loadKnowledgeContent().then(() => {
      const contentEl = document.getElementById('knowledge-content');
      if (contentEl && currentData.knowledgeText) {
        contentEl.innerHTML = currentData.knowledgeText;
      }
    });
  }
}

// 显示练习题
function showQuizSection() {
  setStep(2);

  const mainContent = document.getElementById('main-content');
  mainContent.innerHTML = `
    <div class="card fade-in">
      <div class="card-title">
        <span>❓</span> 练习题
      </div>
      <div class="card-content">
        <div id="quiz-question" style="margin-bottom: 1.5rem; padding: 1.25rem; background: #eff6ff; border-radius: 8px; border-left: 4px solid #6366f1;">
          ${currentData.question && currentData.question.length > 0 ? currentData.question : '正在加载练习题...'}
        </div>
        <label style="font-weight: 600; margin-bottom: 0.5rem; display: block;">你的回答：</label>
        <textarea id="user-answer" placeholder="请在此写下你的回答..." style="width: 100%; min-height: 150px; padding: 1rem; border: 1px solid #e5e7eb; border-radius: 8px; resize: vertical;"></textarea>
      </div>
    </div>
    <div style="display: flex; gap: 1rem; justify-content: center; margin: 1rem 0;">
      <button class="btn btn-secondary" onclick="showKnowledgeSection()">
        返回知识点
      </button>
      <button class="btn btn-primary" onclick="submitAnswer()">
        提交答案
      </button>
    </div>
  `;

  // 如果没有练习题，先加载
  if (!currentData.question || currentData.question.length === 0) {
    preloadQuestion().then(() => {
      const qEl = document.getElementById('quiz-question');
      if (qEl && currentData.question) {
        qEl.textContent = currentData.question;
      }
    });
  }
}

// 提交答案
async function submitAnswer() {
  const userAnswer = document.getElementById('user-answer').value.trim();
  if (!userAnswer) {
    alert('请先输入你的回答');
    return;
  }

  setStep(3);

  const mainContent = document.getElementById('main-content');
  mainContent.innerHTML = `
    <div class="card fade-in">
      <div class="card-title">
        <span>🤖</span> AI评估中...
      </div>
      <div class="card-content">
        <div class="loading" style="justify-content: center; padding: 3rem 0;">
          <div class="spinner"></div>
          <span>AI正在评估你的回答...</span>
        </div>
      </div>
    </div>
  `;

  try {
    const resp = await fetchWithUserId('/api/evaluate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        question: currentData.question,
        reference: currentData.referenceAnswer,
        user_answer: userAnswer,
        knowledge_name: currentData.knowledgeName
      })
    });
    const data = await resp.json();

    currentData.score = data.score;
    currentData.evalText = data.eval_text;
    currentData.strengths = data.strengths || [];
    currentData.weaknesses = data.weaknesses || [];
    currentData.summary = data.summary || '';
    currentData.suggestions = data.suggestions || '';

    // 从eval_text中提取建议（兼容旧格式）
    if (!currentData.suggestions && currentData.evalText) {
      const suggestionMatch = currentData.evalText.match(/建议[：:]\s*([^。\n]+)/);
      if (suggestionMatch) {
        currentData.suggestions = suggestionMatch[1].trim();
      }
    }

    // 直接显示评估结果（不跳转）
    showEvaluationResult();
  } catch (error) {
    showError('评估失败，请重试');
  }
}

// 显示评估结果
function showEvaluationResult() {
  const mainContent = document.getElementById('main-content');
  const scoreColor = currentData.score >= 8 ? '#10b981' : currentData.score >= 6 ? '#f59e0b' : '#ef4444';

  mainContent.innerHTML = `
    <div class="card fade-in">
      <div class="card-title">
        <span>📊</span> AI评估结果
      </div>
      <div class="card-content">
        <div style="text-align: center; margin-bottom: 1.5rem;">
          <div style="font-size: 4rem; font-weight: 800; color: ${scoreColor};">${currentData.score}/10</div>
        </div>
        ${currentData.summary ? `
          <div style="padding: 1rem; background: #f0fdf4; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid #10b981;">
            <strong>💡 总结：</strong>${currentData.summary}
          </div>
        ` : ''}
        ${currentData.strengths && currentData.strengths.length > 0 ? `
          <div style="margin-bottom: 1rem;">
            <strong>✅ 达标之处：</strong>
            <ul style="margin-top: 0.5rem; padding-left: 1.5rem;">
              ${currentData.strengths.map(s => `<li>${s}</li>`).join('')}
            </ul>
          </div>
        ` : ''}
        ${currentData.weaknesses && currentData.weaknesses.length > 0 ? `
          <div style="margin-bottom: 1rem;">
            <strong>📌 不足之处：</strong>
            <ul style="margin-top: 0.5rem; padding-left: 1.5rem;">
              ${currentData.weaknesses.map(w => `<li>${w}</li>`).join('')}
            </ul>
          </div>
        ` : ''}
        ${currentData.suggestions ? `
          <div style="padding: 1rem; background: #eff6ff; border-radius: 8px; border-left: 4px solid #3b82f6;">
            <strong>🎯 建议：</strong>${currentData.suggestions}
          </div>
        ` : ''}
        <div id="reference-answer-container" style="display: none; margin-top: 1rem; padding: 1rem; background: #f9fafb; border-radius: 8px; border: 1px solid #e5e7eb;">
          <strong>📝 AI参考答案：</strong>
          <div style="margin-top: 0.75rem; line-height: 1.8;">${currentData.referenceAnswer || '暂无参考答案'}</div>
        </div>
      </div>
      <div style="display: flex; gap: 1rem; justify-content: center; margin-top: 1.5rem;">
        <button class="btn btn-secondary" onclick="toggleReferenceAnswer()">
          查看AI答案
        </button>
        <button class="btn btn-primary" onclick="generateDiary()">
          生成学习日记
        </button>
      </div>
    </div>
  `;
}

// 切换显示/隐藏参考答案
function toggleReferenceAnswer() {
  const container = document.getElementById('reference-answer-container');
  const button = document.querySelector('.btn-secondary');
  if (container.style.display === 'none' || container.style.display === '') {
    container.style.display = 'block';
    button.textContent = '隐藏AI答案';
  } else {
    container.style.display = 'none';
    button.textContent = '查看AI答案';
  }
}

// 生成学习日记
async function generateDiary() {
  setStep(4);

  const mainContent = document.getElementById('main-content');
  mainContent.innerHTML = `
    <div class="card fade-in">
      <div class="card-title">
        <span>📝</span> 正在生成学习日记...
      </div>
      <div class="card-content">
        <div class="loading" style="justify-content: center; padding: 3rem 0;">
          <div class="spinner"></div>
          <span>请稍候，正在生成学习日记...</span>
        </div>
      </div>
    </div>
  `;

  try {
    const resp = await fetchWithUserId('/api/submit', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        skill_name: currentData.skillName,
        knowledge_name: currentData.knowledgeName,
        score: currentData.score,
        eval_text: currentData.evalText,
        summary: currentData.summary,
        strengths: currentData.strengths,
        weaknesses: currentData.weaknesses
      })
    });
    const data = await resp.json();

    const todayCount = data.today_count || 1;
    const dateStr = data.date;

    mainContent.innerHTML = `
      <div class="card fade-in">
        <div class="card-title">
          <span>🎉</span> 本次学习完成！
        </div>
        <div class="card-content">
          <div style="padding: 1rem; background: #e0f2fe; border-radius: 8px; margin-bottom: 1.5rem; text-align: center;">
            <div style="font-size: 1.25rem; font-weight: 600;">今日已学习 <span style="color: #3b82f6;">${todayCount}</span> 个知识点</div>
          </div>
          <div style="margin-bottom: 1.5rem; padding: 1rem; background: #f0fdf4; border-radius: 8px;">
            <div style="margin-bottom: 0.5rem;"><strong>📅 学习日期：</strong>${dateStr}</div>
            <div style="margin-bottom: 0.5rem;"><strong>📚 技能领域：</strong>${currentData.skillName}</div>
            <div style="margin-bottom: 0.5rem;"><strong>🎯 知识点：</strong>${currentData.knowledgeName}</div>
            <div style="margin-bottom: 0.5rem;"><strong>⭐ 得分：</strong>${currentData.score}/10</div>
          </div>
          <div style="padding: 1.25rem; background: #fef3c7; border-radius: 8px; border-left: 4px solid #f59e0b;">
            <strong>📝 学习日记</strong>
            <div style="margin-top: 0.75rem; line-height: 1.8;">${data.diary}</div>
          </div>
        </div>
        <div style="display: flex; gap: 1rem; justify-content: center; margin-top: 1.5rem;">
          <button class="btn btn-secondary" onclick="window.location.href='/progress'">
            查看进度
          </button>
          <button class="btn btn-secondary" onclick="window.location.href='/history'">
            查看历史
          </button>
          <button class="btn btn-primary" onclick="learnMore()">
            继续学习
          </button>
        </div>
      </div>
    `;
  } catch (error) {
    showError('生成日记失败，请重试');
  }
}

// 继续学习 - 调用 LLM 推荐下一个知识点
async function learnMore() {
  setStep(1);

  const mainContent = document.getElementById('main-content');
  mainContent.innerHTML = `
    <div class="card fade-in">
      <div class="card-title">
        <span>🚀</span> 正在为你推荐下一个知识点...
      </div>
      <div class="card-content">
        <div class="loading" style="justify-content: center; padding: 3rem 0;">
          <div class="spinner"></div>
          <span>正在调用 AI 推荐合适的知识点...</span>
        </div>
      </div>
    </div>
  `;

  try {
    const resp = await fetchWithUserId('/api/next_recommendation', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'}
    });
    const recommendation = await resp.json();

    currentData.skillName = recommendation.skill;
    currentData.knowledgeName = recommendation.knowledge_point;
    currentData.knowledgeText = '';
    currentData.question = '';
    currentData.referenceAnswer = '';
    currentData.score = 0;
    currentData.evalText = '';
    currentData.strengths = [];
    currentData.weaknesses = [];
    currentData.summary = '';
    currentData.todayCount = 0;

    // 加载新知识点
    await Promise.all([
      loadKnowledgeContent(),
      preloadQuestion()
    ]);

    // 显示新知识点
    showKnowledgeSection();
  } catch (error) {
    console.error('获取推荐失败:', error);
    // 失败时回到默认逻辑
    initPage();
  }
}

// 加载知识点内容
async function loadKnowledgeContent() {
  try {
    const resp = await fetchWithUserId('/api/knowledge', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        knowledge_name: currentData.knowledgeName
      })
    });
    const data = await resp.json();
    currentData.knowledgeText = data.knowledge_text || '';
  } catch (error) {
    console.log('加载知识点失败');
  }
}

// 显示错误
function showError(message) {
  const mainContent = document.getElementById('main-content');
  mainContent.innerHTML = `
    <div class="card fade-in">
      <div class="card-title">
        <span>❌</span> 出错了
      </div>
      <div class="card-content">
        <p style="color: #ef4444;">${message}</p>
        <div style="text-align: center; margin-top: 1.5rem;">
          <button class="btn btn-primary" onclick="initPage()">
            返回首页
          </button>
        </div>
      </div>
    </div>
  `;
}
