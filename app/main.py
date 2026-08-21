from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from .agent import get_transfer, get_transfers, process_transfer
from .models import TransferRequest

load_dotenv()

app = FastAPI(title="Aira Transfer Agent", version="1.0.0")

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/transfers")
async def create_transfer(req: TransferRequest):
    try:
        transfer = process_transfer(req)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return transfer.model_dump(mode="json")


@app.get("/api/transfers")
async def list_transfers():
    return [t.model_dump(mode="json") for t in get_transfers()]


@app.get("/api/transfers/{transfer_id}")
async def read_transfer(transfer_id: str):
    transfer = get_transfer(transfer_id)
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    return transfer.model_dump(mode="json")
