document.addEventListener('DOMContentLoaded', function() {
  const analyzeBtn = document.getElementById('analyzeBtn');
  const stopBtn = document.createElement('button');
  stopBtn.textContent = 'Stop Auto-Analysis';
  stopBtn.id = 'stopBtn';
  stopBtn.style.cssText = `
    margin-top: 10px;
    padding: 8px 12px;
    width: 100%;
    background-color: #ff4444;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  `;
  
  const statusDiv = document.createElement('div');
  statusDiv.style.cssText = `
    margin-top: 10px;
    font-size: 13px;
    text-align: center;
  `;
  
  document.body.appendChild(stopBtn);
  document.body.appendChild(statusDiv);

  analyzeBtn.addEventListener('click', function() {
    statusDiv.textContent = 'Starting analysis...';
    statusDiv.style.color = '#555';

    chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
      if (!tabs[0]) {
        statusDiv.textContent = 'No active tab found';
        statusDiv.style.color = 'red';
        return;
      }

      chrome.scripting.executeScript({
        target: { tabId: tabs[0].id },
        files: ['content.js']
      }, () => {
        chrome.tabs.sendMessage(tabs[0].id, { 
          action: 'ANALYZE_REEL'
        }, (response) => {
          if (chrome.runtime.lastError) {
            statusDiv.textContent = 'Error: Not on Instagram Reel';
            statusDiv.style.color = 'red';
          } else if (response && !response.success) {
            statusDiv.textContent = `Error: ${response.error}`;
            statusDiv.style.color = 'red';
          } else {
            statusDiv.textContent = 'Analysis started! Auto-updating on reel changes.';
            statusDiv.style.color = 'green';
          }
        });
      });
    });
  });

  stopBtn.addEventListener('click', function() {
    statusDiv.textContent = 'Stopping auto-analysis...';
    statusDiv.style.color = '#555';

    chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
      if (!tabs[0]) return;
      
      chrome.tabs.sendMessage(tabs[0].id, { 
        action: 'STOP_ANALYSIS'
      }, (response) => {
        if (chrome.runtime.lastError) {
          statusDiv.textContent = 'Error stopping analysis';
          statusDiv.style.color = 'red';
        } else {
          statusDiv.textContent = 'Auto-analysis stopped';
          statusDiv.style.color = '#555';
        }
      });
    });
  });

  // button interaction effects
  [analyzeBtn, stopBtn].forEach(btn => {
    btn.addEventListener('mousedown', () => {
      btn.style.transform = 'scale(0.98)';
    });
    btn.addEventListener('mouseup', () => {
      btn.style.transform = 'scale(1)';
    });
    btn.addEventListener('mouseleave', () => {
      btn.style.transform = 'scale(1)';
    });
  });
});