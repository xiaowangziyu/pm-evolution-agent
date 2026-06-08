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

// 封装 fetch 请求，自动带上 user_id（只通过 Header 传递，避免 HTTPS 重定向丢失 URL 参数）
async function fetchWithUserId(url, options = {}) {
  if (options.headers) {
    options.headers['X-User-Id'] = currentUserId;
  } else {
    options.headers = { 'X-User-Id': currentUserId };
  }
  return fetch(url, options);
}

let currentData = {
  skillName: '',
  skillConsecutiveDays: 0,
  knowledgeName: '',
  knowledgeProgress: 0,
  knowledgeText: '',  // 保存的知识点详解
  isIterative: false,  // 是否为迭代学习
  previousWeaknesses: [],
  previousStrengths: [],
  question: '',
  referenceAnswer: '',
  score: 0,
  evalText: '',
  strengths: [],
  weaknesses: [],
  summary: '',
  todayCount: 0,
  isResumed: false,  // 是否为恢复的进度
  questionAnswered: false  // 练习题是否已收到回答
};

let currentStep = 1;
let questionLoaded = false;  // 练习题是否已加载

document.addEventListener('DOMContentLoaded', () => {
  initPage();
});

async function initPage() {
  const mainContent = document.getElementById('main-content');
  // 显示初始加载状态
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
    // 检查是否有来自日记页的推荐结果
    const nextRecommendationStr = sessionStorage.getItem('nextRecommendation');
    
    if (nextRecommendationStr) {
      // 使用推荐的知识点
      console.log('使用LLM推荐的知识点');
      const recommendation = JSON.parse(nextRecommendationStr);
      
      currentData.skillName = recommendation.skill;
      currentData.knowledgeName = recommendation.knowledge_point;
      currentData.difficulty = recommendation.difficulty;
      currentData.knowledgeProgress = 0;
      currentData.knowledgeText = '';
      currentData.isIterative = false;
      currentData.previousWeaknesses = [];
      currentData.previousStrengths = [];
      currentData.todayCount = 0;
      currentData.isResumed = false;
      currentData.question = '';
      currentData.questionAnswered = false;
      
      // 清除推荐缓存
      sessionStorage.removeItem('nextRecommendation');
      
      // 加载新知识点
      await Promise.all([
        loadKnowledgeContent(),
        preloadQuestion()
      ]);
    } else {
      // 使用默认方式获取知识点
      const resp = await fetchWithUserId('/api/today');
      const data = await resp.json();

      currentData.skillName = data.skill_name;
      currentData.skillConsecutiveDays = data.skill_consecutive_days || 0;
      currentData.knowledgeName = data.knowledge_name;
      currentData.knowledgeProgress = data.knowledge_progress || 0;
      currentData.knowledgeText = data.knowledge_text || '';  // 保存的知识点详解
      currentData.isIterative = data.is_iterative || false;  // 是否为迭代学习
      currentData.previousWeaknesses = data.previous_weaknesses || [];
      currentData.previousStrengths = data.previous_strengths || [];
      currentData.todayCount = data.today_count || 0;
      currentData.isResumed = data.is_resumed || false;
      currentData.question = data.question || '';  // 恢复缓存的练习题
      currentData.questionAnswered = data.question_answered || false;  // 恢复练习题状态

      // 如果是恢复的进度（有保存的知识点详解），直接显示
      if (data.status === 'in_progress' && currentData.knowledgeText) {
        // 预加载练习题（使用缓存，不重新生成）
        preloadQuestion(true);
        showKnowledgeOnly(true);  // true 表示不需要再调用API
      } else {
        // 更新加载提示，告知用户正在生成内容
        mainContent.innerHTML = `
          <div class="card fade-in">
            <div class="card-content">
              <div class="loading" style="justify-content: center; padding: 3rem 0;">
                <div class="spinner"></div>
                <span>正在为你生成今日知识点和练习题...</span>
              </div>
            </div>
          </div>
        `;
        
        // 新知识点，预加载知识点和练习题
        await Promise.all([
          loadKnowledgeContent(),
          preloadQuestion()
        ]);
      }
    }
  } catch (error) {
    showError('加载失败，请稍后重试');
  }
}

