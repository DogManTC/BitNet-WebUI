let currentConv = null;

async function loadModels() {
  const res = await fetch('/models');
  const data = await res.json();
  const select = document.getElementById('model-select');
  select.innerHTML = '';
  data.models.forEach(m => {
    const opt = document.createElement('option');
    opt.value = m;
    opt.textContent = m;
    select.appendChild(opt);
  });
}

async function applySettings() {
  const model = document.getElementById('model-select').value;
  const temperature = parseFloat(document.getElementById('temperature').value);
  const n_predict = parseInt(document.getElementById('n-predict').value, 10);
  await fetch('/settings', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({model, temperature, n_predict})
  });
}

async function loadConversations() {
  const res = await fetch('/conversations');
  const data = await res.json();
  const list = document.getElementById('conv-list');
  list.innerHTML = '';
  data.conversations.forEach(c => {
    const li = document.createElement('li');
    li.textContent = c.title;
    li.dataset.id = c.id;
    if (c.id === currentConv) li.classList.add('active');
    li.onclick = () => selectConversation(c.id);
    list.appendChild(li);
  });
}

async function newConversation() {
  const res = await fetch('/conversations', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({})});
  const data = await res.json();
  currentConv = data.id;
  await loadConversations();
  await loadMessages();
}

async function selectConversation(id) {
  currentConv = id;
  await loadConversations();
  await loadMessages();
}

async function loadMessages() {
  if (!currentConv) return;
  const res = await fetch(`/conversations/${currentConv}`);
  const data = await res.json();
  const chat = document.getElementById('chat');
  chat.innerHTML = '';
  data.messages.forEach(m => {
    const div = document.createElement('div');
    div.className = `message ${m.role}`;
    div.textContent = m.content;
    chat.appendChild(div);
  });
  chat.scrollTop = chat.scrollHeight;
}

async function sendMessage(text) {
  if (!currentConv) await newConversation();
  const chat = document.getElementById('chat');
  const userDiv = document.createElement('div');
  userDiv.className = 'message user';
  userDiv.textContent = text;
  chat.appendChild(userDiv);
  const assistDiv = document.createElement('div');
  assistDiv.className = 'message assistant';
  chat.appendChild(assistDiv);
  chat.scrollTop = chat.scrollHeight;

  const resp = await fetch(`/conversations/${currentConv}/messages`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({content: text, stream: true})
  });
  const reader = resp.body.getReader();
  const decoder = new TextDecoder('utf-8');
  while (true) {
    const {value, done} = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value);
    const parts = chunk.split('\n\n');
    for (const part of parts) {
      if (part.startsWith('data:')) {
        const dataStr = part.slice(5).trim();
        if (dataStr === '[DONE]') break;
        try {
          const data = JSON.parse(dataStr);
          const token = data.choices[0].delta?.content || '';
          assistDiv.textContent += token;
          chat.scrollTop = chat.scrollHeight;
        } catch (e) {}
      }
    }
  }
  await loadConversations();
}

document.getElementById('chat-form').addEventListener('submit', async e => {
  e.preventDefault();
  const input = document.getElementById('message');
  const text = input.value.trim();
  if (!text) return;
  input.value = '';
  await sendMessage(text);
});

document.getElementById('apply').onclick = applySettings;
document.getElementById('new-conv').onclick = newConversation;

loadModels();
loadConversations();
