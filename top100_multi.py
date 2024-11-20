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

def generate_trivia_for_album(album, artist, year, language='de', retries=3):
    """
    Generates trivia questions for an album in the specified language.

    :param album: The title of the album
    :param artist: The artist of the album
    :param year: The release year of the album
    :param language: Language code (e.g. 'de' or 'en')
    :param retries: Number of retries for API calls
    :return: Dictionary with trivia questions
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
            Erstelle 1 realistische und gut recherchierte Trivia-Frage auf {language} für das Album '{album}' von {artist} aus dem Jahr {year}.

            Die Frage MUSS:
            1. Sich auf die Kategorie '{selected_category}' konzentrieren
            2. Dem Schwierigkeitsgrad '{difficulty}' entsprechen
            3. Variabel formuliert sein mit abwechslungsreicher Satzstruktur
            4. Den Künstlernamen "{artist}" und Albumtitel "{album}" explizit enthalten
            5. Auf ECHTEN, VERIFIZIERBAREN FAKTEN basieren

            Schwierigkeitsgrade:
            - EASY: Grundlegende, leicht recherchierbare Fakten (z.B. Singles, Chartplatzierungen, bekannte Songs)
            - MEDIUM: Detailliertere Informationen (z.B. Aufnahmeprozess, beteiligte Musiker, musikalische Besonderheiten)
            - HARD: Spezifisches Expertenwissen (z.B. technische Details, historischer Kontext, kulturelle Bedeutung)

            WICHTIG für die Antwortoptionen:
            - GENAU 4 Optionen
            - Alle Optionen müssen REALISTISCH und PLAUSIBEL sein
            - Falsche Optionen sollten historisch oder faktisch möglich sein
            - KEINE offensichtlich falschen oder absurden Optionen
            - KEINE Buchstaben (A, B, C...) oder Nummerierungen

            Die Trivia-Erklärung MUSS:
            - Die richtige Antwort explizit bestätigen
            - Zusätzliche, relevante Kontextinformationen liefern
            - 2-3 verifizierbare Fakten enthalten
            - Sich auf das spezifische Album oder den historischen Kontext beziehen
            - 5-6 Sätze lang sein

            Beispiel für eine gute Frage zur Kategorie "Produktion":
            "Welcher innovative Aufnahmetechnik setzte {artist} bei den Studiosessions für '{album}' im Jahr {year} ein?"
            (mit echten technischen Details und realistischen Alternativen)

            Beispiel für eine schlechte Frage:
            "Was war die beste Aufnahme auf dem Album '{album}'?"
            (zu subjektiv und nicht verifizierbar)

            Gib die Antwort im vorgegebenen JSON-Format zurück mit 'question', 'options' (genau 4), 'correctAnswer' und 'trivia'.
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

def create_json_format(album_data, output_json_file, language='de'):
    """
    Erstellt das JSON-Format für die Trivia-Daten mit Platzhaltern für Metadaten.
    """
    trivia_data = load_existing_json(output_json_file)

    for entry in album_data:
        artist = entry['artist']
        album = entry['album']
        year = entry['year']

        # Überprüfe ob Album bereits existiert
        if (artist, album) in {(entry["artist"], entry["album"]) for entry in trivia_data}:
            print(f"Album '{album}' von {artist} bereits verarbeitet, überspringe.")
            continue

        # Erstelle den Basis-Dateinamen für das Cover
        decade = f"{year[:3]}0er"  # z.B. "195" + "0er" = "1950er"
        cover_filename = f"{clean_filename(artist)}_{clean_filename(album)}.jpg"
        cover_path = f"/bandcover/{decade}/{cover_filename}"

        # Erstelle den neuen Eintrag mit Platzhaltern für die Links
        new_entry = {
            "artist": artist,
            "album": album,
            "year": year,
            "coverSrc": cover_path,
            "spotify_link": "",
            "deezer_link": "",
            "apple_music_link": "",
            "preview_link": "",
            "questions": generate_trivia_for_album(album, artist, year, language)
        }

        trivia_data.append(new_entry)
        write_json_data(output_json_file, trivia_data)

def process_files_in_directory(input_dir, output_json_dir, finished_dir, language='de'):
    """
    Verarbeitet alle Textdateien im Eingabeverzeichnis.
    """
    if not os.path.exists(output_json_dir):
        os.makedirs(output_json_dir)
    if not os.path.exists(finished_dir):
        os.makedirs(finished_dir)

    for filename in sorted(os.listdir(input_dir)):
        if filename.endswith(".txt"):
            input_file_path = os.path.join(input_dir, filename)
            genre_name = re.sub(r'^top100_|_albums$', '', os.path.splitext(filename)[0])
            output_json_file = os.path.join(output_json_dir, f"{genre_name}.json")

            print(f"Processing file: {filename} for language: {language}")
            album_data = read_album_data(input_file_path)
            create_json_format(album_data, output_json_file, language)

            if os.path.exists(input_file_path):
                shutil.move(input_file_path, os.path.join(finished_dir, filename))
                print(f"File '{filename}' has been moved to the 'finished' directory.")

def main():
    parser = argparse.ArgumentParser(
        description="Musik Trivia Generator",
        epilog="Beispielaufruf: `python top100.py 100txt jsons finished --languages de,en,es,fr,it`"
    )
    parser.add_argument('input_dir', type=str, help="Pfad zum Verzeichnis, das die Textdateien enthält")
    parser.add_argument('output_json_dir', type=str, help="Pfad zum Verzeichnis, in dem die JSON-Dateien gespeichert werden sollen")
    parser.add_argument('finished_dir', type=str, help="Pfad zum Verzeichnis, in das die abgearbeiteten Textdateien verschoben werden")
    parser.add_argument('--languages', type=str, default='de', help="Komma-separierte Liste der Sprachen (z.B. de,en,es,fr,it)")

    args = parser.parse_args()

    # Sprachcode-Mapping
    language_mapping = {
        'Deutsch': 'de',
        'Englisch': 'en',
        'Spanisch': 'es',
        'Französisch': 'fr',
        'Italienisch': 'it',
        'German': 'de',
        'English': 'en',
        'Spanish': 'es',
        'French': 'fr',
        'Italian': 'it'
    }

    # Konvertiere Sprachnamen zu Codes
    languages = [language_mapping.get(lang.strip(), lang.strip().lower())
                for lang in args.languages.split(',')]

    for language in languages:
        lang_output_dir = os.path.join(args.output_json_dir, language)
        if not os.path.exists(lang_output_dir):
            os.makedirs(lang_output_dir)

        process_files_in_directory(args.input_dir, lang_output_dir, args.finished_dir, language)

if __name__ == "__main__":
    main()
