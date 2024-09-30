import openai
import json
import re
import os
import requests
import argparse
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from PIL import Image
from io import BytesIO
import time
from requests.exceptions import ConnectionError, Timeout
import random
import discogs_client
from dotenv import load_dotenv  # Import the dotenv package

# Load environment variables from the .env file
load_dotenv()

# Retrieve API keys and secrets from environment variables
openai.api_key = os.getenv('OPENAI_API_KEY')
LASTFM_API_KEY = os.getenv('LASTFM_API_KEY')
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
DISCOGS_API_TOKEN = os.getenv('DISCOGS_API_TOKEN')

# Initialize Spotify client
spotify = Spotify(auth_manager=SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET))

# Initialize Discogs client
discogs_api = discogs_client.Client('MusicTriviaApp', user_token=DISCOGS_API_TOKEN)

def read_album_data(file_path):
    """
    Reads a file containing a list of albums and stores the data in a list of dictionaries.
    Each dictionary contains the artist, album and year of the album.

    The file should contain one album per line. Each line should be in the format:
    "Artist - Album - Year"

    Args:
        file_path (str): The path to the file containing the album list.

    Returns:
        list: A list of dictionaries containing the album data.
    """
    album_data = []
    with open(file_path, 'r') as file:
        lines = file.readlines()

    for line in lines:
        line = line.strip()
        try:
            # Split the line from the last occurrence of ' - ' to separate year from artist/album
            artist_album, year = line.rsplit(' - ', 1)
            artist, album = artist_album.split(' - ', 1)
            album_data.append({
                "artist": artist,
                "album": album,
                "year": year
            })
        except ValueError:
            print(f"Zeile übersprungen (unerwartetes Format): {line}")

    return album_data

def clean_filename(text):
    """
    Replace special characters in a filename with underscores and convert to lower case.

    This function is used to sanitize album titles before using them as filenames for the album covers.

    Args:
        text (str): The filename to be cleaned.

    Returns:
        str: The cleaned filename.
    """
    # Replace special characters with underscores
    cleaned_text = re.sub(r'[^A-Za-z0-9]', '_', text)
    # Convert to lower case
    cleaned_text = cleaned_text.lower()
    return cleaned_text

def get_discogs_album_cover(artist, album):
    """
    Get the album cover image from Discogs.

    This function uses the Discogs API to search for the album and retrieve the cover image.
    If no cover image is found, None is returned.

    Args:
        artist (str): The artist name.
        album (str): The album name.

    Returns:
        str: The URL of the album cover image.
    """
    try:
        # Search for the album on Discogs
        results = discogs_api.search(f'{album}', artist=artist, type='release')
        if results.page(1):  # Check if there are results
            release = results.page(1)[0]  # Get the first release
            # Check if the release has a cover image
            if 'cover_image' in release.data:
                return release.data['cover_image']
    except Exception as e:
        # Log any errors
        print(f"Fehler beim Abrufen des Covers von Discogs: {e}")
    return None

def get_lastfm_album_cover(artist, album):
    """
    Get the album cover image from Last.fm.

    This function uses the Last.fm API to search for the album and retrieve the cover image.
    If no cover image is found, None is returned.

    Args:
        artist (str): The artist name.
        album (str): The album name.

    Returns:
        str: The URL of the album cover image.
    """
    url = f"http://ws.audioscrobbler.com/2.0/?method=album.getinfo&api_key={LASTFM_API_KEY}&artist={artist}&album={album}&format=json"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            try:
                # Parse the JSON response
                data = response.json()
                # Check if the album has a cover image
                if 'album' in data and 'image' in data['album']:
                    # Iterate over the available image sizes
                    for image in data['album']['image']:
                        if image['size'] == 'extralarge':
                            # Return the URL of the largest available image
                            return image['#text']
            except ValueError:
                print(f"Error parsing JSON response from Last.fm for {artist} - {album}")
        else:
            print(f"Error retrieving data from Last.fm for {artist} - {album}. Status Code: {response.status_code}")
    except Exception as e:
        print(f"Error retrieving data from Last.fm: {e}")
    return None

def get_spotify_album_cover(artist, album):
    """
    Get the album cover image from Spotify.

    This function uses the Spotify API to search for the album and retrieve the cover image.
    If no cover image is found, None is returned.

    Args:
        artist (str): The artist name.
        album (str): The album name.

    Returns:
        str: The URL of the album cover image.
    """
    # Search for the album on Spotify
    result = spotify.search(q=f'album:{album} artist:{artist}', type='album')
    if result['albums']['items']:  # Check if there are results
        album_data = result['albums']['items'][0]  # Get the first album
        # Iterate over the images and return the largest one
        for image in album_data['images']:
            return image['url']
    # Return None if no cover image is found
    return None

