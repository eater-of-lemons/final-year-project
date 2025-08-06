chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'analyze_sentiment') {
    fetch('http://localhost:5050/analyze', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        comments: request.comments
      })
    })
    .then(response => response.json())
    .then(data => sendResponse(data))
    .catch(error => {
      console.error('error:', error);
      sendResponse({error: "failed"});
    });
    
    return true; // required for async response
  }
});