// Wait for Telegram Web App to be ready
window.Telegram.WebApp.ready();

// Get user data from Telegram
const user = window.Telegram.WebApp.initDataUnsafe.user || { id: 'test-user-123' }; // fallback for local testing

const tapButton = document.getElementById('tapButton');
const statusDiv = document.getElementById('status');

// Simple debounce / disable during request
let isProcessing = false;

tapButton.addEventListener('click', async () => {
  if (isProcessing) return;
  isProcessing = true;
  tapButton.disabled = true;
  tapButton.textContent = 'Processing...';

  statusDiv.classList.remove('hidden', 'success', 'error');
  statusDiv.textContent = '';

  try {
    // Simulate 3-5 second delay (anti-fraud interaction time)
    await new Promise(resolve => setTimeout(resolve, 3000 + Math.random() * 2000));

    const response = await fetch('http://localhost:5000/tap', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: user.id.toString(),
        timestamp: Date.now()
      })
    });

    const data = await response.json();

    if (response.ok) {
      statusDiv.textContent = data.message || 'Tap registered successfully!';
      statusDiv.classList.add('success');
    } else {
      statusDiv.textContent = data.message || 'Something went wrong';
      statusDiv.classList.add('error');
    }
  } catch (err) {
    statusDiv.textContent = 'Network error: ' + err.message;
    statusDiv.classList.add('error');
  } finally {
    isProcessing = false;
    tapButton.disabled = false;
    tapButton.textContent = 'TAP TO HELP';
  }
});