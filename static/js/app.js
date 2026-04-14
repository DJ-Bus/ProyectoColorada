/* ═══════════════════════════════════════════════════════════════
   ERP La Colorada — App JavaScript
   ═══════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {

    // ── Sidebar toggle (mobile) ──────────────────────────────────
    const hamburger = document.getElementById('hamburger');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    function openSidebar() {
        if (sidebar) sidebar.classList.add('open');
        if (overlay) overlay.classList.add('open');
        document.body.style.overflow = 'hidden';
    }

    function closeSidebar() {
        if (sidebar) sidebar.classList.remove('open');
        if (overlay) overlay.classList.remove('open');
        document.body.style.overflow = '';
    }

    if (hamburger) hamburger.addEventListener('click', openSidebar);
    if (overlay) overlay.addEventListener('click', closeSidebar);

    // Close sidebar on ESC key
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') closeSidebar();
    });


    // ── Auto-dismiss alerts ──────────────────────────────────────
    const alerts = document.querySelectorAll('.alert[data-auto-dismiss]');
    alerts.forEach(function (alert) {
        const delay = parseInt(alert.dataset.autoDismiss) || 5000;
        setTimeout(function () {
            alert.style.transition = 'opacity 300ms, transform 300ms';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(function () { alert.remove(); }, 300);
        }, delay);
    });

    // Manual dismiss
    document.querySelectorAll('.alert-close').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const alert = this.closest('.alert');
            if (alert) {
                alert.style.transition = 'opacity 200ms';
                alert.style.opacity = '0';
                setTimeout(function () { alert.remove(); }, 200);
            }
        });
    });


    // ── Number input formatting ──────────────────────────────────
    // Auto-select content on focus for number/decimal inputs
    document.querySelectorAll('input[inputmode="decimal"], input[type="number"]').forEach(function (input) {
        input.addEventListener('focus', function () {
            this.select();
        });
    });


    // ── Active sidebar link highlighting ─────────────────────────
    const currentPath = window.location.pathname;
    document.querySelectorAll('.sidebar-link').forEach(function (link) {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

});
