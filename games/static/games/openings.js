(() => {
'use strict';
const app=document.getElementById('opening-app');if(!app)return;
const lesson=JSON.parse(document.getElementById('opening-lesson').textContent),texts=JSON.parse(document.getElementById('opening-texts').textContent);
let state=JSON.parse(document.getElementById('opening-state').textContent),selected=null,busy=false;
const get=id=>document.getElementById('opening-'+id),mode=app.dataset.mode,names={p:'pawn',n:'horse',b:'bishop',r:'rook',q:'queen',k:'king'};
function draw(){
 const cells=[];for(const row of state.fen.split(' ')[0].split('/'))for(const c of row){if(/\d/.test(c))for(let i=0;i<Number(c);i++)cells.push(null);else cells.push(c);}
 const board=get('board');board.replaceChildren();let indices=Array.from({length:64},(_,i)=>i);if(lesson.color==='black')indices.reverse();
 for(const i of indices){const square='abcdefgh'[i%8]+(8-Math.floor(i/8)),piece=cells[i],button=document.createElement('button');button.type='button';button.className='daily-training-square'+((Math.floor(i/8)+i%8)%2?' dark':'')+(selected===square?' selected':'');button.dataset.square=square;button.setAttribute('aria-label',square+(piece?' '+names[piece.toLowerCase()]+' '+texts[piece===piece.toUpperCase()?'white':'black']:''));button.disabled=busy||mode==='learn'||state.finished;
 if(piece){const img=document.createElement('img');img.alt='';img.src=app.dataset.pieces+names[piece.toLowerCase()]+'_'+(piece===piece.toUpperCase()?'white':'black')+'.svg';button.append(img);}button.addEventListener('click',()=>choose(square));board.append(button);}
}
function render(){selected=null;draw();get('progress').max=lesson.moves.length;get('progress').value=state.index;get('counter').textContent=state.index+' / '+lesson.moves.length;
 get('next').hidden=mode!=='learn'||state.finished;get('hint').hidden=mode!=='practice'||state.finished;
 get('explanation').textContent=state.finished?texts.done:mode==='learn'?texts.move+' '+(state.index+1)+': '+lesson.moves[state.index].san+' — '+lesson.moves[state.index].explanation:texts.select;
 get('feedback').textContent=state.feedback||'';get('next').disabled=busy;get('hint').disabled=busy;
}
function choose(square){if(busy||state.finished)return;if(selected&&state.legal.includes(selected+square)){send(selected+square);return;}selected=state.legal.some(m=>m.slice(0,2)===square)?square:null;draw();}
async function send(move){if(busy||state.finished)return;busy=true;render();const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),15000);try{const response=await fetch(app.dataset.endpoint,{method:'POST',signal:controller.signal,headers:{'Content-Type':'application/json','X-CSRFToken':document.querySelector('[name=csrfmiddlewaretoken]')?.value||decodeURIComponent(document.cookie.split('; ').find(c=>c.startsWith('csrftoken='))?.split('=')[1]||'')},body:JSON.stringify({index:state.index,mode,move})});if(!response.ok||response.redirected)throw Error();const data=await response.json();state=data;}catch(_){state.feedback=texts.network;}finally{clearTimeout(timer);busy=false;render();}}
get('next').addEventListener('click',()=>send());get('hint').addEventListener('click',()=>{if(busy||state.finished)return;const move=lesson.moves[state.index];get('explanation').textContent=texts.move+': '+move.san+' — '+move.explanation;for(const square of [move.uci.slice(0,2),move.uci.slice(2,4)])get('board').querySelector('[data-square="'+square+'"]').classList.add('hint');});
get('restart').addEventListener('click',()=>{if(busy)return;state=JSON.parse(document.getElementById('opening-state').textContent);render();});render();
})();