document.addEventListener('DOMContentLoaded', () => {
    const contacts = [...document.querySelectorAll('.nav-contact-detail')];
    const close = (except = null) => contacts.forEach(item => { if (item !== except) item.open = false; });
    contacts.forEach(item => item.addEventListener('toggle', () => { if (item.open) close(item); }));
    document.addEventListener('click', event => { if (!event.target.closest('.nav-contact-links')) close(); });
    document.addEventListener('keydown', event => {
        if (event.key !== 'Escape') return;
        const active = contacts.find(item => item.open);
        if (active) { close(); active.querySelector('summary').focus(); }
    });
});