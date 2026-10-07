(() => {
    'use strict';
    const form=document.getElementById('create-game-form');
    if (!form) return;
    const words=JSON.parse(document.getElementById('create-game-texts').textContent);
    const time=form.querySelector('input[name="time_control_minutes"]');
    const name=form.querySelector('input[name="opponent_name"]');
    const presets=form.querySelectorAll('[data-minutes]');
    function update() {
        const chosen=field=>form.querySelector(`input[name="${field}"]:checked`);
        const label=input=>input?.closest('label').querySelector('strong')?.textContent || '—';
        const opponent=chosen('opponent_mode');
        document.getElementById('opponent-name-field').hidden=opponent?.value!=='choose';
        document.getElementById('create-summary-opponent').textContent=label(opponent)+(opponent?.value==='choose' && name.value.trim() ? ' · '+name.value.trim() : '');
        document.getElementById('create-summary-type').textContent=label(chosen('game_type'));
        document.getElementById('create-summary-color').textContent=label(chosen('color_choice'));
        document.getElementById('create-summary-time').textContent=time.value ? time.value+' '+words.minutes : words.no_clock;
        presets.forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.minutes===time.value)));
    }
    presets.forEach(button=>button.addEventListener('click',()=>{time.value=button.dataset.minutes;update();}));
    form.addEventListener('change',update);form.addEventListener('input',update);
    update();
})();
