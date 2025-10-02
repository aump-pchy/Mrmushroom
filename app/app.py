from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image
import io, requests, os
from fastapi.staticfiles import StaticFiles

# --- Config ---
MODEL_PATH = "app/mrMushroom.pt"
CONF_THR = 0.25
IOU_THR  = 0.70
TOXIC = {'Deathcap','DestroyingAngel','Panthercap'}
UNCERTAIN_GAP = 0.10

app = FastAPI(title="MushroomGuard (.pt) on Cloud Run")
#app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ✅ เปิด CORS ให้เว็บ Firebase เรียก API ได้
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://web-production-4c99d.up.railway.app",   # เว็บ firebase ของคุณ
        "http://localhost:5000",              # เอาไว้เทส local
        "*"                                   # (ชั่วคราว) อนุญาตทุก origin
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)


# NOTE: อย่า import ultralytics ตรงนี้ (จะทำให้บูตช้า/พังตอน import)
_model = None
_class_names = None

def get_model():
    """โหลดโมเดลเมื่อมีรีเควสต์ครั้งแรกเท่านั้น"""
    global _model, _class_names
    if _model is None:
        from ultralytics import YOLO  # import ตรงนี้แทน
        m = YOLO(MODEL_PATH)
        _model = m
        # อ่านชื่อตรงจากโมเดล (กันชื่อคลาสไม่ตรง)
        _class_names = [m.names[i] for i in sorted(m.names)]
    return _model, _class_names

class URLBody(BaseModel):
    image_url: str

def infer_pil(img: Image.Image):
    m, names = get_model()
    r = m.predict(source=img, imgsz=896, conf=CONF_THR, iou=IOU_THR, verbose=False)[0]
    dets = []
    for b in r.boxes:
        cid = int(b.cls[0]); conf = float(b.conf[0])
        x1,y1,x2,y2 = [float(v) for v in b.xyxy[0].tolist()]
        label = names[cid] if cid < len(names) else f"class_{cid}"
        dets.append({"label": label, "confidence": round(conf,3), "xyxy": [x1,y1,x2,y2]})
    best = max(dets, key=lambda d: d["confidence"]) if dets else None
    return dets, best

def safety_policy(dets, best):
    if not best:
        return "uncertain", 0.0, 0.0, "ไม่พบเห็ด/รูปไม่ชัด (Unknown). ห้ามบริโภค", True
    toxic_max  = max([d["confidence"] for d in dets if d["label"] in TOXIC],  default=0.0)
    edible_max = max([d["confidence"] for d in dets if d["label"] not in TOXIC], default=0.0)
    if toxic_max >= 0.50:
        return "toxic", edible_max, toxic_max, "อันตราย/ห้ามบริโภค (Danger).", True
    if (edible_max - toxic_max) < UNCERTAIN_GAP or max(edible_max,toxic_max) < 0.5:
        return "uncertain", edible_max, toxic_max, "ไม่มั่นใจ (Uncertain). ห้ามบริโภค.", True
    return "info_only", edible_max, toxic_max, "ข้อมูลประกอบเท่านั้น.", True

#BASE_DIR = os.path.dirname(os.path.dirname(__file__))
#app.mount("/web", StaticFiles(directory=os.path.join(BASE_DIR, "www"), html=True), name="www")

@app.get("/")
def root():
    return {"ok": True, "message": "alive"}  # Cloud Run health check




@app.get("/healthz")
def health():
    return {"ok": True}

@app.post("/predict/url")
def predict_url(body: URLBody):
    try:
        r = requests.get(body.image_url, timeout=10)
        r.raise_for_status()
        img = Image.open(io.BytesIO(r.content)).convert("RGB")
    except Exception as e:
        raise HTTPException(400, f"Cannot fetch image: {e}")
    dets, best = infer_pil(img)
    status, edible_max, toxic_max, advice, toxic_flag = safety_policy(dets, best)
    return {"status": status, "prediction": best, "edible_max": edible_max,
            "toxic_max": toxic_max, "advice": advice, "toxic_flag": toxic_flag}

@app.post("/predict/file")
async def predict_file(file: UploadFile = File(...)):
    img = Image.open(io.BytesIO(await file.read())).convert("RGB")
    dets, best = infer_pil(img)
    status, edible_max, toxic_max, advice, toxic_flag = safety_policy(dets, best)
    return {"status": status, "prediction": best, "edible_max": edible_max,
            "toxic_max": toxic_max, "advice": advice, "toxic_flag": toxic_flag}
