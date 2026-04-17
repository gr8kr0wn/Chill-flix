from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from moviebox_api.moviebox import MovieBoxClient
from typing import Optional

app = FastAPI(title="Chillflix API", description="MovieBox API wrapper for Chillflix")

# Configure CORS to allow your frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:3000",
        "https://chillflix.vercel.app",
        "https://chillflix-git-main.vercel.app",
        "https://chillflix.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Chillflix API",
        "version": "1.0.0",
        "endpoints": [
            "/api/stream?title={movie_title}",
            "/api/search?query={search_term}",
            "/api/details?id={content_id}&type={movie|tv}"
        ]
    }

@app.get("/api/stream")
async def get_stream(title: str, year: Optional[int] = None):
    """
    Get a streamable URL for a movie or TV show.
    
    Args:
        title: The title of the movie/show
        year: Optional year to improve search accuracy
    
    Returns:
        JSON with stream_url and metadata
    """
    client = MovieBoxClient()
    
    try:
        # Build search query
        search_query = f"{title} {year}" if year else title
        
        # Search for content
        results = await client.search(search_query)
        
        if not results or len(results) == 0:
            raise HTTPException(status_code=404, detail=f"No results found for '{search_query}'")
        
        # Get the first/best match
        content = results[0]
        
        # Fetch detailed information including stream sources
        details = await client.get_details(content.id, content.media_type)
        
        # Extract stream URLs
        stream_urls = []
        if hasattr(details, 'sources') and details.sources:
            for source in details.sources:
                stream_urls.append({
                    "url": source.url,
                    "quality": getattr(source, 'quality', 'unknown'),
                    "format": "hls" if source.url.endswith('.m3u8') else "mp4"
                })
        
        if not stream_urls:
            raise HTTPException(status_code=500, detail="No playable sources found")
        
        # Sort by quality (assuming quality strings like "1080p", "720p", etc.)
        quality_order = {"4k": 5, "2160p": 5, "1080p": 4, "720p": 3, "480p": 2, "360p": 1}
        stream_urls.sort(key=lambda x: quality_order.get(str(x.get('quality', '')).lower(), 0), reverse=True)
        
        return {
            "success": True,
            "title": details.title if hasattr(details, 'title') else content.title,
            "year": getattr(details, 'year', None),
            "stream_url": stream_urls[0]["url"],
            "quality": stream_urls[0]["quality"],
            "format": stream_urls[0]["format"],
            "all_sources": stream_urls,
            "source": "MovieBox"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.get("/api/search")
async def search_content(query: str, limit: int = 10):
    """
    Search for movies and TV shows.
    
    Args:
        query: Search term
        limit: Maximum number of results to return
    
    Returns:
        JSON with search results
    """
    client = MovieBoxClient()
    
    try:
        results = await client.search(query)
        
        if not results:
            return {"success": True, "results": [], "count": 0}
        
        # Limit results
        limited_results = results[:limit]
        
        formatted_results = []
        for item in limited_results:
            formatted_results.append({
                "id": item.id,
                "title": item.title,
                "media_type": item.media_type,
                "year": getattr(item, 'year', None),
                "poster": getattr(item, 'poster_path', None)
            })
        
        return {
            "success": True,
            "results": formatted_results,
            "count": len(formatted_results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.get("/api/details")
async def get_content_details(id: str, type: str = "movie"):
    """
    Get detailed information about a specific movie or TV show.
    
    Args:
        id: The content ID
        type: Either 'movie' or 'tv'
    
    Returns:
        JSON with content details and stream sources
    """
    client = MovieBoxClient()
    
    try:
        details = await client.get_details(id, type)
        
        stream_urls = []
        if hasattr(details, 'sources') and details.sources:
            for source in details.sources:
                stream_urls.append({
                    "url": source.url,
                    "quality": getattr(source, 'quality', 'unknown'),
                    "format": "hls" if source.url.endswith('.m3u8') else "mp4"
                })
        
        return {
            "success": True,
            "id": id,
            "title": details.title if hasattr(details, 'title') else None,
            "year": getattr(details, 'year', None),
            "overview": getattr(details, 'overview', None),
            "poster": getattr(details, 'poster_path', None),
            "backdrop": getattr(details, 'backdrop_path', None),
            "stream_urls": stream_urls,
            "source": "MovieBox"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching details: {str(e)}")
