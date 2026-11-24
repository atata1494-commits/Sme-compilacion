#!/usr/bin/env python3
"""Vista previa de recuperación SME: inspecciona respaldos sin extraer ni restaurar."""
from __future__ import annotations
import argparse, json, sqlite3, zipfile
from pathlib import Path, PurePosixPath
MAX_ENTRIES=1000
MAX_MEMBER=128*1024*1024
MAX_TOTAL=256*1024*1024
def preflight(infos):
    warnings=[]
    if len(infos)>MAX_ENTRIES: warnings.append(f"Demasiadas entradas: {len(infos)} (límite {MAX_ENTRIES})")
    total=0
    for i in infos:
        total+=i.file_size
        p=PurePosixPath(i.filename)
        if p.is_absolute() or ".." in p.parts: warnings.append(f"Ruta insegura: {i.filename}")
        if i.file_size>MAX_MEMBER: warnings.append(f"Archivo excede límite individual: {i.filename}")
        if total>MAX_TOTAL: warnings.append("ZIP excede el límite total descomprimido"); break
        mode=(i.external_attr>>16)&0xffff
        kind=mode&0o170000
        if kind not in (0,0o100000,0o040000): warnings.append(f"Archivo especial no permitido: {i.filename}")
        if i.flag_bits&1: warnings.append(f"Entrada cifrada no verificable: {i.filename}")
    return warnings
def sqlite_preview(raw):
    result={"tables":[],"warning":None}
    con=sqlite3.connect(":memory:")
    try:
        if not hasattr(con,"deserialize"):
            result["warning"]="Python no admite inspección SQLite en memoria (deserialize)."
            return result
        con.deserialize(raw)
        check=con.execute("PRAGMA integrity_check").fetchall()
        result["integrity"]="ok" if check==[("ok",)] else str(check)
        for name,sql in con.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
            safe=name.replace('"','""')
            try: count=con.execute(f'SELECT COUNT(*) FROM "{safe}"').fetchone()[0]
            except sqlite3.Error: count=None
            result["tables"].append({"name":name,"rows":count,"schema":sql})
    except sqlite3.Error as exc: result["warning"]=f"SQLite no verificable: {exc}"
    finally: con.close()
    return result
def preview_backup(path:Path):
    report={"file":str(path),"format":path.suffix.lower(),"warnings":[],"contents":[]}
    if not path.is_file():
        report["warnings"].append("El archivo no existe."); return report
    ext=path.suffix.lower()
    if ext==".json":
        try:
            data=json.loads(path.read_text(encoding="utf-8"))
            report["contents"].append({"type":"JSON","top_level_type":type(data).__name__,
                "top_level_keys":list(data.keys())[:100] if isinstance(data,dict) else None,
                "record_count":len(data) if isinstance(data,(dict,list)) else None})
        except (OSError,UnicodeError,json.JSONDecodeError) as e: report["warnings"].append(f"JSON inválido: {e}")
    elif ext in (".db",".sqlite",".sqlite3"):
        try:
            con=sqlite3.connect(f"file:{path.resolve()}?mode=ro",uri=True)
            try:
                tables=[]
                for name,sql in con.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
                    safe=name.replace('"','""')
                    count=con.execute(f'SELECT COUNT(*) FROM "{safe}"').fetchone()[0]
                    tables.append({"name":name,"rows":count,"schema":sql})
                report["contents"].append({"type":"SQLite","integrity":con.execute("PRAGMA integrity_check").fetchone()[0],"tables":tables})
            finally: con.close()
        except sqlite3.Error as e: report["warnings"].append(f"SQLite inválida/no legible: {e}")
    elif ext==".zip":
        try:
            with zipfile.ZipFile(path) as z:
                infos=z.infolist(); report["warnings"].extend(preflight(infos))
                if report["warnings"]: return report
                crc_bad=z.testzip()
                if crc_bad: report["warnings"].append(f"CRC defectuoso: {crc_bad}"); return report
                for info in infos:
                    if info.is_dir(): continue
                    name=info.filename.lower()
                    if name.endswith(".json"):
                        try:
                            data=json.loads(z.read(info).decode("utf-8"))
                            report["contents"].append({"file":info.filename,"type":"JSON","top_level_type":type(data).__name__,
                                "top_level_keys":list(data.keys())[:100] if isinstance(data,dict) else None,
                                "record_count":len(data) if isinstance(data,(dict,list)) else None})
                        except (UnicodeError,json.JSONDecodeError,RuntimeError,zipfile.BadZipFile) as e: report["warnings"].append(f"JSON interno no verificable ({info.filename}): {e}")
                    elif name.endswith((".db",".sqlite",".sqlite3")):
                        report["contents"].append({"file":info.filename,"type":"SQLite","preview":sqlite_preview(z.read(info))})
                    else: report["contents"].append({"file":info.filename,"type":"archivo","bytes":info.file_size})
        except (OSError,zipfile.BadZipFile,RuntimeError) as e: report["warnings"].append(f"ZIP inválido: {e}")
    else: report["warnings"].append("Formato no admitido para vista previa.")
    report["note"]="Vista previa solamente: no se extrae, no restaura y no modifica la base de datos activa."
    return report
def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("backup",type=Path); args=parser.parse_args()
    report=preview_backup(args.backup); print(json.dumps(report,ensure_ascii=False,indent=2))
    return 1 if report["warnings"] else 0
if __name__=="__main__": raise SystemExit(main())
