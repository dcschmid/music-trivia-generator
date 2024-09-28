# Music Trivia Generator

This Python script generates trivia questions for various music albums, automatically downloads album covers, and stores the questions along with album metadata in JSON format. It uses multiple sources to fetch album cover art, including Last.fm, Spotify, Discogs, and TheAudioDB.

## Features

- Automatically generates trivia questions for music albums using OpenAI’s GPT-4.
- Downloads album covers from various APIs like Last.fm, Spotify, Discogs, and TheAudioDB.
- Supports trivia questions for various difficulty levels (easy, medium, hard).
- Stores trivia questions and album information in JSON format for easy integration with other systems.
- Logs missing album covers for manual follow-up.

## Prerequisites

Before running the script, you need to have the following:

- Python 3.x
- OpenAI API Key
- Last.fm API Key
- Spotify API credentials (Client ID and Client Secret)
- Discogs API Token (optional)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/music-trivia-generator.git
cd music-trivia-generator
```

2. Set up a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set your API keys:

- Create a .env file in the root directory and add the following keys:

```bash
OPENAI_API_KEY=your-openai-api-key
LASTFM_API_KEY=your-lastfm-api-key
SPOTIFY_CLIENT_ID=your-spotify-client-id
SPOTIFY_CLIENT_SECRET=your-spotify-client-secret
DISCOGS_API_TOKEN=your-discogs-token (optional)
```

## Usage

The script takes two command-line arguments: a text file containing album data and the genre name for cover storage.

1. Prepare a text file with the format:

```bash
Artist Name - Album Title - Release Year
```

Example (top100_albums.txt):

```bash
Jacques Brel - Ne Me Quitte Pas - 1972
Stromae - Racine Carrée - 2013
Gotye - Making Mirrors - 2011
```

2. Run the script with the file path and genre:

```bash
python3 top100.py top100_albums.txt "pop"
```

The script will generate trivia questions for each album and save album covers in the bandcover/{genre}/ directory.

## How It Works

1. Reading Album Data: The script reads a text file containing a list of albums in the format: Artist - Album - Year.
2. Cover Art Fetching:
  - The script first tries to fetch album covers from Last.fm.
  - If unavailable, it falls back to Spotify, Discogs, and TheAudioDB.
  - If no cover is found, it logs the missing album in a text file (missing_covers.txt).
3. Trivia Generation: For each album, the script uses OpenAI’s GPT-4 to generate trivia questions for three difficulty levels (easy, medium, hard). Each question includes:
  - The question itself.
  - Four possible answer options.
  - The correct answer.
  - A detailed trivia explanation.
4. Saving Results: The script stores the generated trivia, album information, and cover art path in a JSON file named {genre}.json.

## Example JSON Output

The output JSON will look like this:

```json
{
  "artist": "Stromae",
  "album": "Racine Carrée",
  "year": "2013",
  "coverSrc": "/bandcover/pop/stromae_racine_carree.jpg",
  "questions": {
    "easy": [
      {
        "question": "Which song from Stromae's album 'Racine Carrée' became a global hit?",
        "options": ["Papaoutai", "Formidable", "Tous les mêmes", "Ta fête"],
        "correctAnswer": "Papaoutai",
        "trivia": "'Papaoutai' is one of Stromae's most successful songs from 'Racine Carrée', released in 2013. It addresses the theme of absent fathers and became an international hit, topping charts across Europe."
      }
    ],
    "medium": [...],
    "hard": [...]
  }
}
```

## Logging Missing Covers

If the script fails to fetch an album cover, it logs the missing cover in a file called missing_covers.txt. This file includes the artist, album, and release year for manual follow-up.
