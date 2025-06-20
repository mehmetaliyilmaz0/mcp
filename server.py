# server.py
import difflib, pathlib, os
import google.generativeai as genai  # NEW: Gemini SDK
from mcp.server.fastmcp import FastMCP

BASE = pathlib.Path(__file__).parent
DATA = BASE / "data"; DATA.mkdir(exist_ok=True)
FILE = DATA / "notes.txt"
UTF8 = dict(encoding="utf8")


if not FILE.exists():
    FILE.write_text("Bu bir test notudur.\n2023 yılında yazıldı.\n", **UTF8)

genai.configure(api_key="GEMINI_API_KEY")  

app = FastMCP("editor")


@app.resource(FILE.resolve().as_uri(), name="Notlar", mime_type="text/plain")
async def oku():
    return FILE.read_text(**UTF8)


def _diff(old, new):
    return "\n".join(difflib.unified_diff(old.splitlines(), new.splitlines(),
                                          fromfile="old", tofile="new"))


@app.tool(name="apply_edit", description="Doğal dil komutla metni düzenler")
async def apply_edit(prompt: str):
    old = FILE.read_text(**UTF8)
    user_input = prompt.strip()

    system_prompt = (
        "Aşağıdaki metni kullanıcı komutuna göre düzenle. "
        "Sadece düzenlenmiş metnin tamamını döndür:\n\nMETİN:\n" + old
    )

    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(
            [
                {"role": "system", "parts": [system_prompt]},
                {"role": "user", "parts": [user_input]}
            ]
        )
        new = response.text.strip()
    except Exception as e:
        return {"status": "error", "message": str(e), "diff": ""}

    if new == old:
        return {"status": "no-change", "message": "Değişiklik yok", "diff": ""}

    FILE.write_text(new, **UTF8)
    return {"status": "modified", "diff": _diff(old, new)}

if __name__ == "__main__":
    app.run(transport="stdio")
