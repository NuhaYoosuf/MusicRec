# MusicRec
music-recommender-app

> Discover music tailored to your taste using Spotify's recommendation engine, FastAPI, and a beautiful React interface.

<img width="1364" height="638" alt="image" src="https://github.com/user-attachments/assets/f42f88c4-8e15-47a6-b1cb-e2c5f456580a" />

📌 Overview

**MusicRec** is a full-stack music discovery application that:
- Lets users register with a display name and email
- Collects music preferences like genres and artists
- Uses the Spotify API to generate personalized music recommendations
- Allows saving/removing favorite tracks
- Supports trending track browsing and music previews
- Has a clean, responsive frontend using **React** and **CSS3**
- Is powered by a **FastAPI backend** and **MongoDB** for storage

---

## 🚀 Features

### 👤 User Setup & Management
- Simple user onboarding
- Preference-based music profiles
- Save users and preferences in MongoDB

### 🎵 Recommendations Engine
- Fetch recommendations from Spotify based on selected genres/artists
- Default recommendations for new users
- Trending songs section (popular new tracks from current year)

### 🔍 Music Search
- Search songs, albums, or artists via Spotify Search API
- Save/unsave tracks to a personal library

### 💾 Save & Manage Tracks
- Save tracks you love
- View and remove them from a personal saved tracks modal

### 🌈 Responsive UI
- Beautiful and minimal interface
- Mobile-first responsive design with pure CSS

---
🧑‍💻 Tech Stack

| Layer       | Technology                            |
|-------------|----------------------------------------|
| Frontend    | React, Axios, CSS3                     |
| Backend     | FastAPI, Uvicorn, httpx, Python 3.10+  |
| Database    | MongoDB (via `motor`)                  |
| Auth/API    | Spotify Web API                        |
| Environment | dotenv, CORS Middleware                |

---

## 🛠 Setup Instructions

### 🔧 Prerequisites

- Node.js & npm
- Python 3.10+
- MongoDB (local or Atlas)
- Spotify Developer Account

🔐 Spotify Setup

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Add this redirect URI:
[http://localhost:3000/auth/callback](http://localhost:3000/auth/callback)
4. Copy the **Client ID** and **Client Secret**

📁 Environment Variables

Create a `.env` file inside your backend folder:

```env
# .env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="music_recommender"
SPOTIFY_CLIENT_ID="your_spotify_client_id"
SPOTIFY_CLIENT_SECRET="your_spotify_client_secret"
````

---

### 🔌 Backend (FastAPI)

1. Navigate to the backend directory
2. Install dependencies:

```bash
pip install fastapi uvicorn python-dotenv motor httpx pydantic
```

3. Run the server:

```bash
uvicorn server:app --reload --port 8000
```

* Make sure `server.py` is the correct filename

---

### 🌐 Frontend (React)

1. Navigate to the frontend folder:

```bash
cd frontend
```

2. Create `.env` file:

```env
REACT_APP_BACKEND_URL=http://localhost:8000
```

3. Install dependencies and run:

```bash
npm install
npm start
```

---

## 🌍 API Endpoints (Backend)

| Method | Endpoint                                | Description                           |
| ------ | --------------------------------------- | ------------------------------------- |
| GET    | `/api/genres`                           | Fetch available Spotify genres        |
| POST   | `/api/users`                            | Create a new user                     |
| GET    | `/api/users/{user_id}`                  | Get user details                      |
| PUT    | `/api/users/{user_id}/preferences`      | Update user's favorite genres/artists |
| GET    | `/api/search?q=`                        | Search tracks                         |
| GET    | `/api/recommendations/{user_id}`        | Personalized recommendations          |
| POST   | `/api/users/{user_id}/saved-tracks`     | Save a track                          |
| GET    | `/api/users/{user_id}/saved-tracks`     | Get user's saved tracks               |
| DELETE | `/api/users/{user_id}/saved-tracks/:id` | Remove a saved track                  |
| GET    | `/api/trending`                         | Get trending tracks                   |

---

## 📸 Screenshots

| Home                            | Preferences                                   | Recommendations                            |
| ------------------------------- | --------------------------------------------- | ------------------------------------------ |
| ![home](./screenshots/home.png) | ![preferences](./screenshots/preferences.png) | ![recs](./screenshots/recommendations.png) |

---

## 🧪 Future Enhancements

* Spotify OAuth login
* Play full-length tracks
* Collaborative playlists with other users
* Emotion-based recommendations (via webcam or text input)

---

## 👨‍💻 Author

**Nuha Yoosuf**
[GitHub](https://github.com/your-username) • [LinkedIn](https://linkedin.com/in/your-name)

---

