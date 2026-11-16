"""Build standalone 02.2 from the exact 02.1 parent, never mutate the parent."""
from pathlib import Path
import hashlib,sys
here=Path(__file__).resolve().parent
parent=Path(sys.argv[1]) if len(sys.argv)>1 else here.parent/'02.1'/'office.html'
data=parent.read_bytes()
assert hashlib.sha256(data).hexdigest()=='a7d29336a87665cc1ecabac0a15f79b9a08f12ae7dfd3fe6c14f6daf8385eea1', 'Unexpected parent; stop and review'
html=data.decode('utf-8').replace('PREMIUM-02.1','PREMIUM-02.2')
css='''<style>.cast-panel{margin-top:16px;background:#141b27;border:1px solid #293347;border-radius:14px;overflow:hidden}.cast-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;padding:0 16px}.cast-card{display:grid;text-align:center;justify-items:center;background:radial-gradient(ellipse at 50% 20%,#39465a,#1a2331 78%);padding:12px;gap:3px}.cast-card svg{width:100%;max-width:146px;aspect-ratio:96/116;pointer-events:none}.cast-card strong{font-size:16px}.cast-note{padding:8px 16px 14px}.scene [data-avatar]{cursor:pointer}.scene [data-avatar]:focus{outline:2px solid #fff;outline-offset:3px}@media(max-width:600px){.cast-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}}</style>'''
assert html.count('</head>')==1 and html.count('</body>')==1
html=html.replace('</head>',css+'</head>').replace('</body>','<script>\n'+(here/'avatars.js').read_text(encoding='utf-8')+'\n</script></body>')
(here/'office.html').write_text(html,encoding='utf-8')
