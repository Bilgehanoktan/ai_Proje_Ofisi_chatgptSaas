"""Build standalone 02.4 from exact 02.3; no product writes."""
from pathlib import Path
import hashlib,sys
here=Path(__file__).resolve().parent
parent=Path(sys.argv[1]) if len(sys.argv)>1 else here.parent/'02.3'/'office.html'
b=parent.read_bytes()
assert hashlib.sha256(b).hexdigest()=='090152d2fa815e6ee49ca2725d1491cfe21ea77d8c0e49d7f875498b7d1a6da0','Unexpected parent'
html=b.decode('utf-8').replace('PREMIUM-02.3','PREMIUM-02.4',1)
assert html.count('</body>')==1
html=html.replace('</body>','<script>\n'+(here/'camera.js').read_text(encoding='utf-8')+'\n</script></body>')
(here/'office.html').write_text(html,encoding='utf-8')
