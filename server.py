from fastapi import FastAPI, APIRouter, HTTPException, Depends, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import httpx
import base64
import json


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Spotify Configuration
SPOTIFY_CLIENT_ID = os.environ['SPOTIFY_CLIENT_ID']
SPOTIFY_CLIENT_SECRET = os.environ['SPOTIFY_CLIENT_SECRET']
# REDIRECT_URI = "http://localhost:3000/auth/callback"
REDIRECT_URI = "http://127.0.0.1:3000/auth/callback"

# Define Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    spotify_id: str
    display_name: str
    email: Optional[str] = None
    favorite_genres: List[str] = []
    favorite_artists: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserPreferences(BaseModel):
    genres: List[str]
    artists: List[str]

class Track(BaseModel):
    id: str
    name: str
    artists: List[str]
    album: str
    preview_url: Optional[str] = None
    image_url: Optional[str] = None
    external_url: str
    duration_ms: int
    popularity: int

class RecommendationRequest(BaseModel):
    user_id: str
    limit: Optional[int] = 20

class SavedTrack(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    track_id: str
    track_name: str
    artists: List[str]
    saved_at: datetime = Field(default_factory=datetime.utcnow)

# Spotify API Helper Functions
async def get_spotify_token():
    """Get Spotify client credentials token"""
    auth_string = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    auth_bytes = auth_string.encode('utf-8')
    auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
    
    headers = {
        'Authorization': f'Basic {auth_base64}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {'grant_type': 'client_credentials'}
    
    async with httpx.AsyncClient() as client:
        response = await client.post('https://accounts.spotify.com/api/token', headers=headers, data=data)
        if response.status_code == 200:
            return response.json()['access_token']
    return None

async def search_spotify_tracks(query: str, token: str, limit: int = 20):
    """Search for tracks on Spotify"""
    headers = {'Authorization': f'Bearer {token}'}
    params = {'q': query, 'type': 'track', 'limit': limit}
    
    async with httpx.AsyncClient() as client:
        response = await client.get('https://api.spotify.com/v1/search', headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        return None

async def get_spotify_recommendations(seed_genres: List[str], seed_artists: List[str], token: str, limit: int = 20):
    """Get recommendations from Spotify API"""
    headers = {'Authorization': f'Bearer {token}'}
    
    # Limit to 5 seeds total (Spotify API limitation)
    total_seeds = seed_genres[:3] + seed_artists[:2]
    
    params = {
        'limit': limit,
        'seed_genres': ','.join(seed_genres[:3]) if seed_genres else '',
        'seed_artists': ','.join(seed_artists[:2]) if seed_artists else '',
        'min_popularity': 30,
        'target_energy': 0.7,
        'target_danceability': 0.6
    }
    
    # Remove empty params
    params = {k: v for k, v in params.items() if v}
    
    async with httpx.AsyncClient() as client:
        response = await client.get('https://api.spotify.com/v1/recommendations', headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        return None

def format_track(track_data: Dict[str, Any]) -> Track:
    """Format Spotify track data to our Track model"""
    return Track(
        id=track_data['id'],
        name=track_data['name'],
        artists=[artist['name'] for artist in track_data['artists']],
        album=track_data['album']['name'],
        preview_url=track_data.get('preview_url'),
        image_url=track_data['album']['images'][0]['url'] if track_data['album']['images'] else None,
        external_url=track_data['external_urls']['spotify'],
        duration_ms=track_data['duration_ms'],
        popularity=track_data.get('popularity', 0)
    )

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Music Recommender API"}

@api_router.get("/genres")
async def get_available_genres():
    """Get available genres from Spotify"""
    token = await get_spotify_token()
    if not token:
        raise HTTPException(status_code=500, detail="Failed to get Spotify token")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    async with httpx.AsyncClient() as client:
        response = await client.get('https://api.spotify.com/v1/recommendations/available-genre-seeds', headers=headers)
        if response.status_code == 200:
            return response.json()
        raise HTTPException(status_code=500, detail="Failed to fetch genres")

@api_router.post("/users", response_model=User)
async def create_user(user_data: Dict[str, Any]):
    """Create a new user"""
    user = User(
        spotify_id=user_data.get('spotify_id', ''),
        display_name=user_data.get('display_name', ''),
        email=user_data.get('email')
    )
    await db.users.insert_one(user.dict())
    return user

@api_router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str):
    """Get user by ID"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)

@api_router.put("/users/{user_id}/preferences")
async def update_user_preferences(user_id: str, preferences: UserPreferences):
    """Update user preferences"""
    update_data = {
        "favorite_genres": preferences.genres,
        "favorite_artists": preferences.artists
    }
    
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "Preferences updated successfully"}

@api_router.get("/search")
async def search_tracks(q: str = Query(..., description="Search query"), limit: int = 20):
    """Search for tracks"""
    token = await get_spotify_token()
    if not token:
        raise HTTPException(status_code=500, detail="Failed to get Spotify token")
    
    results = await search_spotify_tracks(q, token, limit)
    if not results:
        raise HTTPException(status_code=500, detail="Search failed")
    
    tracks = [format_track(track) for track in results['tracks']['items']]
    return {"tracks": tracks}

@api_router.get("/recommendations/{user_id}")
async def get_recommendations(user_id: str, limit: int = 20):
    """Get personalized recommendations for a user"""
    # Get user preferences
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    token = await get_spotify_token()
    if not token:
        raise HTTPException(status_code=500, detail="Failed to get Spotify token")
    
    # Get recommendations based on user preferences
    seed_genres = user.get('favorite_genres', [])[:3]  # Spotify allows max 5 seeds
    seed_artists = user.get('favorite_artists', [])[:2]
    
    if not seed_genres and not seed_artists:
        # Default recommendations if no preferences set
        seed_genres = ['pop', 'rock', 'indie']
    
    recommendations = await get_spotify_recommendations(seed_genres, seed_artists, token, limit)
    if not recommendations:
        raise HTTPException(status_code=500, detail="Failed to get recommendations")
    
    tracks = [format_track(track) for track in recommendations['tracks']]
    return {"recommendations": tracks, "seed_genres": seed_genres, "seed_artists": seed_artists}

@api_router.post("/users/{user_id}/saved-tracks")
async def save_track(user_id: str, track_data: Dict[str, Any]):
    """Save a track to user's favorites"""
    saved_track = SavedTrack(
        user_id=user_id,
        track_id=track_data['track_id'],
        track_name=track_data['track_name'],
        artists=track_data['artists']
    )
    
    # Check if already saved
    existing = await db.saved_tracks.find_one({
        "user_id": user_id,
        "track_id": track_data['track_id']
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Track already saved")
    
    await db.saved_tracks.insert_one(saved_track.dict())
    return {"message": "Track saved successfully"}

@api_router.get("/users/{user_id}/saved-tracks")
async def get_saved_tracks(user_id: str):
    """Get user's saved tracks"""
    saved_tracks = await db.saved_tracks.find({"user_id": user_id}).to_list(1000)
    return {"saved_tracks": [SavedTrack(**track) for track in saved_tracks]}

@api_router.delete("/users/{user_id}/saved-tracks/{track_id}")
async def remove_saved_track(user_id: str, track_id: str):
    """Remove a saved track"""
    result = await db.saved_tracks.delete_one({
        "user_id": user_id,
        "track_id": track_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Saved track not found")
    
    return {"message": "Track removed successfully"}

@api_router.get("/trending")
async def get_trending_tracks(limit: int = 20):
    """Get trending/popular tracks"""
    token = await get_spotify_token()
    if not token:
        raise HTTPException(status_code=500, detail="Failed to get Spotify token")
    
    # Search for popular tracks
    results = await search_spotify_tracks("year:2024", token, limit)
    if not results:
        raise HTTPException(status_code=500, detail="Failed to get trending tracks")
    
    tracks = [format_track(track) for track in results['tracks']['items']]
    # Sort by popularity
    tracks.sort(key=lambda x: x.popularity, reverse=True)
    
    return {"trending_tracks": tracks}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