async function preloadQuestion(useCache = false) {
  // 如果有缓存的题目且不需要强制刷新，直接返回
  if (useCache && currentData.question && currentData.question.length > 0) {
    questionLoaded = true;
    return;
  }
  
  try {
    const resp = await fetchWithUserId('/api/question', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        knowledge_name: currentData.knowledgeName,
        previous_weaknesses: currentData.previousWeaknesses,
        difficulty: currentData.difficulty || "中等"
      })
    });
    const data = await resp.json();
    currentData.question = data.question;
    currentData.referenceAnswer = data.reference;
    questionLoaded = true;
    
    // 保存到后端current_learning
    await saveCurrentLearning({
      knowledge_text: currentData.knowledgeText,
      question: currentData.question,
      reference: currentData.referenceAnswer,
      question_answered: false
    });
  } catch (error) {
    console.log('预加载练习题失败，将在需要时重新加载');
  }
}

async function saveCurrentLearning(data) {
  try {
    await fetchWithUserId('/api/current_learning', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        skill_name: currentData.skillName,
        knowledge_name: currentData.knowledgeName,
        knowledge_progress: currentData.knowledgeProgress,
        skill_consecutive_days: currentData.skillConsecutiveDays,
        is_iterative: currentData.isIterative,
        previous_weaknesses: currentData.previousWeaknesses,
        previous_strengths: currentData.previousStrengths,
        today_count: currentData.todayCount,
        ...data
      })
    });
  } catch (error) {
    console.log('保存当前学习状态失败');
  }
}

function showKnowledgeOnly(hasKnowledgeText) {
  setStep(1);

  const mainContent = document.getElementById('main-content');
  
  // 检查是否有练习题缓存
  const hasQuestionCached = currentData.question && currentData.question.length > 0;
  
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
        ${currentData.isIterative ? `
          <div style="margin-bottom: 1rem; padding: 1rem; background: #fff7ed; border-radius: 8px; border-left: 4px solid #f97316;">
            <strong>🔄 迭代学习</strong><br>
            <small>上次学习的不足之处：${currentData.previousWeaknesses.join('；')}</small>
          </div>
        ` : ''}
        <div id="knowledge-content" style="white-space: pre-wrap; line-height: 1.8;">
          ${currentData.knowledgeText}
        </div>
      </div>
    </div>
    <div id="start-quiz-container" style="text-align: center; margin: 0.5rem 0;">
      <button class="btn btn-primary" id="start-quiz-btn" onclick="showQuizSection()">
        开始答题
      </button>
    </div>
    <div id="quiz-section" style="display: none;">
      <div class="card fade-in">
        <div class="card-title">
          <span>❓</span> 练习题
        </div>
        <div class="card-content">
          <div id="quiz-question" style="margin-bottom: 1.5rem; padding: 1.25rem; background: #eff6ff; border-radius: 8px; border-left: 4px solid #6366f1;">
            ${hasQuestionCached ? currentData.question : `
              <div class="loading" style="justify-content: center;">
                <div class="spinner"></div>
                <span>正在加载练习题...</span>
              </div>
            `}
          </div>
          <label style="font-weight: 600; margin-bottom: 0.5rem; display: block;">你的回答：</label>
          <textarea id="user-answer" placeholder="请在此写下你的回答..."></textarea>
        </div>
      </div>
      <div style="text-align: center;">
        <button class="btn btn-primary" onclick="submitAnswer()">
          提交答案
        </button>
      </div>
    </div>
  `;

  if (hasKnowledgeText && !hasQuestionCached) {
    // 如果有知识点但没有练习题，异步加载练习题
    preloadQuestion();
  }
}

function showQuizSection() {
  setStep(2);
  
  // 如果练习题还没加载，先显示加载状态
  if (!questionLoaded) {
    document.getElementById('quiz-question').innerHTML = `
      <div class="loading" style="justify-content: center;">
        <div class="spinner"></div>
        <span>正在生成练习题...</span>
      </div>
    `;
    
    // 异步加载练习题
    preloadQuestion().then(() => {
      document.getElementById('quiz-question').textContent = currentData.question;
    });
  }
  
  document.getElementById('start-quiz-container').style.display = 'none';
  document.getElementById('quiz-section').style.display = 'block';
}

async function submitAnswer() {
  setStep(3);
  
  const userAnswer = document.getElementById('user-answer').value.trim();
  if (!userAnswer) {
    alert('请先输入你的回答');
    return;
  }
  
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
    
    // 保存评估数据到sessionStorage
    sessionStorage.setItem('evalData', JSON.stringify({
      skill_name: currentData.skillName,
      knowledge_name: currentData.knowledgeName,
      score: currentData.score,
      eval_text: currentData.evalText,
      summary: currentData.summary,
      strengths: currentData.strengths,
      weaknesses: currentData.weaknesses
    }));
    
    // 跳转到日记页面
    window.location.href = '/diary';
  } catch (error) {
    showError('评估失败，请重试');
  }
}

async function loadKnowledgeContent() {
  setStep(1);

  const mainContent = document.getElementById('main-content');
  
  // 先显示页面框架和知识点加载中提示
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
        ${currentData.previousWeaknesses.length > 0 ? `
          <div style="margin-bottom: 1rem; padding: 1rem; background: #fff7ed; border-radius: 8px; border-left: 4px solid #f97316;">
            <strong>🔄 迭代学习</strong><br>
            <small>上次学习的不足之处：${currentData.previousWeaknesses.join('；')}</small>
          </div>
        ` : ''}
        <div id="knowledge-content" style="white-space: pre-wrap; line-height: 1.8; min-height: 100px;">
          <div class="loading" style="justify-content: center; padding: 2rem 0;">
            <div class="spinner"></div>
            <span>正在生成知识点讲解...</span>
          </div>
        </div>
      </div>
    </div>
    <div id="start-quiz-container" style="text-align: center; margin: 0.5rem 0;">
      <button class="btn btn-primary" id="start-quiz-btn" onclick="showQuizSection()" disabled>
        开始答题
      </button>
    </div>
    <div id="quiz-section" style="display: none;">
      <div class="card fade-in">
        <div class="card-title">
          <span>❓</span> 练习题
        </div>
        <div class="card-content">
          <div id="quiz-question" style="margin-bottom: 1.5rem; padding: 1.25rem; background: #eff6ff; border-radius: 8px; border-left: 4px solid #6366f1;">
            <div class="loading" style="justify-content: center;">
              <div class="spinner"></div>
              <span>正在加载练习题...</span>
            </div>
          </div>
          <label style="font-weight: 600; margin-bottom: 0.5rem; display: block;">你的回答：</label>
          <textarea id="user-answer" placeholder="请在此写下你的回答..."></textarea>
        </div>
      </div>
      <div style="text-align: center;">
        <button class="btn btn-primary" onclick="submitAnswer()">
          提交答案
        </button>
      </div>
    </div>
  `;

  try {
    const resp = await fetchWithUserId('/api/knowledge', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        knowledge_name: currentData.knowledgeName,
        skill_name: currentData.skillName,
        skill_consecutive_days: currentData.skillConsecutiveDays || 0,
        knowledge_progress: currentData.knowledgeProgress || 0,
        previous_weaknesses: currentData.previousWeaknesses,
        previous_strengths: currentData.previousStrengths,
        today_count: currentData.todayCount || 0
      })
    });
    const data = await resp.json();

    currentData.knowledgeText = data.text;
    
    typeWriter(data.text, 'knowledge-content');
    
    setTimeout(() => {
      document.getElementById('start-quiz-btn').disabled = false;
    }, 500);
    
    // 保存到后端current_learning
    await saveCurrentLearning({
      knowledge_text: currentData.knowledgeText,
      question_answered: false
    });
  } catch (error) {
    showError('加载知识点失败');
  }
}

