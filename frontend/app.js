const sceneList = document.querySelector('#scene-list');
const sceneTemplate = document.querySelector('#scene-template');
const form = document.querySelector('#project-form');
const generateButton = document.querySelector('#generate-button');
const formMessage = document.querySelector('#form-message');

function addScene(values = {}) {
  const scene = sceneTemplate.content.cloneNode(true);
  const card = scene.querySelector('.scene-card');
  const sceneId = sceneList.children.length + 1;
  card.dataset.sceneId = sceneId;
  card.querySelector('.scene-index').textContent = String(sceneId).padStart(2, '0');
  card.querySelector('.scene-label').textContent = String(sceneId).padStart(2, '0');
  card.querySelector('.narration').value = values.narration || '';
  card.querySelector('.visual-prompt').value = values.visual_prompt || '';
  card.querySelectorAll('.voice-input').forEach((input) => {
    input.name = `voice-${sceneId}`;
    input.checked = input.value === (values.voice || '');
  });
  card.querySelector('.remove-scene').addEventListener('click', () => {
    if (sceneList.children.length === 1) return;
    card.remove();
    renumberScenes();
  });
  sceneList.appendChild(scene);
  updateCount();
}

function renumberScenes() {
  [...sceneList.children].forEach((card, index) => {
    const number = String(index + 1).padStart(2, '0');
    card.dataset.sceneId = index + 1;
    card.querySelector('.scene-index').textContent = number;
    card.querySelector('.scene-label').textContent = number;
    card.querySelectorAll('.voice-input').forEach((input) => { input.name = `voice-${index + 1}`; });
  });
  updateCount();
}

function updateCount() {
  const count = sceneList.children.length;
  document.querySelector('#scene-count').textContent = `${count} scene${count === 1 ? '' : 's'}`;
}

function collectScenes() {
  return [...sceneList.children].map((card, index) => ({
    scene_id: index + 1,
    narration: card.querySelector('.narration').value.trim(),
    visual_prompt: card.querySelector('.visual-prompt').value.trim(),
    voice: card.querySelector('.voice-input:checked').value || null,
  }));
}

function showResults(payload) {
  const grid = document.querySelector('#results-grid');
  grid.innerHTML = payload.scenes.map((scene) => `
    <article class="result-card">
      <div class="result-image-wrap"><img src="${scene.image_url}" alt="Generated visual for scene ${scene.scene_id}" loading="lazy"><span class="result-number">${String(scene.scene_id).padStart(2, '0')}</span></div>
      <div class="result-body"><div class="result-title"><span>Scene ${String(scene.scene_id).padStart(2, '0')}</span><a href="${scene.video_url}" target="_blank" rel="noreferrer">Open video ↗</a></div><audio controls src="${scene.audio_url}"></audio></div>
    </article>`).join('');
  document.querySelector('#result-project').textContent = payload.project_id;
  document.querySelector('#results-section').hidden = false;
  document.querySelector('#results-section').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

document.querySelector('#add-scene').addEventListener('click', () => addScene());
form.addEventListener('submit', async (event) => {
  event.preventDefault();
  formMessage.textContent = 'Generating your scenes...';
  formMessage.className = 'form-message is-loading';
  generateButton.disabled = true;
  try {
    const response = await fetch('/api/v1/projects/generate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ project_id: document.querySelector('#project-id').value.trim(), scenes: collectScenes() }) });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || 'Generation failed.');
    showResults(payload);
    formMessage.textContent = 'Project generated successfully.';
    formMessage.className = 'form-message is-success';
  } catch (error) {
    formMessage.textContent = error.message;
    formMessage.className = 'form-message is-error';
  } finally { generateButton.disabled = false; }
});

addScene({ narration: 'Solar energy comes from sunlight.', visual_prompt: 'Solar panels receiving morning sunlight on a modern rooftop.', voice: 'female' });