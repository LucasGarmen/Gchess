(() => {
    const panel = document.getElementById('mobile-bot-setup');
    const select = document.getElementById('mobile-computer-elo');
    const summary = document.getElementById('entry-level-summary');
    if (!panel || !select || !summary) return;
    const presets = Array.from(panel.querySelectorAll('[data-entry-level]'));
    function render() {
        let selected;
        presets.forEach(button => {
            const active = button.dataset.entryLevel === select.value;
            button.setAttribute('aria-pressed', String(active));
            if (active) selected = button;
        });
        summary.textContent = `${selected ? selected.textContent.trim() : summary.dataset.custom} · ${select.value}`;
    }
    presets.forEach(button => button.addEventListener('click', () => {
        select.value = button.dataset.entryLevel;
        select.dispatchEvent(new Event('change', {bubbles: true}));
    }));
    select.addEventListener('change', render);
    // Opening setup copies the current/saved game difficulty; reflect that value.
    new MutationObserver(() => { if (!panel.hidden) render(); }).observe(panel, {attributes: true, attributeFilter: ['hidden']});
    render();
})();