function typeWriter(text, elementId) {
  const element = document.getElementById(elementId);
  let i = 0;
  element.innerHTML = '';
  
  function type() {
    if (i < text.length) {
      element.innerHTML += text.charAt(i);
      i++;
      setTimeout(type, 10);
    }
  }
  
  type();
}

async function submitLearning() {
  const mainContent = document.getElementById('main-content');
  
  try {
    const resp = await fetchWithUserId('/api/submit', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        skill_name: currentData.skillName,
        knowledge_name: currentData.knowledgeName,
        score: currentData.score,
        eval_text: currentData.evalText,
        summary: currentData.summary || '',
        strengths: currentData.strengths,
        weaknesses: currentData.weaknesses
      })
    });
    const data = await resp.json();

    // 更新今日学习计数
    currentData.todayCount = data.today_count || currentData.todayCount + 1;

    mainContent.innerHTML = `
      <div class="card fade-in">
        <div class="card-title">
          <span>🎉</span> 本次学习完成！
        </div>
        <div class="card-content">
          <div style="text-align: center; margin-bottom: 1.5rem;">
            <span style="font-size: 4rem;">🎉</span>
          </div>
          <div style="padding: 1rem; background: #e0f2fe; border-radius: 8px; margin-bottom: 1rem; text-align: center;">
            今日已学习 ${currentData.todayCount} 个知识点
          </div>
          <div style="padding: 1.25rem; background: #fef3c7; border-radius: 8px;">
            <strong>📝 学习日记</strong><br>
            ${data.diary}
          </div>
        </div>
      </div>
      <div style="text-align: center; margin-top: 1.5rem;">
        <button class="btn btn-primary" onclick="learnMore()">
          继续学习
        </button>
      </div>
      <div style="text-align: center; margin-top: 1rem;">
        <a href="/progress" class="btn btn-secondary" style="margin-right: 1rem;">
          查看进度
        </a>
        <a href="/history" class="btn btn-secondary">
          查看历史
        </a>
      </div>
    `;
  } catch (error) {
    showError('提交失败');
  }
}

