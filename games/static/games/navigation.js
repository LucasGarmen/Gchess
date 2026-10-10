(() => {
    'use strict';
    const nav = document.getElementById('site-nav');
    if (!nav) return;
    const groups = [...nav.querySelectorAll('.nav-group')];
    const hover = () => matchMedia('(hover: hover) and (pointer: fine)').matches;
    const desktopSidebar = () => matchMedia('(min-width: 1101px)').matches;
    let closeTimer;
    function position(group) {
        const menu = group.querySelector('.nav-submenu');
        const rect = group.getBoundingClientRect();
        const side = desktopSidebar();
        const width = Math.min(224, innerWidth - 24);
        menu.style.width = width + 'px';
        const height = menu.getBoundingClientRect().height;
        let left = side ? nav.getBoundingClientRect().right - 1 : rect.left;
        let top = side ? rect.top : rect.bottom;
        left = Math.max(12, Math.min(left, innerWidth - width - 12));
        top = Math.max(8, Math.min(top, innerHeight - height - 8));
        menu.style.left = left + 'px';
        menu.style.top = top + 'px';
    }
    function close(group) {
        group.dataset.open = 'false';
        group.querySelector('.nav-submenu').hidden = true;
        group.querySelector('.nav-disclosure').setAttribute('aria-expanded', 'false');
        group.querySelector('.nav-main-row .nav-link')?.setAttribute('aria-expanded', 'false');
    }
    function open(group) {
        clearTimeout(closeTimer);
        groups.forEach(other => { if (other !== group) close(other); });
        group.dataset.open = 'true';
        group.querySelector('.nav-submenu').hidden = false;
        group.querySelector('.nav-disclosure').setAttribute('aria-expanded', 'true');
        group.querySelector('.nav-main-row .nav-link')?.setAttribute('aria-expanded', 'true');
        position(group);
    }
    groups.forEach(group => {
        const button = group.querySelector('.nav-disclosure');
        const heading = group.querySelector('.nav-main-row .nav-link');
        if (heading) {
            heading.setAttribute('aria-controls', button.getAttribute('aria-controls'));
            heading.setAttribute('aria-expanded', 'false');
            heading.addEventListener('click', event => {
                if (innerWidth > 900 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
                event.preventDefault();
                group.dataset.open === 'true' ? close(group) : open(group);
            });
        }
        button.addEventListener('click', () => group.dataset.open === 'true' ? close(group) : open(group));
        group.addEventListener('pointerenter', event => { if (innerWidth > 900 && (event.pointerType === 'mouse' || hover())) open(group); });
        group.addEventListener('pointerleave', event => { if (innerWidth > 900 && (event.pointerType === 'mouse' || hover())) closeTimer = setTimeout(() => close(group), 180); });
        group.addEventListener('focusin', event => { if (innerWidth > 900 && event.target !== button) open(group); });
        group.addEventListener('focusout', event => { if (!group.contains(event.relatedTarget)) close(group); });
        group.addEventListener('keydown', event => {
            if (event.key === 'Escape') { event.preventDefault(); close(group); button.focus(); }
            if (event.key === 'ArrowRight' && event.target === group.querySelector('.nav-link')) { event.preventDefault(); open(group); group.querySelector('.nav-submenu a').focus(); }
        });
    });
    document.addEventListener('click', event => { if (!event.target.closest('.nav-group')) groups.forEach(close); });
    window.addEventListener('resize', () => groups.forEach(close));
    window.addEventListener('scroll', () => groups.forEach(group => { if (group.dataset.open === 'true') position(group); }), {passive:true});
})();
