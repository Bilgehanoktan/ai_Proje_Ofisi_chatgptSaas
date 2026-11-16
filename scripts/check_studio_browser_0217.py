"""0217 isolated helper browser harness, not product React/Next browser."""
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright
p=argparse.ArgumentParser()
p.add_argument('compiled_js',type=Path)
p.add_argument('--chromium',required=True)
a=p.parse_args()
js=a.compiled_js.read_text()
with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path=a.chromium,headless=True,args=['--no-sandbox'])
    page=b.new_page(viewport={'width':390,'height':844})
    page.set_content('<main><button id="plan">Plan</button><button id="qa">QA</button><button id="clear">Temizle</button><p role="status" id="status"></p></main>')
    page.add_script_tag(content='var exports={};'+js+'''\nconst tasks={plan:{id:'plan',label:'Plan',role:'Planner',state:'HOLD',depends_on:[]},qa:{id:'qa',label:'QA',role:'QA',state:'HOLD',depends_on:['plan']}};for(const id of ['plan','qa','clear'])document.getElementById(id).onclick=()=>{const v=exports.studioContext(tasks[id]);document.getElementById('status').textContent=v?v.roleLabel+' | '+v.agentLabel+' | '+v.decision:'HOLD';};''')
    for name,expected in [('plan','Planner | Atanmış ajan doğrulanmadı | HOLD'),('qa','QA | Atanmış ajan doğrulanmadı | HOLD'),('clear','HOLD')]:
        page.locator('#'+name).click(); assert page.get_by_role('status').inner_text()==expected; print('PASS',name,expected)
    assert page.evaluate('exports.historicalAgentContext().placementAllowed') is False; print('PASS historical placement denied')
    print('Chromium version:',b.version); b.close()
