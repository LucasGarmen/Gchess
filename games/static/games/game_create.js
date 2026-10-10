(() => {
    'use strict';
    const form=document.getElementById('create-game-form');
    if (!form) return;
    const time=form.querySelector('input[name="time_control_minutes"]');
    const presets=form.querySelectorAll('[data-minutes]');
    function update() {
        const chosen=field=>form.querySelector(`input[name="${field}"]:checked`);
        const opponent=chosen('opponent_mode');
        document.getElementById('opponent-name-field').hidden=opponent?.value!=='choose';
        presets.forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.minutes===time.value)));
    }
    presets.forEach(button=>button.addEventListener('click',()=>{time.value=button.dataset.minutes;update();}));
    form.addEventListener('change',update);form.addEventListener('input',update);
    update();
})();