async function learnMore() {
  // 调用 LLM 推荐接口获取下一个知识点
  console.log('learnMore() 被调用了');
  const mainContent = document.getElementById('main-content');
  mainContent.innerHTML = `
    <div class="card fade-in">
      <div class="card-content">
        <div class="loading" style="justify-content: center; padding: 3rem 0;">
          <div class="spinner"></div>
          <span>正在为你推荐下一个知识点...</span>
        </div>
      </div>
    </div>
  `;
  
  try {
    console.log('开始调用 /api/next_recommendation');
    const resp = await fetchWithUserId('/api/next_recommendation', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'}
    });
    console.log('/api/next_recommendation 响应状态:', resp.status);
    const recommendation = await resp.json();
    console.log('/api/next_recommendation 响应内容:', recommendation);
    
    // 更新当前数据为推荐的内容
    currentData.skillName = recommendation.skill;
    currentData.knowledgeName = recommendation.knowledge_point;
    currentData.difficulty = recommendation.difficulty; // 保存推荐的难度
    
    // 清空之前的状态
    currentData.knowledgeText = '';
    currentData.question = '';
    currentData.referenceAnswer = '';
    currentData.isIterative = false;
    currentData.previousWeaknesses = [];
    currentData.previousStrengths = [];
    currentData.questionAnswered = false;
    questionLoaded = false;
    
    // 清除可能存在的恢复状态
    clearCurrentLearning();
    
    // 显示推荐理由（可选）
    if (recommendation.reason) {
      console.log('推荐理由:', recommendation.reason);
    }
    
    // 加载新知识点
    await loadKnowledgeContent();
    await preloadQuestion();
    
    // 显示知识点
    showKnowledgeOnly(false);
    
  } catch (error) {
    console.error('获取推荐失败，使用默认方式:', error);
    // 失败时降级到原方式
    initPage();
  }
}

async function clearCurrentLearning() {
  // 调用后端清除当前学习状态
  try {
    await fetchWithUserId('/api/current_learning/clear', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'}
    });
  } catch (error) {
    // 清除失败没关系，忽略
  }
}

function showCompletedPage(lastRecord) {
  const mainContent = document.getElementById('main-content');
  let content = '';

  if (lastRecord) {
    content = `
      <div class="card fade-in">
        <div class="card-title">
          <span>✅</span> 今日学习已完成！
        </div>
        <div class="card-content">
          <div style="text-align: center; margin-bottom: 1.5rem;">
            <span style="font-size: 4rem;">🎉</span>
          </div>
          <div style="padding: 1.25rem; background: #f0fdf4; border-radius: 8px;">
            <div style="margin-bottom: 0.75rem;"><strong>📅 今日学习：</strong>${lastRecord.date}</div>
            <div style="margin-bottom: 0.75rem;"><strong>📚 技能领域：</strong>${lastRecord.skill}</div>
            <div style="margin-bottom: 0.75rem;"><strong>🎯 知识点：</strong>${lastRecord.knowledge}</div>
            <div style="margin-bottom: 0.75rem;"><strong>⭐ 得分：</strong>${lastRecord.score}/10</div>
            <hr style="margin: 1rem 0; border: none; border-top: 1px dashed #d1d5db;">
            <div><strong>📝 学习日记：</strong><br>${lastRecord.diary}</div>
          </div>
        </div>
      </div>
    `;
  } else {
    content = `
      <div class="card fade-in">
        <div class="card-title">
          <span>✅</span> 今日学习已完成！
        </div>
        <div class="card-content" style="text-align: center;">
          <span style="font-size: 4rem;">🎉</span>
          <p style="margin-top: 1rem; color: #64748b;">明天再来继续学习吧！</p>
        </div>
      </div>
    `;
  }

  mainContent.innerHTML = content + `
    <div style="text-align: center;">
      <a href="/progress" class="btn btn-secondary" style="margin-right: 1rem;">
        查看进度
      </a>
      <a href="/history" class="btn btn-primary">
        查看历史
      </a>
    </div>
  `;

  setStep(4);
}

function setStep(step) {
  currentStep = step;
  const steps = document.querySelectorAll('.step-item');
  steps.forEach((el, index) => {
    if (index < step) {
      el.classList.add('active');
    } else {
      el.classList.remove('active');
    }
  });
}

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
            重新开始
          </button>
        </div>
      </div>
    </div>
  `;
}