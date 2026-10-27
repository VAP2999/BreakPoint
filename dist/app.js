import {total,evidence} from './cart.js';
const $=s=>document.querySelector(s); let quantity=1; let record=null;
$('#mode').value=new URLSearchParams(location.search).get('mode')==='fixed'?'fixed':'buggy';
const money=n=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD'}).format(n/100);
const fixed=()=>$('#mode').value==='fixed';
function render(){ $('#quantity').textContent=quantity; $('#total').textContent=money(total(quantity,fixed())); $('#remove').disabled=quantity===0; }
$('#remove').onclick=()=>{quantity=Math.max(0,quantity-1);render()};
$('#add').onclick=()=>{quantity++;render()};
function clear(){record=null;$('#status').textContent='READY';$('#evidence').innerHTML='<div class="empty"><b>Ready for a fresh run.</b><p>Run the reproduction to capture evidence for the selected fixture.</p></div>'}
$('#reset').onclick=()=>{quantity=1;clear();render()};
$('#mode').onchange=()=>{quantity=1;clear();render()};
$('#run').onclick=()=>{quantity=1;render();$('#remove').click();record={...evidence(quantity,fixed()),timestamp:new Date().toISOString(),steps:['Reset cart to one item','Click Remove item','Compare displayed total against $0.00'],displayedTotal:$('#total').textContent};$('#status').textContent=record.confirmed?'BUG REPRODUCED':'CONTRACT PASSED';$('#evidence').innerHTML=`<div class="steps">✓ Reset cart to one item<br>✓ Click Remove item<br>✓ Read quantity and displayed total</div><div class="result ${record.confirmed?'':'pass'}"><h3>${record.confirmed?'Empty cart retains a charge':'Fixed control passes'}</h3><span>${record.confirmed?'A zero-item cart still displays $24.00.':'A zero-item cart correctly displays $0.00.'}</span><div class="numbers"><div>EXPECTED<strong>$0.00</strong></div><div>OBSERVED<strong>${record.displayedTotal}</strong></div></div></div><p class="hint">Observed in this page with a deterministic probe. Independent browser replay is the next verification layer.</p><pre>await page.getByRole('button', { name: 'Remove item' }).click();\nawait expect(page.getByTestId('total')).toHaveText('$0.00');</pre><button class="secondary" id="export">Download evidence JSON</button>`;$('#export').onclick=()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(record,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='breakpoint-evidence.json';a.click();URL.revokeObjectURL(url)}};
render();
