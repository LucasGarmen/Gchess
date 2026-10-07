(() => {
 'use strict';
 const node=document.getElementById('daily-training-state');if(!node)return;
 let state=JSON.parse(node.textContent);const texts=JSON.parse(document.getElementById('daily-training-texts').textContent);
 const app=document.getElementById('daily-training-app'),board=document.getElementById('daily-training-board');
 const get=id=>document.getElementById('daily-training-'+id);
 let selected=null,busy=false,waiting=false;
 const types={p:'pawn',n:'horse',b:'bishop',r:'rook',q:'queen',k:'king'};
 const csrf=()=>document.cookie.split(';').map(x=>x.trim()).find(x=>x.startsWith('csrftoken='))?.slice(10)||'';
 function draw(fen,highlight=''){
  const placement=fen.split(' ')[0].split('/');const pieces={};
  placement.forEach((row,i)=>{let col=0;for(const char of row){if(/\d/.test(char))col+=Number(char);else{pieces['abcdefgh'[col]+(8-i)]=char;col++;}}});
  board.replaceChildren();const black=state.task?.fen.split(' ')[1]==='b';
  for(let y=0;y<8;y++)for(let x=0;x<8;x++){
   const file=black?7-x:x,rank=black?y+1:8-y,square='abcdefgh'[file]+rank,piece=pieces[square];
   const button=document.createElement('button');button.type='button';button.className='daily-training-square'+((file+rank)%2===1?' dark':'');
   if(square===selected)button.classList.add('selected');
   if(selected&&state.task.legal_moves.some(move=>move.slice(0,2)===selected&&move.slice(2,4)===square))button.classList.add('target');
   if(highlight.slice(0,2)===square||highlight.slice(2,4)===square)button.classList.add('last');
   button.disabled=busy||waiting;button.setAttribute('aria-label',square+(piece?' '+texts.piece_names[piece.toLowerCase()]+' '+(piece===piece.toUpperCase()?texts.white:texts.black):''));
   if(piece){const img=document.createElement('img');img.src=app.dataset.pieces+types[piece.toLowerCase()]+'_'+(piece===piece.toUpperCase()?'white':'black')+'.png?v=2';img.alt='';button.append(img);}
   if(x===0){const label=document.createElement('small');label.className='rank';label.textContent=rank;button.append(label);}
   if(y===7){const label=document.createElement('small');label.textContent='abcdefgh'[file];button.append(label);}
   button.addEventListener('click',()=>choose(square));board.append(button);
  }
 }
 function render(){
  get('week-count').textContent=state.recent_count;
  selected=null;waiting=false;get('promotion').hidden=true;get('feedback').textContent='';get('next').hidden=true;
  get('play').hidden=state.completed;get('finish').hidden=!state.completed;
  if(state.completed){get('summary').textContent=texts.summary.replace('{total}',state.total);get('independent').textContent=state.independent;get('helped').textContent=state.helped;return;}
  get('counter').textContent=(state.index+1)+' / '+state.total+' · '+state.date;
  get('progress').max=state.total;get('progress').value=state.index;
  get('origin').textContent=state.task.personal?texts.personal+' · '+state.task.phase:texts.fallback;
  get('goal').textContent=state.task.personal?texts.goal:texts.goal_mate;get('turn').textContent=state.task.turn;
  get('source').hidden=!state.task.source_url;if(state.task.source_url)get('source').href=state.task.source_url;
  get('hint').disabled=false;get('reveal').disabled=false;draw(state.task.fen);
 }
 function choose(square){
  if(busy||waiting)return;
  const moves=selected?state.task.legal_moves.filter(move=>move.slice(0,2)===selected&&move.slice(2,4)===square):[];
  if(moves.length===1){send('try',moves[0]);return;}
  if(moves.length>1){const choices=get('promotion').querySelector('div');choices.replaceChildren();
   for(const move of moves){const button=document.createElement('button');button.type='button';button.textContent=texts[{q:'queen',r:'rook',b:'bishop',n:'knight'}[move[4]]];button.addEventListener('click',()=>{get('promotion').hidden=true;send('try',move);});choices.append(button);}get('promotion').hidden=false;return;}
  selected=state.task.legal_moves.some(move=>move.slice(0,2)===square)?square:null;draw(state.task.fen);
 }
 async function send(action,move){
  if(busy||waiting)return;busy=true;get('hint').disabled=true;get('reveal').disabled=true;draw(state.task.fen);
  try{
   const response=await fetch(app.dataset.answerUrl,{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':csrf()},body:JSON.stringify({id:state.id,index:state.index,action,move})});
   if(response.redirected)throw new Error('auth');
   const data=await response.json();
   if(response.status===409&&data.state){state=data.state;busy=false;render();return;}
   if(!response.ok)throw new Error('save');
   get('feedback').textContent=data.feedback;busy=false;
   if(data.resolved){waiting=true;draw(data.result_fen,data.result_move);state=data.state;get('next').hidden=false;get('next').textContent=state.completed?texts.finish+' →':texts.next+' →';}
   else{get('hint').disabled=false;get('reveal').disabled=false;draw(state.task.fen);}
  }catch(error){busy=false;get('feedback').textContent=texts.connection;get('hint').disabled=false;get('reveal').disabled=false;draw(state.task.fen);}
 }
 get('hint').addEventListener('click',()=>send('hint'));get('reveal').addEventListener('click',()=>send('reveal'));
 get('next').addEventListener('click',()=>{render();get(state.completed?'finish':'turn').scrollIntoView({block:'start',behavior:'smooth'});});
 render();
})();
