from fastapi import FastAPI
from app.api.routes.paycalc_route import router as paycalc_router

app = FastAPI()
app.include_router(paycalc_router)


@app.get("/")
async def root():
    return {"message": "Hello World!"}
