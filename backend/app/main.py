from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import auth, files, templates, clean

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ClarifAI",
    description="AI-assisted data cleaning platform: describe your cleaning needs in plain English, "
    "get a fully cleaned, normalized Excel sheet back.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(files.router)
app.include_router(templates.router)
app.include_router(clean.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "ClarifAI backend"}


@app.get("/health")
def health():
    return {"status": "healthy"}
