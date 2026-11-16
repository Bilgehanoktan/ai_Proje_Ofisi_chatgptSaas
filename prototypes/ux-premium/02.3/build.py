"""Build standalone 02.3, pin exact 02.2 parent and never mutate it."""
from pathlib import Path
import hashlib,sys
here=Path(__file__).resolve().parent
parent=Path(sys.argv[1]) if len(sys.argv)>1 else here.parent/'02.2'/'office.html'
b=parent.read_bytes()
assert hashlib.sha256(b).hexdigest()=='86e177752f922a6fe498a93e7fd4aa31768267d716df4ca15cb7a1bd3c96f0a3','Unexpected parent'
html=b.decode('utf-8').replace('PREMIUM-02.2','PREMIUM-02.3',1)
assert html.count('</body>')==1
html=html.replace('</body>','<script>\n'+(here/'motion.js').read_text(encoding='utf-8')+'\n</script></body>')
(here/'office.html').write_text(html,encoding='utf-8')
