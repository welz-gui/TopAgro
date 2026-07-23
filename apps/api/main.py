from fastapi import FastAPI, Depends, HTTPException
from typing import List

app = FastAPI(title="AgroTop 2.0 API")

@app.get("/")
def read_root():
    return {"message": "AgroTop 2.0 API Online"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}