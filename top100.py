import openai
import json
import re
import os
import argparse
import random
from dotenv import load_dotenv  # Import the dotenv package

# Load environment variables from the .env file
load_dotenv()

# Retrieve API keys and secrets from environment variables
openai.api_key = os.getenv('OPENAI_API_KEY')

def read_album_data(file_path):
    """
    Reads a file containing a list of albums and stores the data in a list of dictionaries.
    Each dictionary contains the artist, album and year of the album.
    """
    album_data = []
    with open(file_path, 'r') as file:
        lines = file.readlines()

    for line in lines:
        line = line.strip()
        try:
            # Split the line from the last occurrence of ' - ' to separate year from artist/album
            # Example: "Kraftwerk - The Man-Machine - 1978"
            artist_album, year = line.rsplit(' - ', 1)
            artist, album = artist_album.split(' - ', 1)
            album_data.append({
                "artist": artist,
                "album": album,
                "year": year
            })
        except ValueError:
            print(f"Zeile übersprungen (unerwartetes Format): {line}")

    # Return the list of album dictionaries
    return album_data

def clean_filename(text):
    """
    Replaces special characters in a filename with underscores and converts to lower case.

    This is useful for creating filenames from strings that may contain special characters,
    such as song titles or album names.

    Args:
        text (str): The text to be cleaned.

    Returns:
        str: The cleaned text.
    """
    # Replace special characters in a filename with underscores
    cleaned_text = re.sub(r'[^A-Za-z0-9]', '_', text)
    # Convert to lower case
    cleaned_text = cleaned_text.lower()
    return cleaned_text

def extract_json_from_response(raw_content):
    """
    Extracts the JSON part from the response, even if additional text is present.

    The function will search for a JSON object in the given text and try to parse
    it as JSON. If a valid JSON object is found, it will be returned. If no valid
    JSON object is found, a ValueError will be raised.

    Args:
        raw_content (str): The text to search for a JSON object.

    Returns:
        dict: The parsed JSON object, or None if no valid JSON object could be found.

    Raises:
        ValueError: If no valid JSON object could be found.
    """
    try:
        # Look for a JSON object (curly brackets containing key-value pairs)
        # The re.DOTALL flag makes the "." special character match any character
        # at all, including a newline; this is necessary because the JSON object
        # can span multiple lines.
        json_pattern = r'\{.*\}'
        matches = re.findall(json_pattern, raw_content, re.DOTALL)
        if matches:
            # Iterate over the matches and try to parse each one as JSON
            for match in matches:
                try:
                    # Try to parse the match as JSON
                    return json.loads(match)
                except json.JSONDecodeError as e:
                    # If the match is not valid JSON, print an error message
                    # and continue to the next match
                    print(f"Error loading JSON: {e}, content: {match}")
                    continue
        # If no valid JSON object is found, raise a ValueError
        raise ValueError("No valid JSON format found.")
    except Exception as e:
        # If an unexpected error occurs, print an error message and return None
        print(f"Error extracting JSON: {e}")
        return None

