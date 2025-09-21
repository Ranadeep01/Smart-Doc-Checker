import os
import uuid
import hashlib
import time
import datetime
import threading
import requests
import cloudinary.uploader

from fastapi import FastAPI, UploadFile, File, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.sql import func
from openai import OpenAI
from flexprice_utils import track_documents_checked, track_reports_generated, get_user_usage
import flexprice

FLEXPRICE_API_KEY = os.getenv("FLEXPRICE_API_KEY", "your_flexprice_api_key_here")
flexprice.api_key = FLEXPRICE_API_KEY

# -----------------------------
# ENVIRONMENT VARIABLES
# -----------------------------
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "123")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "documents_dev")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "dm3de3gy3")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "384768686711434")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "xoumq71Vh_KZtYT6f_S54BgJfTA")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your_openai_api_key_here")

# -----------------------------
# DATABASE SETUP
# -----------------------------
engine = create_engine(DATABASE_URL, echo=True)  # echo=True logs SQL queries
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# -----------------------------
# CLOUDINARY CONFIG
# -----------------------------
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)

# -----------------------------
# OPENAI CLIENT
# -----------------------------
client = OpenAI(api_key=OPENAI_API_KEY)

# -----------------------------
# PRICING
# -----------------------------
PRICE_PER_DOC = 10
PRICE_PER_REPORT = 50

# -----------------------------
# DATABASE MODELS
# -----------------------------
from sqlalchemy.dialects.postgresql import UUID, BIGINT, TEXT

class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = {"schema": "documents"}

    id = Column(BIGINT, primary_key=True, index=True)  # match bigint
    submission_id = Column(UUID(as_uuid=True), index=True)  # match uuid
    document_name = Column(TEXT)  # match text
    uploaded_on = Column(DateTime(timezone=True), server_default=func.now())  # match timestamp with tz

class Usage(Base):
    __tablename__ = "usage"
    __table_args__ = {"schema": "documents"}
    id = Column(Integer, primary_key=True, index=True)
    total_docs_checked = Column(Integer, default=0)
    total_reports_generated = Column(Integer, default=0) 

# Create tables if not exist
Base.metadata.create_all(bind=engine)

# -----------------------------
# DEPENDENCY
# -----------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------------
# FASTAPI APP & CORS
# -----------------------------
app = FastAPI(title="Smart Doc Checker")

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# HELPERS
# -----------------------------
def get_timestamp():
    """Returns timezone-aware datetime"""
    return datetime.datetime.now(datetime.timezone.utc)

# -----------------------------
# UPLOAD ENDPOINT
# -----------------------------
@app.post("/upload", response_model=None)
async def upload_documents(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    if len(files) < 2 or len(files) > 3:
        return JSONResponse(status_code=400, content={"message": "Upload 2–3 documents only."})

    submission_id = str(uuid.uuid4())
    uploaded_docs = []

    try:
        for file in files:
            res = cloudinary.uploader.upload(file.file.read(), resource_type="auto")
            file.file.seek(0)  # reset pointer if needed

            doc = Submission(
                submission_id=submission_id,
                document_name=file.filename,
                uploaded_on=get_timestamp()
            )
            db.add(doc)
            uploaded_docs.append({"name": file.filename, "url": res['secure_url']})

        # Update usage
        usage = db.query(Usage).first()
        if not usage:
            usage = Usage(total_docs_checked=len(files))
            db.add(usage)
        else:
            usage.total_docs_checked += len(files)

        db.commit()
        track_documents_checked(user_id=submission_id, quantity=len(files))
        return {"message": "Files uploaded successfully", "docs": uploaded_docs, "submission_id": submission_id}

    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"message": f"Upload failed: {e}"})


# -----------------------------
# ANALYZE ENDPOINT
# -----------------------------
@app.post("/analyze", response_model=None)
async def analyze(submission_id: str, db: Session = Depends(get_db)):
    docs = db.query(Submission).filter(Submission.submission_id == submission_id).all()
    if not docs:
        return JSONResponse(status_code=404, content={"message": "No documents found."})

    doc_texts = "\n\n".join([f"{doc.document_name}: Sample content placeholder." for doc in docs])
    prompt = f"Find contradictions in the following documents:\n{doc_texts}\nProvide explanation and suggestions."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        analysis = response.choices[0].message["content"]
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Analysis failed: {e}"})

    # Update report usage
    usage = db.query(Usage).first()
    if usage:
        usage.total_reports_generated += 1
    db.commit()
    track_reports_generated(user_id=submission_id)

    return {"analysis": analysis}

# -----------------------------
# USAGE ENDPOINT
# -----------------------------
from flexprice_utils import get_user_usage

@app.get("/usage/{submission_id}", response_model=None)
async def get_usage(submission_id: str):
    """
    Fetch usage and billing info from Flexprice for a specific submission/user.
    """
    usage_data = get_user_usage(user_id=submission_id)
    return usage_data


# -----------------------------
# EXTERNAL DOC MONITOR (OPTIONAL)
# -----------------------------
def monitor_external_doc():
    url = "https://example.com/college-rules"
    last_hash_file = "last_hash.txt"

    while True:
        try:
            resp = requests.get(url)
            content_hash = hashlib.md5(resp.text.encode()).hexdigest()
            last_hash = ""
            if os.path.exists(last_hash_file):
                with open(last_hash_file, "r") as f:
                    last_hash = f.read()

            if content_hash != last_hash:
                with open(last_hash_file, "w") as f:
                    f.write(content_hash)

                # Trigger analysis for last submission
                with SessionLocal() as db:
                    last_submission = db.query(Submission).order_by(Submission.uploaded_on.desc()).first()
                    if last_submission:
                        requests.post("http://localhost:8000/analyze", json={"submission_id": last_submission.submission_id})
        except Exception as e:
            print("Monitoring error:", e)
        time.sleep(60)

# Uncomment to enable background monitor
# threading.Thread(target=monitor_external_doc, daemon=True).start()
