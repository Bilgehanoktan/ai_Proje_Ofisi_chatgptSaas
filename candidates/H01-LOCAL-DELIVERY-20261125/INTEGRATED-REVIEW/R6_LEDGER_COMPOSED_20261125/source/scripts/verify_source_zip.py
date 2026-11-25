"""Read-only R11 ZIP preflight; never extracts/imports/executes product code."""
import argparse, hashlib, json, re, stat, sys, zipfile
from pathlib import Path, PurePosixPath
PIN='337d4fa90bd93b2119da4cd7f6eba193e93d18fe'
COUNT=141
MAX_FILE=64*1024*1024
MAX_TOTAL=512*1024*1024

def git_blob(data):
    return hashlib.sha1(b'blob '+str(len(data)).encode('ascii')+b'\0'+data).hexdigest()

def safe_path(name):
    p=PurePosixPath(name)
    if not name or '\\' in name or ':' in name or p.is_absolute() or p.as_posix()!=name or any(x in ('..','.') or x.endswith(('.', ' ')) or any(ord(c)<32 or c in '<>"|?*' for c in x) or re.fullmatch(r'(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?',x) for x in p.parts):
        raise ValueError('UNSAFE_PATH: '+name)
    return p

def verify_zip(archive, pin=PIN, count=COUNT):
    with zipfile.ZipFile(archive) as z:
        entries={}; seen=set(); dirs=set(); total=0
        for i in z.infolist():
            name=i.filename.rstrip('/') if i.is_dir() else i.filename
            safe_path(name)
            folded=name.casefold()
            if folded in seen: raise ValueError('DUPLICATE_OR_CASE_COLLISION: '+name)
            seen.add(folded)
            kind=stat.S_IFMT(i.external_attr>>16)
            if kind not in (0,stat.S_IFREG,stat.S_IFDIR) or i.flag_bits&1:
                raise ValueError('UNSAFE_ENTRY: '+name)
            if i.is_dir(): dirs.add(name); continue
            if kind==stat.S_IFDIR or i.file_size>MAX_FILE: raise ValueError('ENTRY_LIMIT: '+name)
            total+=i.file_size
            if total>MAX_TOTAL: raise ValueError('ARCHIVE_LIMIT')
            entries[name]=i
        file_names={v.casefold() for v in entries}
        for name in [*entries,*dirs]:
            if any(str(p).casefold() in file_names for p in PurePosixPath(name).parents if str(p)!='.'):
                raise ValueError('FILE_PARENT_CONFLICT: '+name)
        candidates=[n for n in entries if n=='product/SOURCE_MANIFEST.json' or (n.endswith('/product/SOURCE_MANIFEST.json') and len(PurePosixPath(n).parts)==3)]
        if len(candidates)!=1: raise ValueError('MANIFEST_LOCATION_AMBIGUOUS')
        manifest_name=candidates[0]; prefix=manifest_name[:-len('SOURCE_MANIFEST.json')]
        raw=z.read(entries[manifest_name]);
        if git_blob(raw)!=pin: raise ValueError('MANIFEST_PIN_MISMATCH')
        def unique(pairs):
            obj={}
            for k,v in pairs:
                if k in obj: raise ValueError('DUPLICATE_JSON_KEY: '+k)
                obj[k]=v
            return obj
        data=json.loads(raw,object_pairs_hook=unique); files=data['files']
        if not isinstance(files,dict) or len(files)!=count: raise ValueError('MANIFEST_COUNT_MISMATCH')
        expected={manifest_name}
        for name,record in files.items():
            safe_path(name)
            if name=='SOURCE_MANIFEST.json' or not isinstance(record,dict) or type(record.get('bytes')) is not int or record['bytes']<0 or not re.fullmatch('[0-9a-f]{64}',record.get('sha256','')):
                raise ValueError('INVALID_MANIFEST_ENTRY: '+name)
            full=prefix+name; expected.add(full)
            i=entries.get(full)
            if i is None or i.file_size!=record['bytes']: raise ValueError('MISSING_OR_SIZE_MISMATCH: '+name)
            h=hashlib.sha256(); n=0
            with z.open(i) as f:
                while chunk:=f.read(65536):
                    n+=len(chunk)
                    if n>record['bytes']: raise ValueError('STREAM_LIMIT: '+name)
                    h.update(chunk)
            if n!=record['bytes'] or h.hexdigest()!=record['sha256']: raise ValueError('SOURCE_HASH_MISMATCH: '+name)
        actual={n for n in entries if n.startswith(prefix)}
        if actual!=expected: raise ValueError('PRODUCT_PATH_SET_MISMATCH')
        return {'source_integrity':'MATCH','manifest_blob':pin,'verified_product_entries':count,'product_files':len(actual),'archive_extracted':False,'product_executed':False,'authority':'NOT_EVALUATED'}

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('archive',type=Path); a=p.parse_args()
    try: print(json.dumps(verify_zip(a.archive),indent=2)); return 0
    except (OSError,ValueError,KeyError,TypeError,AttributeError,RuntimeError,zipfile.BadZipFile,NotImplementedError) as e:
        print(json.dumps({'source_integrity':'HOLD','reason':str(e),'product_executed':False},indent=2)); return 1
if __name__=='__main__': sys.exit(main())
