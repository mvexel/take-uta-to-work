// Test-only jsdom dependency. Pass before.html and after.html fixtures as arguments.
const {JSDOM}=require('jsdom');const fs=require('node:fs');const assert=require('node:assert/strict');
const dom=new JSDOM(fs.readFileSync(process.argv[2],'utf8'),{url:'http://127.0.0.1:8765/',runScripts:'outside-only',pretendToBeVisual:true});
const w=dom.window;let hidden=false,calls=0,fail=false;const timers=new Map();let seq=0;
Object.defineProperty(w.document,'hidden',{get:()=>hidden});
w.setTimeout=(fn,ms)=>{timers.set(++seq,{fn,ms});return seq};w.clearTimeout=id=>timers.delete(id);
w.scrollTo=({left,top})=>{w.scrollX=left;w.scrollY=top};w.scrollY=450;
w.fetch=async()=>{calls++;if(fail)throw Error('offline');return{ok:true,text:async()=>fs.readFileSync(process.argv[3],'utf8')}};
w.eval(fs.readFileSync(require('node:path').join(__dirname,'refresh.js'),'utf8'));
(async()=>{
const card=w.document.querySelector('#card-bike'),detail=card.querySelector('details'),focus=detail.querySelector('summary');detail.open=true;focus.focus();
let tick=[...timers.values()].find(t=>t.ms===15000);assert.ok(tick);await tick.fn();
assert.match(card.textContent,/Verified refresh fixture update/);assert.equal(card.parentElement.id,'planned');assert.equal(detail.open,true);assert.equal(w.document.activeElement,focus);assert.equal(w.scrollY,450);assert.match(w.document.querySelector('.sources').textContent,/Source refresh fixture update/);assert.match(w.document.querySelector('.fresh').textContent,/Needs reconciliation/);
hidden=true;w.document.dispatchEvent(new w.Event('visibilitychange'));assert.equal([...timers.values()].filter(t=>t.ms===15000).length,0);const n=calls;await tick.fn();assert.equal(calls,n);
hidden=false;w.document.dispatchEvent(new w.Event('visibilitychange'));assert.ok([...timers.values()].find(t=>t.ms===15000));
fail=true;const old=w.document.getElementById('main').innerHTML;await [...timers.values()].find(t=>t.ms===15000).fn();assert.equal(w.document.getElementById('main').innerHTML,old);assert.match(w.document.querySelector('[role=status]').textContent,/Refresh unavailable/);
console.log('PASS: changed board and source rendered; moved card/open state/focus/scroll retained; hidden tab made no requests; failure retained content; 15-second scheduling verified.');dom.window.close();
})().catch(e=>{console.error(e);process.exitCode=1});
