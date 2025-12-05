# (paste-in full app if you prefer; minimal placeholder below if you want to build up)
from fastapi import FastAPI
app = FastAPI()

@app.get("/health")
def health():
    return {"status":"ok"}
