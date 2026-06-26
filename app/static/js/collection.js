function calculateStats() {
  let totalCards = 0;
  let totalValue = 0.0;
  
  globalInventory.forEach(card => {
    if (card.owner_name === simulatedUser) {
      totalCards += (card.quantity || 0);
      if (card.price) {
        totalValue += (parseFloat(card.price) * (card.quantity || 0));
      }
    }
  });

  document.getElementById('stat-cards').textContent = totalCards;
  document.getElementById('stat-value').textContent = `$${totalValue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
}
