function updateCartCount() {
    fetch('/api/cart/count')
        .then(r => r.json())
        .then(data => {
            const cartCountEl = document.getElementById('cartCount');
            if (cartCountEl && data.count !== undefined) {
                cartCountEl.textContent = data.count;
                cartCountEl.style.display = data.count > 0 ? 'block' : 'none';
            }
        })
        .catch(e => console.error('Error fetching cart count:', e));
}

document.addEventListener('DOMContentLoaded', function() {
    updateCartCount();

    // Active nav-link
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
});

if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register("/static/service-worker.js")
            .then(registration => {
                console.log('ServiceWorker registration successful with scope: ', registration.scope);
            })
            .catch(error => {
                console.log('ServiceWorker registration failed: ', error);
            });
    });
}
