"""Standalone CSS fixture regression; not Next.js, React, W8 or native acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

PARENT_EDS = 'd5227c57cbf033a7269abe409ee5929819bc2a0d'
PARENT_GLOBALS = '4762316bf085b61c01ccf5a788d9c028f5ac6aab'

def blob(data):
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()

def markup(theme):
    metrics=''.join(f'<article class="metric"><small>{label}</small><div class="value">—</div><small>Doğrulanmadı</small></article>' for label in ['Bütçe','Rezervasyon','Maliyet','Tahsilat'])
    cards=''.join(f'<article class="item"><h3>{label}</h3><p>Salt okunur kaynak incelemesi. Gerçek işlem veya yetki yok.</p><button type="button">İncele</button></article>' for label in ['Skill & Memory','Finance & Security','Workflow Studio'])
    return f'''<!doctype html><html lang="tr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><body><div class="eds-frame" data-eds-theme="{theme}"><div class="shell"><aside class="sidebar"><div class="brand"><span class="mark">◈</span><div>AI COMPANY OS</div></div><nav><button aria-pressed="true">Yönetim</button><button>Projeler</button></nav></aside><main><header class="topline"><div><div class="eyebrow">P10J23 · CSS TEST FIXTURE</div><h1>Company Command Center</h1><small>Temsili görünüm · canlı veri yok</small></div><div class="chips"><button>Tema</button><span class="pill">HOLD</span></div></header><div class="notice">D0 · Sentetik görsel test · gerçek ürün değil</div><div class="metrics">{metrics}</div><section class="panel" id="management"><div class="bar"><h2>Şirket yönetim merkezleri</h2><span class="pill">NO SPEND</span></div><p class="sub">Kaynak ve kanıt inceleme</p><label>Kaynak ara <input type="search" placeholder="Kaynak veya fonksiyon"></label><div class="sectiongrid">{cards}</div><p class="projection-read-status" data-phase="hold">HOLD · Bağımsız kabul yok</p><code>{'a'*120}</code></section><div class="workspace"><section class="panel office-panel" id="embed-office"><h2>Office fixture</h2><div class="scene">Sahne yer tutucu</div></section><section class="panel operation-panel"><h2>Operation fixture</h2></section></div></main></div><div class="shell shell-office"><main><header class="topline" id="office-header"><h1>Office only fixture</h1></header><section class="panel" id="office-panel"><h2>Office only</h2><div class="sectiongrid"><article class="item">Fixture</article></div></section></main></div></div></body></html>'''

def style(page, selector, keys):
    return page.locator(selector).evaluate('(el, keys)=>Object.fromEntries(keys.map(k=>[k,getComputedStyle(el)[k]]))',keys)

def contrast(fg,bg):
    def lum(s):
        import re
        v=[int(x)/255 for x in re.findall(r'\d+',s)[:3]]
        v=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in v]
        return sum(x*y for x,y in zip(v,[.2126,.7152,.0722]))
    a,b=sorted([lum(fg),lum(bg)]);return (b+.05)/(a+.05)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--frontend',type=Path,required=True);ap.add_argument('--chromium',required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--globals',type=Path);args=ap.parse_args()
    glob=(args.globals or args.frontend/'app/globals.css').read_bytes();eds=(args.frontend/'design-system/eds.css').read_bytes();baseline,suffix=eds.split(b'\n/* P10J23:',1)
    assert blob(glob)==PARENT_GLOBALS and blob(baseline)==PARENT_EDS, 'PARENT_PIN_HOLD'
    args.output.mkdir(parents=True,exist_ok=True);results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=args.chromium,args=['--no-sandbox']);version=browser.version
        for theme in ['dark','light']:
            for width in [1440,768,390,320]:
                page=browser.new_page(viewport={'width':width,'height':900},reduced_motion='reduce')
                page.set_content(markup(theme));page.add_style_tag(content=glob.decode());page.add_style_tag(content=baseline.decode())
                office_selectors=['#embed-office','#embed-office .scene','#office-header h1','#office-panel','#office-panel .item']
                keys=['padding','borderRadius','boxShadow','backgroundColor','fontSize','width','height','gridTemplateColumns']
                before=[style(page,s,keys) for s in office_selectors]
                # Exclude dimensions that naturally depend on management content? Here office width/height remain same.
                hold_before=style(page,'.projection-read-status',['backgroundColor','color','borderLeftColor'])
                page.add_style_tag(content=eds.decode())
                after=[style(page,s,keys) for s in office_selectors]
                assert before==after,(theme,width,'office style changed',before,after)
                assert hold_before==style(page,'.projection-read-status',['backgroundColor','color','borderLeftColor'])
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),(theme,width,'horizontal overflow')
                inp=page.locator('input');inp.focus();st=style(page,'input',['backgroundColor','color','outlineStyle','outlineWidth','minHeight','fontSize'])
                assert st['outlineStyle']=='solid' and float(st['outlineWidth'][:-2])>=3
                assert float(st['minHeight'][:-2])>=44
                assert contrast(st['color'],st['backgroundColor'])>=4.5
                placeholder=inp.evaluate("el=>getComputedStyle(el,'::placeholder').color")
                assert contrast(placeholder,st['backgroundColor'])>=4.5
                if width<=680: assert st['fontSize']=='16px'
                if width<=420: assert len(style(page,'#management .sectiongrid',['gridTemplateColumns'])['gridTemplateColumns'].split())==1
                assert style(page,'#management',['borderRadius'])['borderRadius']=='18px'
                assert style(page,'#management .item:first-child button',['transitionDuration','animationDuration'])=={'transitionDuration':'0s','animationDuration':'0s'}
                screenshot=f'{theme}-{width}.png';page.screenshot(path=str(args.output/screenshot),full_page=True)
                results.append({'theme':theme,'width':width,'result':'PASS','checks':['office computed styles unchanged','HOLD colors unchanged','no horizontal document overflow','input focus and touch height','text and placeholder contrast >=4.5','mobile typography and single column when applicable','panel polish','reduced motion'],'input_contrast':round(contrast(st['color'],st['backgroundColor']),2),'placeholder_contrast':round(contrast(placeholder,st['backgroundColor']),2),'screenshot':screenshot});page.close()
        browser.close()
    evidence={'scope':'standalone synthetic HTML fixture with exact CSS, not React/Next or native office','chromium':version,'parent_eds':PARENT_EDS,'parent_globals':PARENT_GLOBALS,'candidate_eds':blob(eds),'results':results}
    (args.output/'VISUAL_FIXTURE_EVIDENCE.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(evidence,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
