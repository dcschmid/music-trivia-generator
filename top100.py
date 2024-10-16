import os
import json
import re
import shutil
import argparse
import random
import openai  # Das OpenAI-Modul für API-Calls importieren
import time  # Importiere das time-Modul
from dotenv import load_dotenv  # Import the dotenv package

# Load environment variables from the .env file
load_dotenv()

# Retrieve API keys and secrets from environment variables
openai.api_key = os.getenv('OPENAI_API_KEY')

def read_album_data(file_path):
    """
    Reads a file containing a list of albums and stores the data in a list of dictionaries.
    Each dictionary contains the artist, album, and year of the album.

    Args:
        file_path (str): The path to the file containing album data.

    Returns:
        list: A list of dictionaries, where each dictionary contains 'artist', 'album', and 'year'.
    """
    album_data = []
    with open(file_path, 'r') as file:
        lines = file.readlines()  # Read all lines from the file

    for line in lines:
        line = line.strip()  # Remove leading and trailing whitespace
        try:
            # Split the line from the last occurrence of ' - ' to separate year from artist/album
            artist_album, year = line.rsplit(' - ', 1)
            # Split the remaining part into artist and album
            artist, album = artist_album.split(' - ', 1)
            # Append the extracted data as a dictionary to the album_data list
            album_data.append({
                "artist": artist,
                "album": album,
                "year": year
            })
        except ValueError:
            # Print a message if the line format is unexpected
            print(f"Zeile übersprungen (unerwartetes Format): {line}")

    return album_data

def extract_json_from_response(raw_content):
    """
    Extracts the JSON part from the response, even if additional text is present.

    Args:
        raw_content (str): The raw content of the response.

    Returns:
        dict or None: The extracted JSON object or None if no valid JSON is found.
    """
    # Look for a JSON object in the response content
    json_pattern = r'\{.*\}'  # Matches any JSON object
    matches = re.findall(json_pattern, raw_content, re.DOTALL)

    if matches:
        # Iterate over each match and try to parse it as JSON
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError as e:
                # If the JSON is not valid, print the error
                print(f"Error loading JSON: {e}, content: {match}")
                continue

    # If no valid JSON is found, raise a ValueError
    raise ValueError("No valid JSON format found.")

def clean_filename(text):
    """
    Replace special characters in a filename with underscores and convert to lower case.

    This function takes a string as argument and replaces all special characters (i.e.
    characters that are not letters or numbers) with underscores and converts the string
    to lower case. This is useful for generating filenames from strings that may contain
    special characters.

    :param text: The string to clean
    :return: The cleaned string
    """
    # Replace all special characters with underscores
    cleaned_text = re.sub(r'[^A-Za-z0-9]', '_', text)
    # Convert the string to lower case
    cleaned_text = cleaned_text.lower()
    return cleaned_text

