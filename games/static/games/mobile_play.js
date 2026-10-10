document.addEventListener('DOMContentLoaded', () => {
    const chat = document.querySelector('.home-computer-layout .trainer-chat');
    if (!chat) return;
    const disclosure = document.createElement('details');
    disclosure.className = 'mobile-coach-chat';
    const summary = document.createElement('summary');
    summary.textContent = chat.querySelector('h2')?.textContent || 'Coach';
    chat.before(disclosure);
    disclosure.append(summary, chat);
    const mobile = window.matchMedia('(max-width: 900px)');
    const sync = () => { disclosure.open = !mobile.matches; };
    sync();
    mobile.addEventListener('change', sync);
});
