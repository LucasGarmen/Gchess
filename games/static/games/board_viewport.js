(() => {
    let frame;
    const fit = () => {
        const layout = document.querySelector('.home-computer-layout');
        if (!layout || !document.body.classList.contains('mobile-bot-playing')) return;
        const area = layout.querySelector('.board-area');
        const wrapper = area?.querySelector('.board-wrapper');
        const board = wrapper?.querySelector('#board');
        const captures = area?.querySelector('#captured-material');
        if (!board || !captures) return;
        const mobile = innerWidth <= 900;
        const b = board.getBoundingClientRect();
        const w = wrapper.getBoundingClientRect();
        const a = area.getBoundingClientRect();
        const dock = document.querySelector('.coach-chat-dock');
        const dockReserve = mobile && dock && !dock.hidden ? dock.getBoundingClientRect().height + 12 : 8;
        const chrome = Math.max(0, w.height - b.height) + Math.max(0, w.top - a.top);
        const height = innerHeight - a.top - chrome - captures.getBoundingClientRect().height - dockReserve - 8;
        const padding = getComputedStyle(wrapper);
        const width = area.clientWidth - parseFloat(padding.paddingLeft) - parseFloat(padding.paddingRight) - 24;
        const size = Math.floor(Math.max(120, Math.min(width, height)));
        if (mobile) {
            layout.style.setProperty('--mobile-board-size', size + 'px', 'important');
            layout.style.setProperty('--mobile-square-size', size / 8 + 'px', 'important');
        } else layout.style.setProperty('--square-size', size / 8 + 'px', 'important');
    };
    const schedule = () => { cancelAnimationFrame(frame); frame = requestAnimationFrame(fit); };
    document.addEventListener('DOMContentLoaded', () => {
        schedule();
        new MutationObserver(schedule).observe(document.body, {attributes:true, attributeFilter:['class']});
    });
    addEventListener('resize', schedule);
    addEventListener('load', schedule);
    window.visualViewport?.addEventListener('resize', schedule);
})();
