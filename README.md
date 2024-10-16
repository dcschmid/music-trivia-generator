# Music Trivia Generator

This project generates trivia questions for music albums based on the artist, album title, and release year. Trivia questions are categorized into three difficulty levels (easy, medium, hard) and are stored in JSON files. The script utilizes the OpenAI API to generate trivia questions.

## Features

- Trivia Generation: Automatically generates trivia questions for albums based on various categories like Chart Success, Song Lyrics, Production, and Historical Impact.

- Multi-Level Difficulty: Trivia questions are grouped into easy, medium, and hard difficulty levels.

- Wide Range of Categories: Questions cover a variety of music-related categories such as:

  - Song lyrics and meanings
  - Collaborations with other artists
  - Social and political relevance
  - Visual elements (music videos, album art, etc.)
  - Recording techniques and production elements
  - Fan reactions, awards, and chart success

- Randomized Question Formulation: The script dynamically generates questions with varied sentence structures to ensure each question is unique.

- Support for Multiple Albums and Genres: You can process entire directories of text files, each representing a different genre, containing lists of albums.

- Persistence: Generated trivia is saved in JSON format, allowing it to be reused and extended over time.

- Seamless File Handling: The script automatically processes files from an input directory, writes output to a specified directory, and moves completed files to a “finished” directory.

## Prerequisites

Before running the script, you need to have the following:

1. Python 3.8+: Ensure that you have Python 3.8 or a more recent version installed.
2. OpenAI API Key: An OpenAI API key is required to generate the trivia questions. You can sign up for the API here.
3. Environment Variables: The API key and other sensitive information should be stored in a .env file.

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

The script processes text files containing lists of albums. For each album, it generates trivia questions, saves them to a corresponding JSON file, and moves the processed files to a “finished” directory.

### Command-Line Usage

To run the script, use the following command:

```bash
python top100.py <input_dir> <output_json_dir> <finished_dir>
```

- <input_dir>: The directory containing text files with album data.
- <output_json_dir>: The directory where the generated JSON files will be saved.
- <finished_dir>: The directory where processed text files will be moved after completion.

#### Example

```bash
python top100.py ./top100-files ./json-output ./finished
```

#### Input File Format

Each input text file should contain a list of albums, with each line formatted as follows:

```bash
Artist Name - Album Title - Release Year
```

For example:

```bash
Jacques Brel - Ne Me Quitte Pas - 1972
Stromae - Racine Carrée - 2013
Gotye - Making Mirrors - 2011
```

### Output File Format

The script generates a JSON file for each genre (based on the input file names) containing trivia questions for each album. The output file format is as follows:

```json
{
    "artist": "The Beatles",
    "album": "Abbey Road",
    "year": "1969",
    "questions": {
        "easy": [
            {
                "question": "Sample question",
                "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
                "correctAnswer": "Option 1",
                "trivia": "Explanation of the correct answer."
            }
        ],
        "medium": [...],
        "hard": [...]
    }
}
```

## Customization

The script provides trivia questions from various categories, such as:

- Chart Success and Rankings
- Song Lyrics and Meanings
- Musical Elements
- Production and Collaborations
- Historical and Cultural Significance
- Artist Inspirations
- Critical Reception
- Music Videos and Visuals
- … and more

You can expand or customize the list of categories in the script under the categories list.
