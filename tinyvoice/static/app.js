const state = {
  mediaRecorder: null,
  chunks: [],
};

const $ = (id) => document.getElementById(id);

function showError(message) {
  $('preview-box').textContent = `Error: ${message}`;
}

async function api(path, options = {}) {
  const response = await fetch(path, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.error || `Request failed with ${response.status}`);
  }
  return payload;
}

function renderAudit(entries = []) {
  $('audit-log').textContent = entries.length
    ? entries.map((entry) => `${entry.time} ${entry.event}: ${entry.command || entry.error || entry.transcript || ''}`).join('\n')
    : 'No audit entries yet.';
}

function renderPreview(preview) {
  if (!preview || !preview.ok) {
    $('preview-box').textContent = preview?.error || 'No allowlisted command matched.';
    return;
  }
  $('preview-box').textContent = [
    `Matched: ${preview.description}`,
    `Command: ${preview.command}`,
    `Auto-run safe: ${preview.auto_run_safe ? 'yes, but this UI still asks for confirmation' : 'no'}`,
  ].join('\n');
}

async function refreshStatus() {
  const payload = await api('/api/status');
  $('model-pill').textContent = payload.model.ready ? 'Ready' : 'Needs download';
  $('model-message').textContent = payload.model.message;
  $('model-path').textContent = `Model folder: ${payload.model.models_dir}`;
  $('allowed-list').innerHTML = payload.allowed_phrases.map((phrase) => `<li>${phrase}</li>`).join('');
  renderAudit(payload.audit);
}

async function downloadModel() {
  $('download-model').disabled = true;
  $('model-message').textContent = 'Downloading/loading Whisper model. This can take a while on first run…';
  try {
    const payload = await api('/api/model/download', { method: 'POST' });
    $('model-message').textContent = payload.model.message;
    await refreshStatus();
  } catch (error) {
    $('model-message').textContent = error.message;
  } finally {
    $('download-model').disabled = false;
  }
}

async function previewTranscript() {
  try {
    const payload = await api('/api/intent', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ transcript: $('transcript').value }),
    });
    renderPreview(payload.preview);
  } catch (error) {
    showError(error.message);
  }
}

async function runTranscript() {
  try {
    const payload = await api('/api/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ transcript: $('transcript').value, confirm: true }),
    });
    const result = payload.result;
    $('command-output').textContent = [
      `$ ${result.command}`,
      result.stdout || '',
      result.stderr ? `stderr:\n${result.stderr}` : '',
      result.error ? `error: ${result.error}` : '',
    ].filter(Boolean).join('\n');
    renderAudit(payload.audit);
  } catch (error) {
    showError(error.message);
  }
}

async function uploadBlob(blob, filename = 'recording.webm') {
  const formData = new FormData();
  formData.append('audio', blob, filename);
  const payload = await api('/api/transcribe', { method: 'POST', body: formData });
  $('transcript').value = payload.transcript;
  renderPreview(payload.preview);
}

async function startRecording() {
  if (!navigator.mediaDevices?.getUserMedia) {
    showError('Browser microphone API is unavailable. Use the file picker instead.');
    return;
  }
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  state.chunks = [];
  state.mediaRecorder = new MediaRecorder(stream);
  state.mediaRecorder.ondataavailable = (event) => {
    if (event.data.size > 0) state.chunks.push(event.data);
  };
  state.mediaRecorder.onstop = async () => {
    stream.getTracks().forEach((track) => track.stop());
    $('recording-pill').textContent = 'Transcribing…';
    try {
      await uploadBlob(new Blob(state.chunks, { type: 'audio/webm' }));
      $('recording-pill').textContent = 'Idle';
    } catch (error) {
      showError(error.message);
      $('recording-pill').textContent = 'Idle';
    }
  };
  state.mediaRecorder.start();
  $('record').disabled = true;
  $('stop').disabled = false;
  $('recording-pill').textContent = 'Recording';
}

function stopRecording() {
  if (state.mediaRecorder && state.mediaRecorder.state !== 'inactive') {
    state.mediaRecorder.stop();
  }
  $('record').disabled = false;
  $('stop').disabled = true;
}

async function uploadSelectedFile() {
  const file = $('audio-file').files[0];
  if (!file) {
    showError('Choose an audio file first.');
    return;
  }
  try {
    await uploadBlob(file, file.name);
  } catch (error) {
    showError(error.message);
  }
}

$('download-model').addEventListener('click', downloadModel);
$('preview').addEventListener('click', previewTranscript);
$('run').addEventListener('click', runTranscript);
$('record').addEventListener('click', () => startRecording().catch((error) => showError(error.message)));
$('stop').addEventListener('click', stopRecording);
$('upload').addEventListener('click', uploadSelectedFile);

refreshStatus().catch((error) => showError(error.message));
