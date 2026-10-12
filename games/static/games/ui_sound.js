(() => {
'use strict';
// One delegated listener covers dynamically inserted controls too. Hover and
// automatic updates stay silent; board moves and results have their own audio.
let lastAt = -Infinity;
document.addEventListener('click', event => {
 if (!event.isTrusted || event.defaultPrevented) return;
 const target = event.target.closest?.('button, a[href], summary, [role="button"]');
 if (!target || target.matches(':disabled, [aria-disabled="true"]') ||
     target.closest('#board, [data-sound-toggle], .sound-volume, [data-motion-toggle], [data-ui-sound="off"]')) return;
 const now = performance.now();
 if (now - lastAt < 80) return;
 lastAt = now;
 const expanded = target.getAttribute('aria-expanded');
 const kind = target.matches('summary') ? (target.parentElement.open ? 'ui_close' : 'ui_open') :
     expanded !== null ? (expanded === 'true' ? 'ui_close' : 'ui_open') : 'ui_click';
 window.GchessExperience?.interaction(kind);
}, true);
})();
