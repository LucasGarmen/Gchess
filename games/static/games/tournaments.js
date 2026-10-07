(() => {
    'use strict';
    const visibility=document.getElementById('id_visibility');
    const passwordField=document.getElementById('tournament-password-field');
    if(visibility&&passwordField){
        const input=passwordField.querySelector('input');
        function update(){const privateMode=visibility.value==='private';passwordField.hidden=!privateMode;input.required=privateMode;input.disabled=!privateMode;}
        visibility.addEventListener('change',update);update();
    }
    const copy=document.getElementById('tournament-copy');
    if(copy)copy.addEventListener('click',async()=>{
        const field=document.getElementById('tournament-share-link');
        try{await navigator.clipboard.writeText(field.value);document.getElementById('tournament-copy-status').textContent=copy.dataset.copied;}
        catch(_){field.focus();field.select();}
    });
    document.querySelectorAll('[data-confirm]').forEach(button=>button.addEventListener('click',event=>{if(!window.confirm(button.dataset.confirm))event.preventDefault();}));
    const live=document.getElementById('tournament-live');
    const snapshot=document.getElementById('tournament-snapshot');
    if(!live||!snapshot)return;
    const baseline=JSON.stringify(JSON.parse(snapshot.textContent));
    let loading=false;
    async function refresh(){
        if(loading||document.hidden)return;
        loading=true;
        try{
            const response=await fetch(live.dataset.stateUrl,{cache:'no-store',headers:{Accept:'application/json'}});
            if(response.redirected||response.status===401||response.status===403){clearInterval(timer);return;}
            if(!response.ok)return;
            const data=await response.json();
            if(JSON.stringify(data.revision)!==baseline)location.reload();
        }catch(_){}finally{loading=false;}
    }
    const timer=setInterval(refresh,12000);
    window.addEventListener('focus',refresh);
    document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh();});
})();
