document.addEventListener('DOMContentLoaded', async () => {
  const container = document.getElementById('products');
  container.innerHTML = '<p>Loading products...</p>';
  try {
    const backend = (window.BACKEND_URL || '') || '/api/v1';
    const res = await fetch(backend + '/products').catch(e => { throw e });
    if (!res.ok) throw new Error('Fetch failed: ' + res.status);
    const products = await res.json();
    if (!Array.isArray(products) || products.length === 0) {
      container.innerHTML = '<p>No products yet. Run seed script.</p>';
      return;
    }
    container.innerHTML = '<ul>' + products.map(p =>
      `<li><strong>${p.name}</strong> — $${p.price} <br><em>${p.category}</em></li>`
    ).join('') + '</ul>';
  } catch (e) {
    container.innerHTML = '<p>Error loading products: ' + e.message + '</p>';
  }
});
