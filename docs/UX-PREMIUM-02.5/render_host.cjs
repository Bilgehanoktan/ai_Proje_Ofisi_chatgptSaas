// Diagnostic renderer for the actual JSX route; not Next.js or React runtime.
const fs=require('node:fs'),vm=require('node:vm'),ts=require(process.env.TYPESCRIPT_MODULE||"typescript");
const path=require('node:path');
const local=path.join(__dirname,'source/product/ai-company-os-frontend');
const root=process.env.FRONTEND_ROOT|| (fs.existsSync(local)?local:path.resolve(__dirname,'../../product/ai-company-os-frontend'));
const source=fs.readFileSync(root+'/app/office/premium/page.tsx','utf8');
const result=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.React,jsxFactory:'h',target:ts.ScriptTarget.ES2020},reportDiagnostics:true});
if(result.diagnostics.some(d=>d.category===ts.DiagnosticCategory.Error))throw Error('TSX syntax');
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const style=v=>Object.entries(v).map(([k,x])=>k.replace(/[A-Z]/g,c=>'-'+c.toLowerCase())+':'+(typeof x==='number'?x+'px':x)).join(';');
function h(tag,attrs,...children){let a=Object.entries(attrs||{}).map(([k,v])=>` ${k==='className'?'class':k==='referrerPolicy'?'referrerpolicy':k==='srcDoc'?'srcdoc':k}="${esc(k==='style'?style(v):v)}"`).join('');return {html:`<${tag}${a}>${children.flat().map(c=>typeof c==='object'?c.html:esc(c)).join('')}</${tag}>`};}
const asset=fs.readFileSync(root+'/office/assets/premiumOfficeHtml.ts','utf8');
const assetExports={};vm.runInNewContext(ts.transpileModule(asset,{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{exports:assetExports});
const routeExports={};vm.runInNewContext(result.outputText,{exports:routeExports,h,require:id=>{if(id==='../../../office/assets/premiumOfficeHtml')return assetExports;throw Error('unexpected import '+id);}});
const shell=routeExports.default().html;
fs.writeFileSync(__dirname+'/host.html','<!doctype html><html lang="tr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Host diagnostic</title><style>*{box-sizing:border-box}body{margin:0;background:#0b1220;color:#e8f0f7;font:14px system-ui} .topline{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}.eyebrow,.sub{color:#a4b5c7}.notice{background:#29231c;color:#e5d1ae;padding:12px;border-radius:8px}a{color:#9ad9e4}h1{margin:4px 0}</style>'+shell+'</html>');
