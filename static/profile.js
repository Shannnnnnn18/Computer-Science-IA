// Load theme preference on page load
document.addEventListener("DOMContentLoaded", () => {
  const theme = localStorage.getItem("theme");
  const body = document.getElementById("profileBody");
  const toggle = document.getElementById("themeSwitch");

  if (theme === "dark") {
    body.classList.add("dark-bg");
    toggle.checked = true;
  }
});

// Save profile settings
function saveProfile() {
  const toggle = document.getElementById("themeSwitch");
  const body = document.getElementById("profileBody");

  if (toggle.checked) {
    body.classList.add("dark-bg");
    localStorage.setItem("theme", "dark");
  } else {
    body.classList.remove("dark-bg");
    localStorage.setItem("theme", "light");
  }

  alert("Profile settings saved");
}
