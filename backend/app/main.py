from fastapi import FastAPI
from api.routes.paycalc import router as paycalc_router

app = FastAPI()
app.include_router(paycalc_router)


@app.get("/")
async def root():
    return {"message": "Hello World!"}