def download_and_resize_album_cover(cover_url, save_path, size=(300, 300)):
    """
    Downloads the album cover from the given URL and resizes it to the given size.

    Args:
        cover_url (str): The URL of the album cover.
        save_path (str): The path where the resized cover should be saved.
        size (tuple): A tuple containing the new width and height of the cover.

    Returns:
        bool: True if the cover was downloaded and resized successfully, False otherwise.
    """
    try:
        # Request the image from the URL
        response = requests.get(cover_url)
        if response.status_code == 200:
            # Open the image from the response
            img = Image.open(BytesIO(response.content))
            # Convert the image to RGB if it's in RGBA
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            # Resize the image to the given size
            img_resized = img.resize(size, Image.Resampling.LANCZOS)
            # Save the resized image to the given path
            img_resized.save(save_path, format='JPEG')
            print(f"Cover erfolgreich heruntergeladen und skaliert: {save_path}")
        else:
            return False
    except Exception as e:
        print(f"Exception beim Herunterladen des Covers: {e}")
        return False
    return True

def extract_json_from_response(raw_content):
    """
    Extracts the JSON part from the response, even if additional text is present.
    Searches for the first occurrence of a JSON-like structure and ignores other content.
    """
    try:
        # Find the JSON part of the response
        json_pattern = r'\{.*\}'  # Look for a JSON object
        matches = re.findall(json_pattern, raw_content, re.DOTALL)
        if matches:
            for match in matches:
                try:
                    # Try to load the JSON content
                    return json.loads(match)
                except json.JSONDecodeError as e:
                    # If the JSON is invalid, print an error message and continue with the next match
                    print(f"Error loading JSON: {e}, content: {match}")
                    continue
        # If no valid JSON is found, raise an error
        raise ValueError("No valid JSON format found.")
    except Exception as e:
        # If an unexpected error occurs, print an error message
        print(f"Error extracting JSON: {e}")
        return None