def generate_trivia_for_album(album, artist, year, retries=3):
    """
    Generates trivia questions for an album with the given artist, album title, and year.
    The questions are categorized into easy, medium, and hard difficulties.

    :param album: The title of the album.
    :param artist: The artist of the album.
    :param year: The release year of the album.
    :param retries: The number of times to retry calling the OpenAI API in case of errors.
    :return: A dictionary with the keys "easy", "medium", and "hard", each containing a list of trivia questions.
    """

    # Initialize the result dictionary
    questions = {"easy": [], "medium": [], "hard": []}

    # Expanded categories list
    categories = [
        "Erfolge und Chartplatzierungen",
        "Songtexte und Bedeutung",
        "Musikalische Elemente",
        "Produktion und Kollaborationen",
        "Hintergrund und interessante Fakten",
        "Historische und kulturelle Bedeutung",
        "Inspirationsquellen des Künstlers",
        "Live-Auftritte und Touren",
        "Kritiken und Rezeption",
        "Musikvideos und visuelle Inhalte",
        "Fan-Reaktionen und Popkultur-Einflüsse",
        "Albumkonzept und Thematik",
        "Instrumentierung und Produktionstechniken",
        "Bedeutende Auftritte",
        "Reaktionen der Musikpresse",
        "Einfluss auf die Musikszene",
        "Kollaborationen mit anderen Künstlern",
        "Erfolge bei Musikpreisen",
        "Persönliche Erfahrungen des Künstlers",
        "Soziale und politische Relevanz",
        "Musikvideos und visuelle Elemente",
        "Stilistische Innovationen",
        "Gesellschaftliche Botschaften",
        "Berühmte Zitate aus dem Album",
        "Aufnahmeprozess",
        "Kontroversen um das Album",
        "Künstlerische Inspirationen",
        "Veröffentlichung und Vermarktung",
        "Internationale Bedeutung",
        "Verlorene Tracks oder unveröffentlichte Musik",
        "Bedeutung der Albumkunst",
        "Albumtitel und seine Bedeutung",
        "Remixes und alternative Versionen",
        "Reaktionen von Kritikern und Fans im Laufe der Zeit",
        "Einfluss auf andere Künstler",
        "Live-Performances bestimmter Songs",
        "Verwendete Aufnahmetechniken",
        "Bedeutung der Track-Reihenfolge",
        "Visuelle Elemente bei Tourneen",
        "Zusammenarbeit mit Produzenten",
        "Rekordverkäufe und Meilensteine",
        "Soziale und politische Themen im Album",
        "Neuinterpretationen oder Coverversionen",
        "Einfluss auf die Mode und Kultur",
        "Nachhaltigkeit und Umweltbewusstsein des Albums",
        "Relevanz in Filmen und TV-Shows",
        "Geheime Botschaften oder versteckte Hinweise in Songs",
        "Einflüsse aus anderen Musikgenres",
        "Persönliche Geschichten der Bandmitglieder",
        "Langfristiger Einfluss auf das Musikgeschäft",
        "Trivia zur ersten Performance bestimmter Songs",
        "Verwendung des Albums in der Werbung",
        "Einfluss auf soziale Bewegungen",
        "Entstehungsgeschichte des Albums",
        "Einfluss auf nachfolgende Musikgenerationen",
        "Produktionstechnische Herausforderungen",
        "Wirtschaftlicher Erfolg und Vermarktung",
        "Gesellschaftlicher Kontext",
        "Entwicklung des Musikstils des Künstlers",
        "Zusätzliche Inhalte und Deluxe-Versionen",
        "Besondere musikalische Arrangements",
        "Reaktionen von Zeitgenossen",
        "Visuelle Elemente und Bühnenshow",
        "Samplings und Referenzen",
        "Technologische Innovationen",
        "Thematische Kontinuität mit früheren Werken",
        "Posthume Bedeutung des Albums",
        "Fandom und Merchandise",
        "Crossover-Erfolg",
        "Aufnahmelocation",
        "Soundtrack-Verwendung",
        "Hörgewohnheiten und Musikkonsum",
        "Wissenschaftliche oder akademische Rezeption",
        "Konzept und Storytelling im Album",
        "Einfluss von Literatur oder Kunst auf das Album",
        "Verwendung in Sportereignissen oder politischen Kampagnen",
        "Kritische Reaktionen auf bestimmte Songs",
        "Ungewöhnliche Kollaborationen oder Gastauftritte",
        "Symbolik in Texten und Artwork",
        "Änderungen in der Bandbesetzung",
        "Finanzielle Kosten der Produktion",
        "Relevanz für bestimmte soziale Bewegungen",
        "Musikalische Rückbesinnung oder Revival",
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
            Die Frage sollte vom Schwierigkeitsgrad '{difficulty}' sein und variabel formuliert sein. Verwende unterschiedliche Satzstrukturen und eine abwechslungsreiche Sprache in jeder Frage.
            Jede Frage MUSS den Namen des Künstlers {artist} und den Titel des Albums '{album}' explizit in der Frage und der Trivia enthalten.
            Die Optionen sollten KEINE Buchstaben (A, B, C...) oder Nummerierungen enthalten.
            Die richtige Antwort muss in der Trivia ausdrücklich erwähnt und erklärt werden. Die Trivia sollte spezifisch auf die richtige Antwort eingehen und detaillierte Informationen dazu geben.
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

    If the file does not exist, an empty list is returned.
    If the file exists but is not a valid JSON file, an empty list is returned.
    """
    if not os.path.exists(json_file):
        # JSON file does not exist, return an empty list
        return []

    with open(json_file, 'r') as file:
        try:
            # Load the JSON data from the file
            return json.load(file)
        except json.JSONDecodeError:
            # JSON file is not valid, return an empty list
            return []

def write_json_data(json_file: str, trivia_data: list) -> None:
    """
    Writes the given trivia data to the specified JSON file.

    :param json_file: The path to the JSON file to write to.
    :param trivia_data: The list of trivia data to write to the file.
    """
    with open(json_file, 'w') as file:
        json.dump(trivia_data, file, indent=2, ensure_ascii=False)
    print(f"JSON-Datei '{json_file}' wurde erfolgreich aktualisiert.")

def create_json_format(album_data, genre, output_json_file):
    """
    Creates the JSON format for the trivia data based on the given album data.

    :param album_data: A list of dictionaries with the album data. Each dictionary should have the keys "artist", "album", and "year".
    :param genre: The genre of the album data. This is used as a key in the JSON data.
    :param output_json_file: The file to write the JSON data to.
    """
    trivia_data = load_existing_json(output_json_file)

    for entry in album_data:
        artist = entry['artist']
        album = entry['album']
        year = entry['year']

        # Check if the album has already been processed
        if (artist, album) in {(entry["artist"], entry["album"]) for entry in trivia_data}:
            print(f"Album '{album}' von {artist} bereits verarbeitet, überspringe.")
            continue

        # Add the album to the trivia data
        trivia_data.append({
            "artist": artist,
            "album": album,
            "year": year,
            # Generate the trivia questions for this album
            "questions": generate_trivia_for_album(album, artist, year)
        })

        # Write the updated trivia data to the JSON file
        write_json_data(output_json_file, trivia_data)

def process_files_in_directory(input_dir, output_json_dir, finished_dir):
    """
    Processes all text files in the specified input directory:
    - Generates trivia for each file
    - Writes the trivia to a corresponding JSON file
    - Moves the processed files to a 'finished' directory

    The output JSON filename is derived from the text file by stripping the
    "top100_" prefix and "_albums" suffix.

    :param input_dir: Directory containing input text files.
    :param output_json_dir: Directory to store output JSON files.
    :param finished_dir: Directory to move processed text files to.
    """
    # Create output and finished directories if they do not exist
    if not os.path.exists(output_json_dir):
        os.makedirs(output_json_dir)
    if not os.path.exists(finished_dir):
        os.makedirs(finished_dir)

    # Sort filenames alphabetically in the input directory
    for filename in sorted(os.listdir(input_dir)):
        if filename.endswith(".txt"):
            input_file_path = os.path.join(input_dir, filename)

            # Extract the genre name by removing specific prefixes and suffixes
            genre_name = re.sub(r'^top100_|_albums$', '', os.path.splitext(filename)[0])

            # Define the path for the output JSON file based on the genre name
            output_json_file = os.path.join(output_json_dir, f"{genre_name}.json")

            print(f"Processing file: {filename}")

            # Read album data from the text file
            album_data = read_album_data(input_file_path)

            # Generate trivia and save it to a JSON file
            create_json_format(album_data, genre_name, output_json_file)

            # Move the processed file to the 'finished' directory
            shutil.move(input_file_path, os.path.join(finished_dir, filename))
            print(f"File '{filename}' has been moved to the 'finished' directory.")

def main():
    """
    Main entry point for the script.

    This function parses command line arguments and calls the process_files_in_directory
    function to generate trivia for the given input files and store it in the specified
    output directory.

    :returns: None
    """
    parser = argparse.ArgumentParser(
        description="Musik Trivia Generator",
        epilog="Beispielaufruf: `python top100.py top100-files JSON finished`"
    )
    parser.add_argument(
        'input_dir',
        type=str,
        help="Pfad zum Verzeichnis, das die Textdateien enthält"
    )
    parser.add_argument(
        'output_json_dir',
        type=str,
        help="Pfad zum Verzeichnis, in dem die JSON-Dateien gespeichert werden sollen"
    )
    parser.add_argument(
        'finished_dir',
        type=str,
        help="Pfad zum Verzeichnis, in das die abgearbeiteten Textdateien verschoben werden"
    )

    args = parser.parse_args()

    # Process the files in the given input directory
    process_files_in_directory(args.input_dir, args.output_json_dir, args.finished_dir)

if __name__ == "__main__":
    main()
