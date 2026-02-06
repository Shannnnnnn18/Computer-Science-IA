let taskCount = 0;

/* =========================
   PRIORITY COLOUR HANDLER
========================= */
function applyPriorityColor(card) {
  card.classList.remove('priority-low', 'priority-medium', 'priority-high');

  const priority = card.querySelector('.task-priority').value;

  if (priority === 'High') card.classList.add('priority-high');
  if (priority === 'Medium') card.classList.add('priority-medium');
  if (priority === 'Low') card.classList.add('priority-low');
}

/* =========================
   DEADLINE WARNING HANDLER
========================= */
function updateDeadlineStatus(card) {
  let warning = card.querySelector('.deadline-warning');
  if (!warning) {
    warning = document.createElement('div');
    warning.className = 'deadline-warning';
    card.appendChild(warning);
  }

  const dateInput = card.querySelector('.task-date').value;
  if (!dateInput) {
    warning.textContent = '';
    return;
  }

  const due = new Date(dateInput);
  const now = new Date();
  const diffHours = (due - now) / (1000 * 60 * 60);

  if (diffHours < 0) {
    warning.textContent = '⚠ Overdue';
    warning.style.color = 'red';
  } else if (diffHours < 24) {
    warning.textContent = '⏰ Due soon';
    warning.style.color = 'orange';
  } else {
    warning.textContent = '';
  }
}

/* =========================
   ADD TASK CARD
========================= */
function addTaskBox(taskData = {}, taskID = null) {
  taskCount++;

  const task = document.createElement('div');
  task.className = 'task-card';
  if (taskID) task.setAttribute('data-task-id', taskID);

  task.innerHTML = `
    <input class="task-title" placeholder="Task title" value="${taskData.title || ''}">

    <textarea class="task-notes" placeholder="Notes">${taskData.description || ''}</textarea>

    <div class="task-meta">
      <input type="datetime-local" class="task-date" value="${taskData.dueDate || ''}">

      <select class="task-priority">
        <option ${taskData.priority === 'Low' ? 'selected' : ''}>Low</option>
        <option ${taskData.priority === 'Medium' ? 'selected' : ''}>Medium</option>
        <option ${taskData.priority === 'High' ? 'selected' : ''}>High</option>
      </select>

      <label class="complete-label">
        <input type="checkbox" class="task-complete" ${taskData.completed ? 'checked' : ''}>
        Completed
      </label>

      <button onclick="saveTask(this)">Save</button>
      <button onclick="deleteTask(this)">Delete</button>
    </div>
  `;

  document.getElementById('taskList').appendChild(task);

  // Priority colour
  applyPriorityColor(task);
  task.querySelector('.task-priority').addEventListener('change', () => {
    applyPriorityColor(task);
  });

  // Deadline warning
  updateDeadlineStatus(task);
  task.querySelector('.task-date').addEventListener('change', () => {
    updateDeadlineStatus(task);
  });

  // Auto-save on completion toggle
  task.querySelector('.task-complete').addEventListener('change', () => {
    saveTask(task.querySelector('button[onclick="saveTask(this)"]'));
  });
}

/* =========================
   SAVE TASK
========================= */
async function saveTask(btn) {
  const card = btn.closest('.task-card');
  const taskID = card.getAttribute('data-task-id');

  const payload = {
    title: card.querySelector('.task-title').value,
    description: card.querySelector('.task-notes').value,
    dueDate: card.querySelector('.task-date').value,
    priority: card.querySelector('.task-priority').value,
    completed: card.querySelector('.task-complete').checked,
    tags: [],
    reminder: ''
  };

  let url, method;
  if (taskID) {
    url = '/api/edit_task';
    payload.taskID = taskID;
  } else {
    url = '/api/add_task';
  }

  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  const j = await res.json();
  if (j.status !== 'ok') {
    alert(j.message || 'Error saving task');
    return;
  }

  if (!taskID && j.taskID) {
    card.setAttribute('data-task-id', j.taskID);
  }
}

/* =========================
   DELETE TASK
========================= */
async function deleteTask(btn) {
  if (!confirm('Are you sure you want to delete this task?')) return;

  const card = btn.closest('.task-card');
  const taskID = card.getAttribute('data-task-id');

  if (taskID) {
    const res = await fetch('/api/delete_task', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ taskID })
    });

    const j = await res.json();
    if (j.status !== 'ok') {
      alert(j.message || 'Error deleting task');
      return;
    }
  }

  card.remove();
}

/* =========================
   LOAD TASKS
========================= */
async function loadTasks() {
  const res = await fetch('/api/get_tasks');
  const j = await res.json();

  document.getElementById('taskList').innerHTML = '';
  j.tasks.forEach(task => addTaskBox(task, task.id));
}

/* =========================
   SORT TASKS
========================= */
function sortTasks(sortType) {
  if (!sortType) return;
  fetch('/api/sort_tasks', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({sort_type: sortType})
  }).then(res => res.json()).then(data => {
    document.getElementById('taskList').innerHTML = '';
    data.tasks.forEach(task => addTaskBox(task, task.id));
    document.getElementById('sortSelect').value = '';
  });
}

/* =========================
   INIT
========================= */
loadTasks();
