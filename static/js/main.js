// 产品经理进化论 - 主页面逻辑

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
    const resp = await fetch('/api/today');
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
    const resp = await fetch('/api/question', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        knowledge_name: currentData.knowledgeName,
        previous_weaknesses: currentData.previousWeaknesses
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
    await fetch('/api/current_learning', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data)
    });
  } catch (error) {
    console.log('保存当前进度失败');
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
            ${hasQuestionCached ? renderQuestion(currentData.question) : `
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
}

function typeWriter(text, elementId, speed = 20) {
  const element = document.getElementById(elementId);
  if (!element) return;
  
  let i = 0;
  element.innerHTML = '';
  
  function type() {
    if (i < text.length) {
      element.innerHTML += text.charAt(i);
      i++;
      setTimeout(type, speed);
    }
  }
  
  type();
}

// 渲染练习题（支持表格）
function renderQuestion(questionText) {
  // 检查是否包含表格
  if (questionText.includes('|') && questionText.includes('---')) {
    // 解析并渲染表格
    return parseAndRenderTable(questionText);
  }
  return questionText;
}

function parseAndRenderTable(text) {
  // 找到表格部分的开始和结束
  const lines = text.split('\n');
  let tableStart = -1;
  let tableEnd = -1;
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    // 检测表格开始（包含|且不是分隔行）
    if (line.includes('|') && !line.includes('---') && line.includes('知识点')) {
      tableStart = i;
    }
    // 检测表格结束（遇到空行或不含|的行，且已在表格中）
    if (tableStart >= 0 && tableEnd < 0) {
      if (line === '' || (!line.includes('|') && !line.includes('---'))) {
        tableEnd = i;
      }
    }
  }
  
  // 如果没找到明确的表格，使用整个文本
  if (tableStart < 0) {
    // 尝试找到包含|---的表格分隔行
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes('---')) {
        tableStart = 0;
        tableEnd = i;
        break;
      }
    }
  }
  
  if (tableStart < 0) {
    return text;  // 没有找到表格，返回原文本
  }
  
  if (tableEnd < 0) {
    tableEnd = lines.length;
  }
  
  // 提取表格行
  const tableLines = lines.slice(tableStart, tableEnd);
  
  // 解析表头和数据行
  const headers = [];
  const rows = [];
  let isFirstRow = true;
  
  for (const line of tableLines) {
    const trimmed = line.trim();
    if (trimmed === '' || trimmed.includes('---')) {
      continue;  // 跳过空行和分隔行
    }
    
    // 解析单元格
    const cells = trimmed.split('|').map(cell => cell.trim()).filter(cell => cell !== '');
    
    if (isFirstRow) {
      headers.push(...cells);
      isFirstRow = false;
    } else {
      rows.push(cells);
    }
  }
  
  if (headers.length === 0) {
    return text;
  }
  
  // 生成HTML表格
  let html = '<table class="quiz-table"><thead><tr>';
  headers.forEach(header => {
    html += `<th>${header}</th>`;
  });
  html += '</tr></thead><tbody>';
  
  rows.forEach(row => {
    html += '<tr>';
    for (let i = 0; i < headers.length; i++) {
      const cellValue = row[i] || '';
      if (cellValue) {
        html += `<td>${cellValue}</td>`;
      } else {
        html += `<td><input type="text" placeholder="请填写..." style="width:100%;border:none;background:transparent;font-size:inherit;padding:0.25rem;" /></td>`;
      }
    }
    html += '</tr>';
  });
  
  html += '</tbody></table>';
  
  return html;
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
    const resp = await fetch('/api/knowledge', {
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
    }, data.text.length * 20 + 500);
    
    if (questionLoaded && currentData.question) {
      document.getElementById('quiz-question').innerHTML = renderQuestion(currentData.question);
    }
  } catch (error) {
    showError('生成知识点讲解失败');
  }
}

function showQuizSection() {
  setStep(2);
  
  const quizSection = document.getElementById('quiz-section');
  const startContainer = document.getElementById('start-quiz-container');
  
  // 隐藏开始答题按钮容器
  startContainer.style.display = 'none';
  
  // 如果有缓存的练习题，直接渲染
  if (currentData.question && currentData.question.length > 0) {
    const quizQuestion = document.getElementById('quiz-question');
    if (quizQuestion) {
      quizQuestion.innerHTML = renderQuestion(currentData.question);
    }
  } else if (!questionLoaded) {
    loadQuestion();
  }
  
  // 显示练习题部分
  quizSection.style.display = 'block';
  quizSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function loadQuestion() {
  const quizQuestion = document.getElementById('quiz-question');
  if (!quizQuestion) return;
  
  try {
    const resp = await fetch('/api/question', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        knowledge_name: currentData.knowledgeName,
        previous_weaknesses: currentData.previousWeaknesses
      })
    });
    const data = await resp.json();

    currentData.question = data.question;
    currentData.referenceAnswer = data.reference;
    questionLoaded = true;
    
    quizQuestion.innerHTML = renderQuestion(data.question);
  } catch (error) {
    console.log('加载练习题失败');
  }
}

async function submitAnswer() {
  const userAnswer = document.getElementById('user-answer')?.value?.trim() || '';
  if (!userAnswer) {
    if (!confirm('请输入您的答案')) {
      return;
    }
    return;
  }

  // 标记练习题为已回答
  currentData.questionAnswered = true;
  await saveCurrentLearning({
    question_answered: true
  });

  const evalData = {
    question: currentData.question,
    user_answer: userAnswer,
    reference: currentData.referenceAnswer,
    knowledge_name: currentData.knowledgeName,
    skill_name: currentData.skillName,
    skill_consecutive_days: currentData.skillConsecutiveDays,
    knowledge_progress: currentData.knowledgeProgress,
    previous_weaknesses: currentData.previousWeaknesses,
    previous_strengths: currentData.previousStrengths,
    today_count: currentData.todayCount
  };

  sessionStorage.setItem('evalData', JSON.stringify(evalData));
  window.location.href = '/evaluate';
}

async function completeLearning() {
  setStep(4);

  const mainContent = document.getElementById('main-content');
  mainContent.innerHTML = `
    <div class="card fade-in">
      <div class="card-title">
        <span>📝</span> 学习日记
      </div>
      <div class="card-content">
        <div class="loading" style="justify-content: center;">
          <div class="spinner"></div>
          <span>正在生成今日学习日记...</span>
        </div>
      </div>
    </div>
  `;

  try {
    const resp = await fetch('/api/submit', {
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

function learnMore() {
  // 重新加载今日学习内容
  initPage();
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

