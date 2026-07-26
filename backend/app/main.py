from fastapi import FastAPI

app = FastAPI(title="EagleEye API")


@app.get("/health")
def health_check():
    return {"status": "ok"}
