(function () {
    'use strict';
    var key='gchess-sound-enabled',enabled=true,audios=new Set(),sources=new Set();
    try {enabled=localStorage.getItem(key)!=='false';} catch (_) {}
    function stop() {
        audios.forEach(function(audio){audio.pause();});audios.clear();
        sources.forEach(function(source){try{source.stop();}catch(_) {}});sources.clear();
    }
    function render() {
        var lang=document.documentElement.lang.split('-')[0];
        var labels={es:['Activar sonido','Silenciar sonido'],pt:['Ativar som','Silenciar som'],en:['Turn sound on','Mute sound']};
        var label=(labels[lang]||labels.en)[enabled?1:0];
        document.querySelectorAll('[data-sound-toggle]').forEach(function(button){
            button.setAttribute('aria-pressed',String(enabled));button.setAttribute('aria-label',label);button.title=label;
            button.classList.toggle('sound-muted',!enabled);
        });
    }
    window.GchessSound={
        isEnabled:function(){return enabled;},
        trackAudio:function(audio){audios.add(audio);audio.addEventListener('ended',function(){audios.delete(audio);},{once:true});},
        trackBuffer:function(source){sources.add(source);source.addEventListener('ended',function(){sources.delete(source);},{once:true});}
    };
    document.addEventListener('click',function(event){
        if(!event.target.closest('[data-sound-toggle]'))return;
        enabled=!enabled;if(!enabled)stop();
        try{localStorage.setItem(key,String(enabled));}catch(_) {}
        render();
    });
    window.addEventListener('storage',function(event){if(event.key!==key && event.key!==null)return;enabled=event.newValue!=='false';if(!enabled)stop();render();});
    document.addEventListener('DOMContentLoaded',function(){
        var original=document.querySelector('[data-sound-toggle]'),toolbar=document.querySelector('.board-toolbar');
        if(original && toolbar){var copy=original.cloneNode(true);copy.removeAttribute('id');toolbar.appendChild(copy);}
        render();
    });
})();
