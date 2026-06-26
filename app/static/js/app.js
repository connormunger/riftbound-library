// Global State
let globalInventory = [];
let currentUser = null;

// Initial Load
document.addEventListener('DOMContentLoaded', () => {
  // 1. Check who is logged in via Google OAuth
  fetch('/api/me')
    .then(res => res.json())
    .then(session => {
      const btn = document.getElementById('login-btn');
      const sidebar = document.getElementById('sidebar');

      if (session.logged_in) {
        // User is logged in and authorized in the DB
        currentUser = session.name;
        document.getElementById('user-name').textContent = session.name;
        sidebar.classList.remove('hidden');
        
        btn.textContent = "Logout";
        btn.onclick = () => window.location.href = '/auth/logout';
        btn.style.borderColor = "var(--accent)";
        btn.style.color = "var(--accent)";
      } else {
        // Not logged in (or unauthorized email)
        sidebar.classList.add('hidden');
        btn.textContent = "Log in with Google";
        btn.onclick = () => window.location.href = '/auth/login';
        btn.style.borderColor = "var(--border)";
        btn.style.color = "var(--text-muted)";
      }
    })
    .catch(err => console.error("Auth check failed", err));

  // 2. Load the inventory database
  fetch('/api/inventory')
    .then(res => res.json())
    .then(data => {
      globalInventory = data;
      
      // Call functions from the other files to build the UI
      if (typeof populateSetDropdown === 'function') populateSetDropdown(data);
      if (typeof filterTable === 'function') filterTable(); 
      if (typeof calculateStats === 'function') calculateStats();
    })
    .catch(err => {
      console.error("Inventory failed to load", err);
      const tbody = document.getElementById('inventory-tbody');
      if (tbody) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 3rem; color: var(--text-muted);">Failed to load data.</td></tr>`;
      }
    });
});

// View Management
function switchView(viewName) {
  // Update active button
  document.getElementById('nav-search').classList.remove('active');
  document.getElementById('nav-collection').classList.remove('active');
  document.getElementById('nav-' + viewName).classList.add('active');

  // Update active view
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.getElementById('view-' + viewName).classList.add('active');
}
