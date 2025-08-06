// create sentiment analysis panel
const panel = document.createElement('div');
panel.id = 'reel-sentiment-dashboard';
panel.style.cssText = `
  position: fixed;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  width: 160px;
  background: rgba(255,255,255,0.96);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 15px;
  z-index: 2147483647;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  font-family: Arial, sans-serif;
  display: none;
`;
document.body.appendChild(panel);

// show alerts/notifications
function showAlert(message, isError = true) {
  try {
    if (chrome.notifications) {
      chrome.notifications.create({
        type: 'basic',
        iconUrl: chrome.runtime.getURL('icons/pos.png'),
        title: isError ? 'Error' : 'Success',
        message: message
      });
      return;
    }
    alert(`${isError ? '⚠️' : '✅'} ${message}`);
  } catch (e) {
    console.error('alert failed:', e);
  }
}

// collect visible comments with retries
async function getVisibleCommentsWithRetry(maxAttempts = 5, delay = 800) {
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    const comments = Array.from(document.querySelectorAll("ul span[dir='auto']"))
      .map(el => el.textContent.trim())
      .filter(text => text.length > 0 && !text.startsWith('@'));
    
    if (comments.length > 0) {
      return comments;
    }
    
    if (attempt < maxAttempts) {
      console.log(`no comments found, retrying (${attempt}/${maxAttempts})`);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  return [];
}

// send comments to backend for analysis
async function analyzeWithBackend(comments) {
  try {
    const response = await fetch('http://localhost:5050/analyze', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({comments})
    });
    
    if (!response.ok) {
      const error = await response.text();
      throw new Error(`server error: ${error}`);
    }
    return await response.json();
  } catch (error) {
    console.error("fetch failed:", error);
    showAlert("failed server connection");
    return null;
  }
}

// show loading state in panel
function showLoadingState() {
  panel.innerHTML = `
    <div style="text-align: center;">
      <div style="font-size: 24px;">⏳</div>
      <div style="font-size: 13px; color: #555;">Loading comments...</div>
    </div>
  `;
  panel.style.display = 'block';
}

// update panel with sentiment results
function updateDashboard(sentiment) {
  if (!sentiment) {
    panel.innerHTML = `
      <div style="text-align: center;">
        <div style="font-size: 24px;">💬</div>
        <div style="font-size: 13px; color: #555;">Open comments to analyze</div>
      </div>
    `;
    return;
  }

  const emoji = sentiment.compound >= 0.5 ? '😊' : sentiment.compound <= -0.5 ? '😠' : '😐';
  
  panel.innerHTML = `
    <div style="text-align: center;">
      <div style="font-size: 28px;">${emoji}</div>
      <div style="font-size: 14px; color: #555; margin: 8px 0;">
        ${(sentiment.compound*100).toFixed(1)}% Sentiment
      </div>
      <div style="height: 6px; background: #eee; border-radius: 3px; overflow: hidden; margin: 0 auto; max-width: 80%; position: relative;">
        <div style="width: ${sentiment.positive * 100}%; height: 100%; background: #4CAF50; position: absolute; left: 0;"></div>
        <div style="width: ${sentiment.neutral * 100}%; height: 100%; background: #FFC107; position: absolute; left: ${sentiment.positive * 100}%;"></div>
        <div style="width: ${sentiment.negative * 100}%; height: 100%; background: #F44336; position: absolute; left: ${(sentiment.positive + sentiment.neutral) * 100}%;"></div>
      </div>
      <div style="font-size: 11px; color: #888; margin-top: 12px;">
        ${sentiment.processed_comments} comments analyzed
      </div>
    </div>
  `;
  panel.style.display = 'block';
}

// reel monitoring system
let currentReelId = null;
let monitoringInterval = null;
let isMonitoring = false;

// get current reel id from url
function getReelId() {
  const url = window.location.href;
  const reelMatch = url.match(/\/p\/([^\/?]+)/);
  return reelMatch ? reelMatch[1] : null;
}

// main analysis function
async function analyzeVisibleComments() {
  showLoadingState();
  try {
    const comments = await getVisibleCommentsWithRetry();
    if (comments.length === 0) {
      console.log('no comments found');
      updateDashboard(null);
      return;
    }
    
    const result = await analyzeWithBackend(comments);
    updateDashboard(result || null);
  } catch (e) {
    console.error('analysis failed:', e);
    updateDashboard(null);
  }
}

// start monitoring for reel changes
function startMonitoring() {
  if (isMonitoring) return;
  isMonitoring = true;
  
  currentReelId = getReelId();
  monitoringInterval = setInterval(async () => {
    const newReelId = getReelId();
    if (newReelId && newReelId !== currentReelId) {
      currentReelId = newReelId;
      await analyzeVisibleComments();
    }
  }, 1500);
}

// stop monitoring
function stopMonitoring() {
  isMonitoring = false;
  if (monitoringInterval) {
    clearInterval(monitoringInterval);
    monitoringInterval = null;
  }
}

// start if already on a reel
if (getReelId()) {
  setTimeout(() => {
    startMonitoring();
  }, 2000);
}

// handle messages from extension
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'ANALYZE_REEL') {
    analyzeVisibleComments().then(() => {
      startMonitoring();
      sendResponse({success: true});
    });
    return true;
  }
  
  if (request.action === 'STOP_ANALYSIS') {
    stopMonitoring();
    sendResponse({success: true});
    return true;
  }
});

// cleanup on page unload
window.addEventListener('beforeunload', stopMonitoring);