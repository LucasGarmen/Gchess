(function () {
    'use strict';
    var key='gchess-sound-enabled',enabled=true,audios=new Set(),sources=new Set(),volume=.5;
    try {var saved=localStorage.getItem('gchess-sound-volume');if(saved!==null && Number.isFinite(Number(saved)))volume=Math.max(0,Math.min(1,Number(saved)));}catch(_){}
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
        trackAudio:function(audio){audio.dataset.baseVolume=String(audio.volume);audio.volume=audio.volume*volume;audios.add(audio);audio.addEventListener('ended',function(){audios.delete(audio);},{once:true});},
        trackBuffer:function(source,gain){if(gain)gain.gain.value*=volume;sources.add(source);source.addEventListener('ended',function(){sources.delete(source);},{once:true});}
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
        document.querySelectorAll('[data-sound-toggle]').forEach(function(button){
            var slider=document.createElement('input');slider.type='range';slider.min='0';slider.max='100';slider.value=String(volume*100);slider.className='sound-volume';
            var lang=document.documentElement.lang.split('-')[0];slider.setAttribute('aria-label',lang==='es'?'Volumen':lang==='pt'?'Volume':'Volume');
            slider.addEventListener('input',function(){volume=Number(slider.value)/100;try{localStorage.setItem('gchess-sound-volume',String(volume));}catch(_){}document.querySelectorAll('.sound-volume').forEach(function(other){other.value=slider.value;});audios.forEach(function(audio){audio.volume=Number(audio.dataset.baseVolume||1)*volume;});});
            button.after(slider);
        });
        render();
    });
})();
