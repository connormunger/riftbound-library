// Global State
let globalInventory = [];
let isDevLoggedIn = false;
let simulatedUser = "Connor";

// Initial Load
document.addEventListener('DOMContentLoaded', () => {
  fetch('/api/inventory')
    .then(res => res.json())
    .then(data => {
      globalInventory = data;
      populateSetDropdown(data);
      filterTable(); 
      calculateStats();
    })
    .catch(err => {
      console.error(err);
      document.getElementById('inventory-tbody').innerHTML = `<tr><td colspan="6" style="text-align:center;">Failed to load data.</td></tr>`;
    });
});

// View Management
function switchView(viewName) {
  document.getElementById('nav-search').classList.remove('active');
  document.getElementById('nav-collection').classList.remove('active');
  document.getElementById('nav-' + viewName).classList.add('active');

  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.getElementById('view-' + viewName).classList.add('active');
}

// Dev Authentication Simulator
function toggleDevLogin() {
  isDevLoggedIn = !isDevLoggedIn;
  const sidebar = document.getElementById('sidebar');
  const btn = document.getElementById('login-btn');
  
  if (isDevLoggedIn) {
    sidebar.classList.remove('hidden');
    document.getElementById('user-name').textContent = simulatedUser;
    btn.textContent = "Dev: Logout";
    btn.style.borderColor = "var(--accent)";
    btn.style.color = "var(--accent)";
  } else {
    sidebar.classList.add('hidden');
    btn.textContent = "Dev: Simulate Login";
    btn.style.borderColor = "var(--border)";
    btn.style.color = "var(--text-muted)";
    switchView('search');
  }
}
