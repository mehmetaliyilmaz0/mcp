# client.py
import asyncio, pathlib, sys, json
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters

async def run(prompt: str):
    srv = pathlib.Path(__file__).with_name("server.py")
    if not srv.exists():
        raise SystemExit("server.py bulunamadı")

    async with stdio_client(
        StdioServerParameters(command="python", args=[srv.as_posix()])
    ) as tr, ClientSession(*tr) as s:
        await s.initialize()
        uri = (srv.parent / "data" / "notes.txt").resolve().as_uri()

        print("ÖNCE:\n", (await s.read_resource(uri)).contents[0].text)
        res = await s.call_tool("apply_edit", {"prompt": prompt})
        if res.content:
            print("YANIT:", json.loads(res.content[0].text))
        print("SONRA:\n", (await s.read_resource(uri)).contents[0].text)

async def main():
    if len(sys.argv) > 1:
        await run(" ".join(sys.argv[1:]))
    else:
        while (p := input("> ").strip()) not in {"quit", "exit"}:
            await run(p)

if __name__ == "__main__":
    asyncio.run(main())
