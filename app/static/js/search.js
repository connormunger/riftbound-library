function populateSetDropdown(data) {
  const uniqueSets = [...new Set(data.map(card => card.set_code))].filter(Boolean).sort();
  const selectEl = document.getElementById('set-filter');
  
  uniqueSets.forEach(set => {
    const option = document.createElement('option');
    option.value = set;
    option.textContent = set;
    selectEl.appendChild(option);
  });
}

function filterTable() {
  const query = document.getElementById('search-input').value.toLowerCase();
  const selectedSet = document.getElementById('set-filter').value;
  const tbody = document.getElementById('inventory-tbody');
  
  const filtered = globalInventory.filter(card => {
    const matchesQuery = (card.card_name || '').toLowerCase().includes(query) || 
                         (card.owner_name || '').toLowerCase().includes(query);
    const matchesSet = (selectedSet === 'ALL') || (card.set_code === selectedSet);
    return matchesQuery && matchesSet;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 3rem; color: var(--text-muted);">No cards found matching your filters.</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map(row => {
    let tagsHtml = '';
    if (row.is_holo) tagsHtml += `<span class="tag holo">Foil</span>`;
    if (row.is_promo) tagsHtml += `<span class="tag holo" style="color:#e05252; border-color: rgba(224,82,82,0.3); background: rgba(224,82,82,0.1);">Promo</span>`;
    
    let ownerCls = row.owner_name === 'Library' ? 'tag owner owner-library' : 'tag owner';
    let priceText = row.price ? `$${parseFloat(row.price).toFixed(2)}` : '—';

	return `
      	  <tr>
            <td>
              <div class="col-card">${escapeHtml(row.card_name)}</div>
              <div class="col-set" style="margin-top: 4px;">${escapeHtml(row.set_code)} · ${escapeHtml(row.collector_number)}</div>
            </td>
            <td style="white-space: nowrap;">${tagsHtml || '<span style="color:var(--text-muted)">—</span>'}</td>
            <td><span class="${ownerCls}">${escapeHtml(row.owner_name)}</span></td>
            <td style="font-family:monospace; text-align:center;">${row.quantity}</td>
            <td class="col-price">${priceText}</td>
          </tr>
    	`;
  }).join('');
}

function escapeHtml(unsafe) {
  if (!unsafe) return '';
  return String(unsafe)
       .replace(/&/g, "&amp;")
       .replace(/</g, "&lt;")
       .replace(/>/g, "&gt;")
       .replace(/"/g, "&quot;")
       .replace(/'/g, "&#039;");
}
