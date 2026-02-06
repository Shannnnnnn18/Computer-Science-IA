/* ===== LOGIN ===== */
async function login() {
    const username = document.getElementById("login-username").value.trim();
    const password = document.getElementById("login-password").value.trim();
    const errorBox = document.getElementById("login-error");

    errorBox.innerText = "";

    if (username === "" || password === "") {
        errorBox.innerText = "Please fill in all fields.";
        return;
    }

    try {
        const response = await fetch("/api/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        });

        const data = await response.json();

        if (data.status === "ok") {
            window.location.href = "/home";
        } else {
            errorBox.innerText = data.message || "Login failed.";
        }
    } catch (error) {
        errorBox.innerText = "Unable to connect to server.";
    }
}


/* ===== REGISTER ===== */
async function registerUser() {
    const username = document.getElementById("register-username").value.trim();
    const email = document.getElementById("register-email").value.trim();
    const password = document.getElementById("register-password").value.trim();
    const errorBox = document.getElementById("register-error");

    errorBox.innerText = "";

    if (username === "" || email === "" || password === "") {
        errorBox.innerText = "All fields are required.";
        return;
    }

    try {
        const response = await fetch("/api/register", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                username: username,
                email: email,
                password: password
            })
        });

        const data = await response.json();

        if (data.status === "ok") {
            window.location.href = "/";
        } else {
            errorBox.innerText = data.message || "Registration failed.";
        }
    } catch (error) {
        errorBox.innerText = "Unable to connect to server.";
    }
}


/* ===== LOGOUT ===== */
function logout() {
    fetch("/api/logout")
        .then(() => {
            window.location.href = "/";
        });
}


/* ===== TASKS ===== */
document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById("tasks-container")) {
        loadTasks();
    }
});
document.addEventListener('DOMContentLoaded', function() {
  const theme = localStorage.getItem('theme') || 'light';
  document.body.classList.add(theme + '-theme');
  document.getElementById('theme-toggle').value = theme;
});

document.addEventListener("DOMContentLoaded", () => {
  if (localStorage.getItem("theme") === "dark") {
    document.body.classList.add("dark-bg");
  }
});

function loadTasks() {
    fetch("/api/get_tasks")
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById("tasks-container");
            container.innerHTML = "";

            if (!data.tasks || data.tasks.length === 0) {
                container.innerHTML = "<p>No tasks available.</p>";
                return;
            }

            data.tasks.forEach((task, index) => {
                const card = document.createElement("div");
                card.className = "task-card";

                card.innerHTML = `
                    <strong>Task ${index + 1}: ${task.title}</strong>
                    <div class="task-notes">Notes: ${task.description || "None"}</div>
                `;

                container.appendChild(card);
            });
        });
}

function openAddTask() {
    window.location.href = "/add-task";
}

function sortTasks() {
    fetch("/api/sort_tasks")
        .then(() => loadTasks());
}

function goHome() {
    window.location.href = "/home";
}

async function loadTasks() {
  const res = await fetch('/api/tasks');
  const data = await res.json();

  const list = document.getElementById('taskList');
  list.innerHTML = '';

  data.tasks.forEach((t, i) => {
    const card = document.createElement('div');
    card.className = 'task-card';

    card.innerHTML = `
      <div class="task-title">Task ${i + 1}: ${t.title}</div>
      <div class="task-notes">Notes: ${t.description || ''}</div>
    `;

    list.appendChild(card);
  });
}

function showAddTask() {
  alert("Add Task form goes here (separate flowchart)");
}

function sortTasks() {
  alert("Sorting logic triggered");
}

window.onload = loadTasks;

async function updateProfile() {
  const newPassword = document.getElementById('newPassword').value;

  const res = await fetch('/api/update_profile', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ newPassword })
  });

  const j = await res.json();
  alert(j.message);
}
