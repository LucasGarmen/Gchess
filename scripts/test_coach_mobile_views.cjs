const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const classes=new Set(['mobile-bot-playing']);let observer,mediaChange,focusChanged,focused=0,blurred=0;
const styles={};const media={matches:true,addEventListener(type,fn){mediaChange=fn}};
function element(){return{children:[],attrs:{},focus(){},append(child){child.parentElement=this;this.children.push(child)},setAttribute(k,v){this.attrs[k]=v},addEventListener(type,fn){this[type]=fn}}}
const body=element();body.classList={contains:n=>classes.has(n),toggle(n,on){on?classes.add(n):classes.delete(n)}};
const history={open:false},dock={querySelector:()=>history};const input={focus(){focused++},blur(){blurred++},value:'Draft'};
let overlay=null;const root={style:{setProperty(k,v){styles[k]=v}}};
const document={body,documentElement:{lang:'es',style:root.style},querySelector(s){return s==='.coach-chat-dock'?dock:s==='.home-computer-layout'?{}:s==='.focus-play'?overlay:null},getElementById:()=>input,createElement:element,addEventListener(type,fn){if(type==='DOMContentLoaded')fn();else if(type==='gchess:focus-mode-changed')focusChanged=fn}};
const ctx={document,matchMedia:()=>media,innerHeight:800,window:{visualViewport:{height:800,offsetTop:0,addEventListener(){}},addEventListener(){}},MutationObserver:class{constructor(fn){observer=fn}observe(){}}};
vm.runInNewContext(fs.readFileSync('games/static/games/coach_mobile_views.js','utf8'),ctx);
const nav=body.children[0],buttons=nav.children;assert.equal(nav.hidden,false);assert.ok(classes.has('coach-mobile-views-active'));
buttons[1].click();assert.ok(classes.has('coach-chat-view'));assert.equal(history.open,true);assert.equal(focused,1);assert.equal(buttons[1].attrs['aria-pressed'],'true');
buttons[0].click();assert.ok(!classes.has('coach-chat-view'));assert.equal(blurred,1);assert.equal(input.value,'Draft');
ctx.window.visualViewport.height=450;observer();assert.equal(styles['--coach-keyboard-inset'],'350px');
overlay=element();focusChanged();assert.equal(nav.parentElement,overlay,'Controls must join the native fullscreen subtree');
media.matches=false;mediaChange();assert.equal(nav.hidden,true);assert.ok(!classes.has('coach-mobile-views-active'));assert.ok(!classes.has('coach-chat-view'));
console.log('Mobile coach views: switching, focus, draft, viewport inset, fullscreen and desktop cleanup passed.');
