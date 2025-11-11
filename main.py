import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId
from datetime import datetime

from database import db, create_document, get_documents
from schemas import Article

app = FastAPI(title="Mystical Team API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def serialize_doc(doc: dict):
    d = {**doc}
    if "_id" in d:
        d["id"] = str(d.pop("_id"))
    # Convert datetimes to isoformat
    for k, v in list(d.items()):
        if isinstance(v, datetime):
            d[k] = v.isoformat()
    return d


@app.get("/")
def read_root():
    return {"message": "Mystical Team API is running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, "name") else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    return response


class ArticleOut(BaseModel):
    id: str
    title: str
    category: str
    summary: str | None = None
    content: str
    image_url: str | None = None
    published_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@app.get("/api/articles", response_model=List[ArticleOut])
def list_articles(
    category: Optional[str] = Query(None, description="Filter by category"),
    q: Optional[str] = Query(None, description="Search by title keyword"),
    limit: int = Query(50, ge=1, le=100),
):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    filter_dict: dict = {}
    if category:
        filter_dict["category"] = category
    if q:
        filter_dict["title"] = {"$regex": q, "$options": "i"}

    docs = get_documents("article", filter_dict, limit)
    return [serialize_doc(d) for d in docs]


@app.get("/api/articles/{article_id}", response_model=ArticleOut)
def get_article(article_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        oid = ObjectId(article_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid article id")

    doc = db["article"].find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Article not found")
    return serialize_doc(doc)


@app.post("/api/articles", response_model=str)
def create_article(article: Article):
    # Minimal create endpoint (useful for seeding)
    try:
        new_id = create_document("article", article)
        return new_id
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/seed")
def seed_content():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    count = db["article"].count_documents({})
    if count > 0:
        return {"status": "ok", "message": "Content already exists", "count": int(count)}

    samples: list[Article] = [
        Article(
            title="Echoes of the Library of Alexandria",
            category="history",
            summary="The rise, brilliance, and mysteries surrounding the ancient world's greatest repository of knowledge.",
            content=(
                "Founded in the 3rd century BCE, the Library of Alexandria became a beacon of scholarship..."
            ),
            image_url="https://images.unsplash.com/photo-1524178232363-1fb2b075b655",
        ),
        Article(
            title="The Many Faces of Athena",
            category="mythology",
            summary="From warrior goddess to patron of wisdom — tracing Athena across cultures.",
            content=(
                "Athena, revered in classical Greece, embodied strategy, crafts, and civic virtue..."
            ),
            image_url="https://images.unsplash.com/photo-1520785643438-5bf77931f29a",
        ),
        Article(
            title="Antikythera Mechanism: The Ancient Computer",
            category="science",
            summary="A 2,000-year-old device that predicted celestial events with surprising precision.",
            content=(
                "Recovered from a shipwreck in 1901, the Antikythera mechanism challenged our assumptions about ancient engineering..."
            ),
            image_url="https://images.unsplash.com/photo-1518770660439-4636190af475",
        ),
    ]

    inserted = 0
    for a in samples:
        create_document("article", a)
        inserted += 1

    return {"status": "ok", "inserted": inserted}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
