# Music Trivia Generator

This Python script generates trivia questions for various music albums based on the artist, album title, and release year. It uses OpenAI’s API to create questions across multiple categories and difficulty levels, storing the trivia questions and metadata in JSON format.

## Features

- Automatically generates trivia questions for music albums using OpenAI’s GPT model.
- Supports trivia questions for three difficulty levels (easy, medium, hard).
- Randomizes trivia question categories to ensure variety.
- Ensures each category is used at least once for each difficulty level.
- Stores trivia questions and album information in JSON format for easy integration with other systems.

## Prerequisites

Before running the script, you need to have the following:

- Python 3.x
- OpenAI API Key

## Installation

1. Clone the repository:

```bash
git clone https://github.com/dcschmid/music-trivia-generator
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
2. Trivia Generation: For each album, the script uses OpenAI’s GPT-4 to generate trivia questions for three difficulty levels (easy, medium, hard). Each question includes:
  - The question itself.
  - Four possible answer options.
  - The correct answer.
  - A detailed trivia explanation.
3. Saving Results: The script stores the generated trivia, album information, and cover art path in a JSON file named {genre}.json.

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
