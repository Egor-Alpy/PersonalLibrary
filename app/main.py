from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from routers import books, authors, genres, publishers, readers, reviews
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="Personal Library API",
    description="API для управления личной библиотекой",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(books.router, prefix="/api/books", tags=["books"])
app.include_router(authors.router, prefix="/api/authors", tags=["authors"])
app.include_router(genres.router, prefix="/api/genres", tags=["genres"])
app.include_router(publishers.router, prefix="/api/publishers", tags=["publishers"])
app.include_router(readers.router, prefix="/api/readers", tags=["readers"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["reviews"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to Personal Library API",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)