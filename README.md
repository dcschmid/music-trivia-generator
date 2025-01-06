# Music Trivia Generator

This project generates multilingual trivia questions for music albums based on artist, album title, and release year. The trivia questions are categorized into three difficulty levels (easy, medium, hard) and stored in language-specific JSON files.

## Features

- **Multilingual Support**: Generates trivia questions in multiple languages (e.g., German, English, Spanish, French, Italian)
- **Batch Processing**: Efficiently generates 9 questions per album in a single API call
- **Three Difficulty Levels**: 3 questions per difficulty level (easy, medium, hard)
- **Realistic Questions**: Based on verifiable facts and historical context
- **Structured Output**: JSON format with metadata and links
- **Automatic File Management**: Processes input files and moves them to finished directory

## Prerequisites

1. Python 3.8+
2. OpenAI API Key
3. Installed Dependencies

## Installation

1. Clone repository:
```bash
git clone https://github.com/dcschmid/music-trivia-generator
cd music-trivia-generator
```

2. Create virtual environment:
```bash
python3 -m venv venv
   # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set API key in .env file:
```bash
OPENAI_API_KEY=your-openai-api-key
```

## Directory Structure

```
project/
├── input-files/           # Input directory
│   ├── top100_rock_albums.txt
│   ├── top100_pop_albums.txt
│   └── ...
├── output/               # Output directory
│   └── json/
│       ├── de/          # German questions
│       ├── en/          # English questions
│       ├── es/          # Spanish questions
│       └── ...
├── finished/            # Processed files
└── top100_multi.py
```

## Usage

### Command Line Options

```bash
python top100_multi.py <input_dir> <output_json_dir> <finished_dir> --languages <languages>
```

Parameters:
- `input_dir`: Directory containing input text files
- `output_json_dir`: Directory for JSON output
- `finished_dir`: Directory for processed files
- `--languages`: Comma-separated list of desired languages

### Examples

Using language codes:
```bash
python top100_multi.py 100txt jsons finished --languages de,en,es,fr,it
```

Using language names:
```bash
python top100_multi.py 100txt jsons finished --languages German,English,Spanish,French,Italian
```

### Input Format

Text files in input_dir should follow this format:
```
Artist - Album Title - Release Year
The Beatles - Abbey Road - 1969
Pink Floyd - Dark Side of the Moon - 1973
```

### Output Format

Generated JSON files follow this structure:
```json
{
    "artist": "The Beatles",
    "album": "Abbey Road",
    "year": "1969",
    "coverSrc": "/bandcover/60er/the-beatles_abbey-road.jpg",
    "spotify_link": "",
    "deezer_link": "",
    "apple_music_link": "",
    "preview_link": "",
    "questions": {
        "easy": [
            {
                "question": "Question text",
                "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
                "correctAnswer": "Correct option",
                "trivia": "Detailed explanation"
            },
            // 2 more easy questions
        ],
        "medium": [
            // 3 medium questions
        ],
        "hard": [
            // 3 hard questions
        ]
    }
}
```

### Question Categories

Questions cover various aspects such as:
- Chart Success and Rankings
- Song Lyrics and Meanings
- Musical Elements
- Production and Collaborations
- Historical and Cultural Significance
- Artist Inspirations
- Critical Reception
- Music Videos and Visuals

### Difficulty Levels

- **Easy**: Basic, easily researchable facts (e.g., singles, chart positions, famous songs)
- **Medium**: More detailed information (e.g., recording process, musicians involved, musical characteristics)
- **Hard**: Specific expert knowledge (e.g., technical details, historical context, cultural impact)

## Error Handling

The script includes:
- Validation of generated JSON structure
- Retry mechanism for API calls
- Proper error logging
- Fallback options if generation fails

## **Notes**

- Links (spotify_link, deezer_link, etc.) are left empty and need to be filled manually
- Cover images need to be placed in the appropriate decade folders
- The script processes all .txt files in the input directory
- Each language gets its own subdirectory in the output folder