def generate_trivia_for_album(album, artist, year, retries=3):
    """
    Generates trivia questions for an album with the given artist, album title, and year.
    The questions are categorized into easy, medium, and hard difficulties.
    """
    questions = {"easy": [], "medium": [], "hard": []}

    # Expanded categories list
    categories = [
        "Erfolge und Chartplatzierungen", "Songtexte und Bedeutung", "Musikalische Elemente",
        "Produktion und Kollaborationen", "Hintergrund und interessante Fakten", "Historische und kulturelle Bedeutung",
        "Inspirationsquellen des Künstlers", "Live-Auftritte und Touren", "Kritiken und Rezeption",
        "Musikvideos und visuelle Inhalte", "Fan-Reaktionen und Popkultur-Einflüsse", "Albumkonzept und Thematik",
        "Instrumentierung und Produktionstechniken", "Bedeutende Auftritte", "Reaktionen der Musikpresse",
        "Einfluss auf die Musikszene", "Kollaborationen mit anderen Künstlern", "Erfolge bei Musikpreisen",
        "Persönliche Erfahrungen des Künstlers", "Soziale und politische Relevanz", "Musikvideos und visuelle Elemente",
        "Stilistische Innovationen", "Gesellschaftliche Botschaften", "Berühmte Zitate aus dem Album",
        "Aufnahmeprozess", "Kontroversen um das Album"
    ]

    # Loop over difficulty levels
    for difficulty in ["easy", "medium", "hard"]:
        used_categories = set()

        while len(questions[difficulty]) < 3:
            # Shuffle categories for each question generation to ensure randomness
            random.shuffle(categories)
            available_categories = [cat for cat in categories if cat not in used_categories]
            if not available_categories:
                print(f"No more available categories for {difficulty}.")
                break
            selected_category = available_categories.pop()
            used_categories.add(selected_category)

            prompt = f"""
            Erstelle 1 Trivia-Frage auf Deutsch für das Album '{album}' von {artist}, das im Jahr {year} veröffentlicht wurde.
            Die Frage sollte sich auf die Kategorie '{selected_category}' konzentrieren.
            Die Frage sollte vom Schwierigkeitsgrad '{difficulty}' sein.
            Jede Frage MUSS den Namen des Künstlers {artist} und den Titel des Albums '{album}' explizit in der Frage und der Trivia enthalten.
            Die Optionen sollten KEINE Buchstaben (A, B, C...) oder Nummerierungen enthalten.
            Die Trivia sollte 3 bis 4 Sätze lang sein und detaillierte Informationen über den Künstler, das Album oder die Songs liefern.
            Die Frage sollte im JSON-Format zurückgegeben werden mit 'question', 'options', 'correctAnswer' und 'trivia'.
            """

            for attempt in range(retries):
                try:
                    response = openai.ChatCompletion.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are a helpful trivia question generator."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=1200,
                        temperature=0.7
                    )

                    raw_content = response['choices'][0]['message']['content'].strip()
                    print(f"OpenAI's response for {difficulty}-questions from category '{selected_category}':\n{raw_content}")

                    trivia_json = extract_json_from_response(raw_content)

                    if trivia_json and isinstance(trivia_json, dict):
                        questions[difficulty].append(trivia_json)
                        break  # Successful attempt, move to the next question
                    else:
                        print(f"Invalid or empty JSON data for {difficulty}-questions from category '{selected_category}'.")

                except Exception as e:
                    print(f"Error calling OpenAI (attempt {attempt + 1} of {retries}): {e}")
                    if attempt < retries - 1:
                        time.sleep(5)
                    else:
                        print(f"Giving up after {retries} attempts.")

    return questions

def load_existing_json(json_file):
    """
    Loads the existing trivia data from the given JSON file.

    Args:
        json_file (str): The path to the JSON file containing the trivia data.

    Returns:
        list: The existing trivia data, or an empty list if the file did not exist or was empty.
    """
    if not os.path.exists(json_file):
        return []

    with open(json_file, 'r') as file:
        try:
            # Load the JSON data from the file
            return json.load(file)
        except json.JSONDecodeError:
            # If the file is not valid JSON, return an empty list
            return []

def write_json_data(json_file, trivia_data):
    """
    Writes the given trivia data to the specified JSON file.

    Args:
        json_file (str): The path to the JSON file to write the trivia data to.
        trivia_data (list): The trivia data to write to the JSON file.
    """
    with open(json_file, 'w') as file:
        # Dump the trivia data to the file using the json.dump method
        # The indent parameter is set to 2 to format the JSON with indentation
        # The ensure_ascii parameter is set to False to allow non-ASCII characters
        json.dump(trivia_data, file, indent=2, ensure_ascii=False)
    print(f"JSON-Datei wurde erfolgreich aktualisiert.")

def create_json_format(album_data, genre, json_file="trivia.json"):
    """
    Creates the JSON format for the trivia data based on the given album data.
    """
    # Load the existing trivia data from the JSON file
    trivia_data = load_existing_json(json_file)

    # Iterate over the album data and process each entry
    for entry in album_data:
        # Get the artist, album, and year from the entry
        artist = entry['artist']
        album = entry['album']
        year = entry['year']

        # Check if the album is already in the trivia data
        if (artist, album) in {(entry["artist"], entry["album"]) for entry in trivia_data}:
            print(f"Album '{album}' von {artist} bereits verarbeitet, überspringe.")
            continue

        # Create clean filenames for the artist and album
        clean_artist = clean_filename(artist)
        clean_album = clean_filename(album)

        # Create a new entry in the trivia data
        trivia_data.append({
            "artist": artist,
            "album": album,
            "year": year,
            "coverSrc": None,
            "questions": generate_trivia_for_album(album, artist, year)
        })

        # Write the updated trivia data to the JSON file
        write_json_data(json_file, trivia_data)

def main():
    """
    Main entry point for the script.

    This function reads the given file containing artist, album, and year information,
    generates trivia questions for each album, and writes the trivia data to a JSON file.
    """
    parser = argparse.ArgumentParser(
        description="Musik Trivia Generator",
        epilog="Beispielaufruf: `python top100.py data.txt Klassik`"
    )
    parser.add_argument(
        'file_path',
        type=str,
        help="Pfad zur Textdatei mit Artist - Album - Jahr"
    )
    parser.add_argument(
        'genre',
        type=str,
        help="Genre für das Album-Cover-Verzeichnis"
    )

    args = parser.parse_args()

    albums = read_album_data(args.file_path)

    create_json_format(albums, args.genre)

    print(f"Verarbeitung abgeschlossen.")


if __name__ == "__main__":
    main()