def generate_trivia_for_album(album, artist, year, retries=3):
    """
    Generates trivia questions for an album with the given artist, album title, and year.
    The questions are generated by OpenAI's GPT-4o-mini model and are categorized into
    easy, medium, and hard difficulties. The questions are generated in the German language.
    """
    questions = {"easy": [], "medium": [], "hard": []}

    # List of categories to generate questions from
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
         "Albumkonzept und Thematik",  # Neue Kategorie
        "Instrumentierung und Produktionstechniken",  # Neue Kategorie
        "Bedeutende Auftritte",  # Neue Kategorie
        "Reaktionen der Musikpresse",  # Neue Kategorie
        "Einfluss auf die Musikszene",  # Neue Kategorie
        "Kollaborationen mit anderen Künstlern",  # Neue Kategorie
        "Erfolge bei Musikpreisen",  # Neue Kategorie
        "Persönliche Erfahrungen des Künstlers",  # Neue Kategorie
        "Soziale und politische Relevanz",  # Neue Kategorie
        "Musikvideos und visuelle Elemente"  # Neue Kategorie
    ]

    # Shuffle the categories to ensure randomness
    random.shuffle(categories)

    for difficulty in ["easy", "medium", "hard"]:
        used_categories = set()  # Keep track of used categories

        while len(questions[difficulty]) < 3:
            available_categories = [cat for cat in categories if cat not in used_categories]
            if not available_categories:
                print(f"No more available categories for {difficulty}.")
                break
            selected_category = random.choice(available_categories)
            used_categories.add(selected_category)  # Mark category as used

            prompt = f"""
            Erstelle 1 Trivia-Frage auf Deutsch für das Album '{album}' von {artist}, das im Jahr {year} veröffentlicht wurde.
            Die Frage sollte sich auf die Kategorie '{selected_category}' konzentrieren.
            Die Frage sollte vom Schwierigkeitsgrad '{difficulty}' sein.
            Jede Frage MUSS den Namen des Künstlers {artist} und den Titel des Albums '{album}' explizit in der Frage und der Trivia enthalten.
            Die Optionen sollten KEINE Buchstaben (A, B, C...) oder Nummerierungen enthalten.
            Die Trivia sollte 7 bis 8 Sätze lang sein und detaillierte Informationen über den Künstler, das Album oder die Songs liefern.
            Die Frage sollte im JSON-Format zurückgegeben werden mit 'question', 'options', 'correctAnswer' und 'trivia'.
            """

            """
            Call OpenAI's ChatCompletion API to generate trivia questions with the given prompt.
            Retries up to 3 times if an error occurs.
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

                    # Extract JSON data from the response
                    trivia_json = extract_json_from_response(raw_content)

                    if trivia_json and isinstance(trivia_json, dict):  # Ensure it's a dictionary
                        questions[difficulty].append(trivia_json)
                        break  # Successful attempt, break
                    else:
                        print(f"Invalid or empty JSON data for {difficulty}-questions from category '{selected_category}'.")

                except Exception as e:
                    print(f"Error calling OpenAI (attempt {attempt + 1} of {retries}): {e}")
                    if attempt < retries - 1:
                        time.sleep(5)  # Wait before retrying
                    else:
                        print(f"Giving up after {retries} attempts.")

    return questions

def log_missing_cover(artist, album, year, clean_artist, clean_album, genre, log_file="missing_covers.txt"):
    """
    Logs a missing cover image to the specified log file.

    The log entry is in the format:
    <artist> - <album> - <year> - <clean_artist>_<clean_album>.jpg

    :param artist: The artist name.
    :param album: The album name.
    :param year: The album release year.
    :param clean_artist: The cleaned artist name (spaces replaced with underscores).
    :param clean_album: The cleaned album name (spaces replaced with underscores).
    :param genre: The genre of the album (not used in the log entry).
    :param log_file: The log file to write the entry to (defaults to "missing_covers.txt").
    """
    log_entry = f"{artist} - {album} - {year} - {clean_artist}_{clean_album}.jpg\n"
    with open(log_file, 'a') as file:
        file.write(log_entry)
    print(f"Fehlendes Cover protokolliert: {log_entry.strip()}")

def load_existing_json(json_file):
    """
    Loads the existing trivia data from the given JSON file.

    If the file does not exist or is empty, an empty list is returned.

    :param json_file: The path to the JSON file.
    :return: The loaded trivia data or an empty list if the file does not exist.
    """
    if not os.path.exists(json_file):
        return []

    with open(json_file, 'r') as file:
        try:
            # Try to load the JSON data
            return json.load(file)
        except json.JSONDecodeError:
            # If the file is empty or has invalid JSON data, return an empty list
            return []

def write_json_data(json_file, trivia_data):
    """
    Writes the given trivia data to the specified JSON file.

    :param json_file: The path to the JSON file.
    :param trivia_data: The trivia data to write to the file.
    """
    with open(json_file, 'w') as file:
        json.dump(trivia_data, file, indent=2, ensure_ascii=False)
    print(f"JSON-Datei wurde erfolgreich aktualisiert.")

def create_json_format(album_data, genre, cover_directory="bandcover", log_file="missing_covers.txt", json_file="trivia.json"):
    """
    Creates the JSON format for the trivia data based on the given album data.

    The function loads the existing trivia data from the given JSON file, processes the given album data,
    downloads the album covers, and saves the data to the JSON file.

    :param album_data: The album data to process.
    :param genre: The genre of the album data.
    :param cover_directory: The directory where the album covers will be saved (defaults to "bandcover").
    :param log_file: The log file where the missing covers will be recorded (defaults to "missing_covers.txt").
    :param json_file: The JSON file where the trivia data will be saved (defaults to "trivia.json").
    """
    # Load the existing trivia data from the given JSON file
    trivia_data = load_existing_json(json_file)

    # Create the log file if it does not exist
    if not os.path.exists(log_file):
        with open(log_file, 'w') as file:
            file.write("Fehlende Cover:\n")

    # Create the cover directory if it does not exist
    if not os.path.exists(cover_directory):
        os.makedirs(cover_directory)

    # Create the genre directory if it does not exist
    genre_directory = f"{cover_directory}/{genre}"
    if not os.path.exists(genre_directory):
        os.makedirs(genre_directory)

    # Process the album data
    for entry in album_data:
        artist = entry['artist']
        album = entry['album']
        year = entry['year']

        # Check if the album is already in the trivia data
        if (artist, album) in {(entry["artist"], entry["album"]) for entry in trivia_data}:
            print(f"Album '{album}' von {artist} bereits verarbeitet, überspringe.")
            continue

        # Clean the artist and album names
        clean_artist = clean_filename(artist)
        clean_album = clean_filename(album)

        # Create the cover path
        cover_path = f"{cover_directory}/{genre}/{clean_artist}_{clean_album}.jpg"

        # Get the cover URL from different sources
        cover_url = get_lastfm_album_cover(artist, album)
        if cover_url:
            print(f"Cover von Last.fm für '{album}' von {artist} gefunden.")
        if not cover_url:
            cover_url = get_spotify_album_cover(artist, album)
            if cover_url:
                print(f"Cover von Spotify für '{album}' von {artist} gefunden.")
        if not cover_url:
            cover_url = get_discogs_album_cover(artist, album)
            if cover_url:
                print(f"Cover von Discogs für '{album}' von {artist} gefunden.")

        # Download and resize the cover
        if cover_url:
            success = download_and_resize_album_cover(cover_url, cover_path)
            if not success:
                log_missing_cover(artist, album, year, clean_artist, clean_album, genre, log_file)
        else:
            log_missing_cover(artist, album, year, clean_artist, clean_album, genre, log_file)

        # Add the trivia data to the list
        trivia_data.append({
            "artist": artist,
            "album": album,
            "year": year,
            "coverSrc": cover_path if cover_url else None,
            "questions": generate_trivia_for_album(album, artist, year)
        })

        # Save the trivia data to the JSON file
        write_json_data(json_file, trivia_data)

def main():
    """Main entry point for the script.

    This function parses the command-line arguments, reads the album data from the given file,
    and calls the `create_json_format` function to generate the JSON format.
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
