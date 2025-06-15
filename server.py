import difflib, pathlib, re, os
from mcp.server.fastmcp import FastMCP

BASE   = pathlib.Path(__file__).parent
DATA   = BASE / "data"; DATA.mkdir(exist_ok=True)
FILE   = DATA / "notes.txt"
if not FILE.exists():
    FILE.write_text("Bu bir test dosyasıdır.\n2023 yılında oluşturuldu.\n", encoding="utf8")
UTF8   = dict(encoding="utf8")


app = FastMCP("editor")

@app.resource(f"file:///{FILE.as_posix()}", name="Notes", mime_type="text/plain")
async def read_notes():             
    return FILE.read_text(**UTF8)

def _diff(a, b):                    
    return "\n".join(difflib.unified_diff(a.splitlines(), b.splitlines(),
                                          fromfile="old", tofile="new"))

@app.tool(name="apply_edit", description="Doğal dil komutla notları günceller")
async def apply_edit(prompt: str):
    old  = FILE.read_text(**UTF8)
    cmd  = prompt.strip()

    # 1) basit “X yerine Y” 
    p1 = re.search(r'"?([^"]+?)"?\s+yerine\s+"?([^"]+?)"?$', cmd, re.I)
    p2 = re.search(r'"?([^"]+?)"?\s+[iı]\s+"?([^"]+?)"?\s*yap$', cmd, re.I)
    if p1 or p2:
        new = old.replace(*(p1 or p2).groups())
    else:
        # 2) “sonuna … ekle”
        m = re.search(r'sonuna\s+"?([^"]+?)"?\s+ekle$', cmd, re.I)
        if m:
            new = old.rstrip("\n") + "\n" + m.group(1) + "\n"
        else:
            return {"status": "no-match", "message": "Komut anlaşılamadı", "diff": ""}

    if new == old:
        return {"status": "no-change", "message": "Değişiklik yok", "diff": ""}
    FILE.write_text(new, **UTF8)
    return {"status": "modified", "diff": _diff(old, new)}

if __name__ == "__main__":
    app.run(transport="stdio")
