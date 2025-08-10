# app.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import Dict, Any
from image_renderer import render_image, save_and_bytes, TEMPLATE_PATH

app = FastAPI(title="Flight Quote Image API", version="1.0.0")

@app.get("/health")
async def health():
    return {"status": "ok", "template_exists": TEMPLATE_PATH.exists()}

@app.post("/render")
async def render(request: Request):
    try:
        payload: Dict[str, Any] = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="JSON inválido")

    try:
        img = render_image(payload, template_path=TEMPLATE_PATH)
        out_path, buf = save_and_bytes(img)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao renderizar: {e}")

    headers = {"X-Saved-Path": str(out_path)}
    return StreamingResponse(buf, media_type="image/png", headers=headers)
