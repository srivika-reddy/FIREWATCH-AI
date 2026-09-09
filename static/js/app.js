const $ = (selector) => document.querySelector(selector);
const message = $('#message');
const statusClass = (status) => status === 'FIRE ALERT' ? 'alert' : status.toLowerCase();

function showMessage(text) { message.textContent = text; message.classList.add('show'); }
function clearMessage() { message.textContent = ''; message.classList.remove('show'); }
function percent(value) { return `${Math.round((value || 0) * 100)}% confidence`; }

function renderResult(result) {
  const status = $('#overall-status');
  status.textContent = result.status;
  status.className = statusClass(result.status);
  $('#last-update').textContent = result.fire_smoke.mode === 'demo/mock' ? 'Demo signal path active' : (result.fire_smoke.mode === 'real model' ? 'Live fire/smoke model signal' : 'Fire/smoke model unavailable');
  $('#scan-label').textContent = result.source ? `Latest: ${result.source}` : 'Latest scan';
  $('#fire-value').textContent = result.fire_smoke.fire ? '1' : '0';
  $('#smoke-value').textContent = result.fire_smoke.smoke ? '1' : '0';
  $('#people-value').textContent = result.objects.people;
  $('#animals-value').textContent = result.objects.animals;
  $('#vehicles-value').textContent = result.objects.vehicles;
  $('#fire-confidence').textContent = percent(result.fire_smoke.fire_confidence);
  $('#smoke-confidence').textContent = percent(result.fire_smoke.smoke_confidence);
  if (result.preview_url) $('#preview').innerHTML = `<img src="${result.preview_url}" alt="Processed monitoring frame">`;
  loadAlerts();
}

async function sendFile(file, endpoint) {
  clearMessage();
  if (!file) return;
  const form = new FormData(); form.append('file', file);
  try {
    const response = await fetch(endpoint, { method: 'POST', body: form });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Detection failed.');
    renderResult(result);
  } catch (error) { showMessage(error.message); }
}
$('#image-input').addEventListener('change', (event) => {
  const file = event.target.files[0];
  if (!file) return;

  $('#preview').innerHTML = `<img src="${URL.createObjectURL(file)}" alt="Selected monitoring frame">`;
  sendFile(file, '/api/detect/image');
});
$('#video-input').addEventListener('change', (event) => sendFile(event.target.files[0], '/api/detect/video'));
let cameraStream;
$('#start-button').addEventListener('click', async () => {
  clearMessage();
  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
    $('#preview').innerHTML = '<video id="camera-preview" autoplay muted playsinline></video>';
    $('#camera-preview').srcObject = cameraStream;
    $('#start-button').disabled = true;
    $('#stop-button').disabled = false;
  } catch (error) {
    showMessage('Camera unavailable or permission denied. Upload an image or video to continue monitoring.');
  }
});
$('#stop-button').addEventListener('click', () => {
  if (cameraStream) cameraStream.getTracks().forEach((track) => track.stop());
  cameraStream = undefined;
  $('#preview').innerHTML = '<div class="preview-empty"><span class="crosshair">+</span><strong>Upload a frame to begin</strong><span>Images and short video clips supported</span></div>';
  $('#start-button').disabled = false;
  $('#stop-button').disabled = true;
});

async function loadAlerts() {
  const response = await fetch('/api/alerts');
  const alerts = await response.json();
  const body = $('#history-body');
  if (!alerts.length) { body.innerHTML = '<tr><td colspan="7" class="empty-row">No alerts recorded yet.</td></tr>'; return; }
  body.innerHTML = alerts.map((alert) => {
    const date = new Date(alert.timestamp).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' });
    return `<tr><td>${date}</td><td><strong>${alert.alert_type}</strong></td><td>${Math.round(alert.confidence * 100)}%</td><td>${alert.people_count}</td><td>${alert.animal_count}</td><td>${alert.vehicle_count}</td><td><span class="status-tag ${statusClass(alert.status)}">${alert.status}</span></td></tr>`;
  }).join('');
}

$('#clear-history').addEventListener('click', async () => { await fetch('/api/alerts', { method: 'DELETE' }); loadAlerts(); });
loadAlerts();
