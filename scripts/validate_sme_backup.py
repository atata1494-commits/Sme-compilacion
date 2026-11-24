#!/usr/bin/env python3
"""Validador offline de respaldos SME. Inspecciona archivos; no restaura ni modifica."""
from __future__ import annotations
import argparse, hashlib, json, sqlite3, zipfile
from pathlib import Path, PurePosixPath

# Límites preventivos para evitar archivos ZIP desproporcionados (zip bombs).
MAX_ZIP_ENTRIES = 1000
MAX_ZIP_MEMBER_BYTES = 128 * 1024 * 1024
MAX_ZIP_TOTAL_BYTES = 256 * 1024 * 1024

def zip_preflight(infos) -> list[str]:
    issues=[]
    if len(infos) > MAX_ZIP_ENTRIES:
        issues.append(f"ZIP supera el máximo de entradas ({len(infos)} > {MAX_ZIP_ENTRIES})")
    total=0
    for info in infos:
        total += info.file_size
        member=PurePosixPath(info.filename)
        if member.is_absolute() or ".." in member.parts:
            issues.append(f"Ruta insegura dentro del ZIP: {info.filename}")
        if info.file_size > MAX_ZIP_MEMBER_BYTES:
            issues.append(f"Entrada demasiado grande ({info.file_size} bytes): {info.filename}")
        if total > MAX_ZIP_TOTAL_BYTES:
            issues.append(f"ZIP supera tamaño descomprimido máximo ({total} > {MAX_ZIP_TOTAL_BYTES} bytes)")
            break
        # Unix external attributes: reject symlinks and other special file types.
        mode=(info.external_attr >> 16) & 0xFFFF
        kind=mode & 0o170000
        if kind not in (0,0o100000,0o040000):
            issues.append(f"Tipo de archivo especial no permitido: {info.filename}")
        if info.flag_bits & 0x1:
            issues.append(f"Archivo cifrado no verificable sin clave: {info.filename}")
    return issues

def validate_backup(path: Path) -> list[str]:
    issues=[]
    if not path.is_file():
        return [f"No existe el archivo: {path}"]
    suffix=path.suffix.lower()
    if suffix == ".json":
        try:
            with path.open("r",encoding="utf-8") as f: json.load(f)
        except (OSError,UnicodeError,json.JSONDecodeError) as e: issues.append(f"JSON inválido o ilegible: {e}")
        return issues
    if suffix in {".db",".sqlite",".sqlite3"}:
        try:
            con=sqlite3.connect(f"file:{path.resolve()}?mode=ro",uri=True)
            try:
                result=con.execute("PRAGMA integrity_check").fetchall()
                if result != [("ok",)]: issues.append(f"SQLite integrity_check: {result}")
            finally: con.close()
        except sqlite3.Error as e: issues.append(f"SQLite no se puede abrir/validar: {e}")
        return issues
    if suffix == ".zip":
        try:
            with zipfile.ZipFile(path,"r") as z:
                infos=z.infolist()
                issues.extend(zip_preflight(infos))
                # Do not inflate or parse anything if the metadata limits failed.
                if issues: return issues
                bad=z.testzip()
                if bad: issues.append(f"CRC/archivo corrupto dentro del ZIP: {bad}")
                for info in infos:
                    if info.is_dir(): continue
                    name=info.filename.lower()
                    if name.endswith(".json"):
                        try: json.loads(z.read(info).decode("utf-8"))
                        except (UnicodeError,json.JSONDecodeError,RuntimeError,zipfile.BadZipFile) as e:
                            issues.append(f"JSON interno inválido ({info.filename}): {e}")
                    elif name.endswith((".db",".sqlite",".sqlite3")):
                        try:
                            raw=z.read(info)
                            con=sqlite3.connect(":memory:")
                            try:
                                con.deserialize(raw)
                                check=con.execute("PRAGMA integrity_check").fetchall()
                                if check != [("ok",)]: issues.append(f"SQLite interno inválido ({info.filename}): {check}")
                            finally: con.close()
                        except (sqlite3.Error,RuntimeError,zipfile.BadZipFile) as e:
                            issues.append(f"SQLite interno no verificable ({info.filename}): {e}")
        except (OSError,zipfile.BadZipFile,RuntimeError) as e: issues.append(f"ZIP inválido o ilegible: {e}")
        return issues
    return [f"Formato no soportado para validación automática: {suffix or '(sin extensión)'}"]

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
    return h.hexdigest()

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("backup",type=Path)
    args=ap.parse_args()
    issues=validate_backup(args.backup)
    print(f"Archivo: {args.backup}")
    try: print(f"SHA-256: {sha256(args.backup)}")
    except OSError as e: print(f"No se pudo calcular SHA-256: {e}")
    if issues:
        print(f"VALIDACIÓN: ALERTAS ({len(issues)})")
        for item in issues: print(f"- {item}")
        print("No restaurar sin revisar las alertas.")
        return 1
    print("VALIDACIÓN: estructura/formato verificados en las comprobaciones disponibles.")
    print("Esto no garantiza que el respaldo contenga todos los datos esperados ni que la restauración sea funcional.")
    return 0
if __name__=="__main__": raise SystemExit(main())
