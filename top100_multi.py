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
    """
    questions = {"easy": [], "medium": [], "hard": []}

    # Kategorien je nach Sprache definieren
    categories = get_categories_for_language(language)  # Neue Hilfsfunktion

    # Angepasster Prompt mit sprachspezifischen Anweisungen
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

            prompt = get_language_specific_prompt(  # Neue Hilfsfunktion
                language,
                difficulty,
                selected_category,
                album,
                artist,
                year
            )

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

def get_categories_for_language(language):
    """
    Returns categories in the specified language.
    """
    categories = {
        'de': [
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
        ],
        'en': [
            "Success and Chart Performance",
            "Lyrics and Meaning",
            "Musical Elements",
            "Production and Collaborations",
            "Background and Interesting Facts",
            "Historical and Cultural Significance",
            "Artist's Sources of Inspiration",
            "Live Performances and Tours",
            "Reviews and Reception",
            "Music Videos and Visual Content",
            "Fan Reactions and Pop Culture Impact",
            "Album Concept and Themes",
            "Instrumentation and Production Techniques",
            "Significant Performances",
            "Music Press Reactions",
            "Impact on the Music Scene",
            "Collaborations with Other Artists",
            "Music Award Achievements",
            "Artist's Personal Experiences",
            "Social and Political Relevance",
            "Music Videos and Visual Elements",
            "Stylistic Innovations",
            "Social Messages",
            "Famous Album Quotes",
            "Recording Process",
            "Album Controversies",
            "Artistic Inspirations",
            "Release and Marketing",
            "International Significance",
            "Lost Tracks or Unreleased Music",
            "Album Artwork Significance",
            "Album Title and Its Meaning",
            "Remixes and Alternative Versions",
            "Critic and Fan Reactions Over Time",
            "Influence on Other Artists",
            "Live Performances of Specific Songs",
            "Recording Techniques Used",
            "Track Order Significance",
            "Visual Elements in Tours",
            "Producer Collaborations",
            "Record Sales and Milestones",
            "Social and Political Themes in the Album",
            "Reinterpretations or Cover Versions",
            "Impact on Fashion and Culture",
            "Album's Sustainability and Environmental Awareness",
            "Relevance in Movies and TV Shows",
            "Hidden Messages or Easter Eggs in Songs",
            "Influences from Other Music Genres",
            "Personal Stories of Band Members",
            "Long-term Impact on the Music Industry",
            "First Performance Trivia of Specific Songs",
            "Album Use in Advertising",
            "Impact on Social Movements",
            "Album Origin Story",
            "Influence on Future Music Generations",
            "Production Technical Challenges",
            "Commercial Success and Marketing",
            "Societal Context",
            "Evolution of Artist's Musical Style",
            "Additional Content and Deluxe Versions",
            "Special Musical Arrangements",
            "Contemporary Reactions",
            "Visual Elements and Stage Show",
            "Samples and References",
            "Technological Innovations",
            "Thematic Continuity with Previous Works",
            "Posthumous Significance of the Album",
            "Fandom and Merchandise",
            "Crossover Success",
            "Recording Location",
            "Soundtrack Usage",
            "Listening Habits and Music Consumption",
            "Scientific or Academic Reception",
            "Album Concept and Storytelling",
            "Literature or Art Influence on the Album",
            "Use in Sports Events or Political Campaigns",
            "Critical Reactions to Specific Songs",
            "Unusual Collaborations or Guest Appearances",
            "Symbolism in Lyrics and Artwork",
            "Band Lineup Changes",
            "Production Financial Costs",
            "Relevance to Specific Social Movements",
            "Musical Throwback or Revival"
        ],
        'es': [
            "Éxitos y Posiciones en las Listas",
            "Letras y Significado",
            "Elementos Musicales",
            "Producción y Colaboraciones",
            "Antecedentes y Datos Interesantes",
            "Significado Histórico y Cultural",
            "Fuentes de Inspiración del Artista",
            "Actuaciones en Vivo y Giras",
            "Críticas y Recepción",
            "Videos Musicales y Contenido Visual",
            "Reacciones de Fans e Impacto en la Cultura Pop",
            "Concepto y Temática del Álbum",
            "Instrumentación y Técnicas de Producción",
            "Actuaciones Significativas",
            "Reacciones de la Prensa Musical",
            "Impacto en la Escena Musical",
            "Colaboraciones con Otros Artistas",
            "Logros en Premios Musicales",
            "Experiencias Personales del Artista",
            "Relevancia Social y Política",
            "Videos Musicales y Elementos Visuales",
            "Innovaciones Estilísticas",
            "Mensajes Sociales",
            "Citas Famosas del Álbum",
            "Proceso de Grabación",
            "Controversias del Álbum",
            "Inspiraciones Artísticas",
            "Lanzamiento y Marketing",
            "Significado Internacional",
            "Canciones Perdidas o Música Inédita",
            "Significado del Arte del Álbum",
            "Título del Álbum y su Significado",
            "Remixes y Versiones Alternativas",
            "Reacciones de Críticos y Fans a lo Largo del Tiempo",
            "Influencia en Otros Artistas",
            "Interpretaciones en Vivo de Canciones Específicas",
            "Técnicas de Grabación Utilizadas",
            "Significado del Orden de las Pistas",
            "Elementos Visuales en Giras",
            "Colaboraciones con Productores",
            "Ventas Récord e Hitos",
            "Temas Sociales y Políticos en el Álbum",
            "Reinterpretaciones o Versiones Cover",
            "Impacto en la Moda y la Cultura",
            "Sostenibilidad y Conciencia Ambiental del Álbum",
            "Relevancia en Películas y Programas de TV",
            "Mensajes Ocultos o Huevos de Pascua en las Canciones",
            "Influencias de Otros Géneros Musicales",
            "Historias Personales de los Miembros de la Banda",
            "Impacto a Largo Plazo en la Industria Musical",
            "Curiosidades sobre Primeras Interpretaciones",
            "Uso del Álbum en Publicidad",
            "Impacto en Movimientos Sociales",
            "Historia del Origen del Álbum",
            "Influencia en Generaciones Musicales Futuras",
            "Desafíos Técnicos de Producción",
            "Éxito Comercial y Marketing",
            "Contexto Social",
            "Evolución del Estilo Musical del Artista",
            "Contenido Adicional y Versiones Deluxe",
            "Arreglos Musicales Especiales",
            "Reacciones Contemporáneas",
            "Elementos Visuales y Show en Escena",
            "Samples y Referencias",
            "Innovaciones Tecnológicas",
            "Continuidad Temática con Trabajos Anteriores",
            "Significado Póstumo del Álbum",
            "Fandom y Merchandising",
            "Éxito Crossover",
            "Ubicación de Grabación",
            "Uso en Bandas Sonoras",
            "Hábitos de Escucha y Consumo Musical",
            "Recepción Científica o Académica",
            "Concepto y Narrativa del Álbum",
            "Influencia de Literatura o Arte en el Álbum",
            "Uso en Eventos Deportivos o Campañas Políticas",
            "Reacciones Críticas a Canciones Específicas",
            "Colaboraciones Inusuales o Apariciones Especiales",
            "Simbolismo en Letras y Artwork",
            "Cambios en la Formación de la Banda",
            "Costos Financieros de Producción",
            "Relevancia para Movimientos Sociales Específicos",
            "Retrospectiva o Revival Musical"
        ],
        'fr': [
            "Succès et Classements",
            "Paroles et Signification",
            "Éléments Musicaux",
            "Production et Collaborations",
            "Contexte et Faits Intéressants",
            "Importance Historique et Culturelle",
            "Sources d'Inspiration de l'Artiste",
            "Concerts et Tournées",
            "Critiques et Réception",
            "Clips Vidéo et Contenu Visuel",
            "Réactions des Fans et Impact sur la Culture Pop",
            "Concept et Thèmes de l'Album",
            "Instrumentation et Techniques de Production",
            "Performances Marquantes",
            "Réactions de la Presse Musicale",
            "Impact sur la Scène Musicale",
            "Collaborations avec d'Autres Artistes",
            "Récompenses Musicales",
            "Expériences Personnelles de l'Artiste",
            "Pertinence Sociale et Politique",
            "Clips et Éléments Visuels",
            "Innovations Stylistiques",
            "Messages Sociaux",
            "Citations Célèbres de l'Album",
            "Processus d'Enregistrement",
            "Controverses autour de l'Album",
            "Inspirations Artistiques",
            "Sortie et Marketing",
            "Importance Internationale",
            "Morceaux Perdus ou Inédits",
            "Signification de la Pochette",
            "Titre de l'Album et sa Signification",
            "Remixes et Versions Alternatives",
            "Réactions des Critiques et Fans au Fil du Temps",
            "Influence sur d'Autres Artistes",
            "Performances Live de Chansons Spécifiques",
            "Techniques d'Enregistrement Utilisées",
            "Importance de l'Ordre des Pistes",
            "Éléments Visuels en Tournée",
            "Collaborations avec les Producteurs",
            "Ventes Record et Étapes Importantes",
            "Thèmes Sociaux et Politiques dans l'Album",
            "Réinterprétations ou Reprises",
            "Impact sur la Mode et la Culture",
            "Durabilité et Conscience Environnementale de l'Album",
            "Pertinence dans les Films et Émissions TV",
            "Messages Cachés ou Easter Eggs dans les Chansons",
            "Influences d'Autres Genres Musicaux",
            "Histoires Personnelles des Membres du Groupe",
            "Impact à Long Terme sur l'Industrie Musicale",
            "Anecdotes sur les Premières Performances",
            "Utilisation de l'Album en Publicité",
            "Impact sur les Mouvements Sociaux",
            "Histoire de l'Origine de l'Album",
            "Influence sur les Générations Musicales Futures",
            "Défis Techniques de Production",
            "Succès Commercial et Marketing",
            "Contexte Sociétal",
            "Évolution du Style Musical de l'Artiste",
            "Contenu Supplémentaire et Versions Deluxe",
            "Arrangements Musicaux Spéciaux",
            "Réactions Contemporaines",
            "Éléments Visuels et Mise en Scène",
            "Samples et Références",
            "Innovations Technologiques",
            "Continuité Thématique avec les Œuvres Précédentes",
            "Importance Posthume de l'Album",
            "Fandom et Merchandising",
            "Succès Crossover",
            "Lieu d'Enregistrement",
            "Utilisation dans les Bandes Sonores",
            "Habitudes d'Écoute et Consommation Musicale",
            "Réception Scientifique ou Académique",
            "Concept et Narration de l'Album",
            "Influence de la Littérature ou de l'Art sur l'Album",
            "Utilisation dans les Événements Sportifs ou Campagnes Politiques",
            "Réactions Critiques à des Chansons Spécifiques",
            "Collaborations Inhabituelles ou Apparitions Spéciales",
            "Symbolisme dans les Paroles et l'Artwork",
            "Changements dans la Formation du Groupe",
            "Coûts Financiers de Production",
            "Pertinence pour des Mouvements Sociaux Spécifiques",
            "Retour aux Sources ou Revival Musical"
        ],
        'it': [
            "Successi e Posizioni in Classifica",
            "Testi e Significato",
            "Elementi Musicali",
            "Produzione e Collaborazioni",
            "Background e Fatti Interessanti",
            "Significato Storico e Culturale",
            "Fonti di Ispirazione dell'Artista",
            "Esibizioni dal Vivo e Tour",
            "Critiche e Ricezione",
            "Video Musicali e Contenuti Visivi",
            "Reazioni dei Fan e Impatto sulla Cultura Pop",
            "Concetto e Tematiche dell'Album",
            "Strumentazione e Tecniche di Produzione",
            "Esibizioni Significative",
            "Reazioni della Stampa Musicale",
            "Impatto sulla Scena Musicale",
            "Collaborazioni con Altri Artisti",
            "Successi ai Premi Musicali",
            "Esperienze Personali dell'Artista",
            "Rilevanza Sociale e Politica",
            "Video Musicali ed Elementi Visivi",
            "Innovazioni Stilistiche",
            "Messaggi Sociali",
            "Citazioni Famose dall'Album",
            "Processo di Registrazione",
            "Controversie sull'Album",
            "Ispirazioni Artistiche",
            "Pubblicazione e Marketing",
            "Significato Internazionale",
            "Tracce Perdute o Musica Inedita",
            "Significato della Copertina",
            "Titolo dell'Album e suo Significato",
            "Remix e Versioni Alternative",
            "Reazioni di Critici e Fan nel Tempo",
            "Influenza su Altri Artisti",
            "Performance dal Vivo di Canzoni Specifiche",
            "Tecniche di Registrazione Utilizzate",
            "Significato dell'Ordine delle Tracce",
            "Elementi Visivi nei Tour",
            "Collaborazioni con i Produttori",
            "Vendite Record e Pietre Miliari",
            "Temi Sociali e Politici nell'Album",
            "Reinterpretazioni o Cover",
            "Impatto sulla Moda e sulla Cultura",
            "Sostenibilità e Consapevolezza Ambientale dell'Album",
            "Rilevanza in Film e Programmi TV",
            "Messaggi Nascosti o Easter Egg nelle Canzoni",
            "Influenze da Altri Generi Musicali",
            "Storie Personali dei Membri della Band",
            "Impatto a Lungo Termine sull'Industria Musicale",
            "Curiosità sulle Prime Esibizioni",
            "Utilizzo dell'Album nella Pubblicità",
            "Impatto sui Movimenti Sociali",
            "Storia dell'Origine dell'Album",
            "Influenza sulle Generazioni Musicali Future",
            "Sfide Tecniche di Produzione",
            "Successo Commerciale e Marketing",
            "Contesto Sociale",
            "Evoluzione dello Stile Musicale dell'Artista",
            "Contenuti Aggiuntivi e Versioni Deluxe",
            "Arrangiamenti Musicali Speciali",
            "Reazioni Contemporanee",
            "Elementi Visivi e Show sul Palco",
            "Campionamenti e Riferimenti",
            "Innovazioni Tecnologiche",
            "Continuità Tematica con Opere Precedenti",
            "Significato Postumo dell'Album",
            "Fandom e Merchandising",
            "Successo Crossover",
            "Location di Registrazione",
            "Utilizzo nelle Colonne Sonore",
            "Abitudini di Ascolto e Consumo Musicale",
            "Ricezione Scientifica o Accademica",
            "Concept e Narrazione dell'Album",
            "Influenza della Letteratura o dell'Arte sull'Album",
            "Utilizzo in Eventi Sportivi o Campagne Politiche",
            "Reazioni Critiche a Canzoni Specifiche",
            "Collaborazioni Insolite o Apparizioni Speciali",
            "Simbolismo nei Testi e nell'Artwork",
            "Cambiamenti nella Formazione della Band",
            "Costi Finanziari di Produzione",
            "Rilevanza per Movimenti Sociali Specifici",
            "Ritorno alle Origini o Revival Musicale"
        ]
    }
    return categories.get(language, categories['en'])  # Englisch als Fallback

def get_language_specific_prompt(language, difficulty, category, album, artist, year):
    """
    Returns the prompt in the specified language.
    """
    prompts = {
        'de': f"""
            Erstelle 1 realistische und gut recherchierte Trivia-Frage auf Deutsch für das Album '{album}' von {artist} aus dem Jahr {year}.

            Die Frage MUSS:
            1. Sich auf die Kategorie '{category}' konzentrieren
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
            - Die richtige Antwort in den Kontext einbetten
            - Relevante Hintergrundinformationen liefern
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
            """,
        'en': f"""
            Create 1 realistic and well-researched trivia question in English for the album '{album}' by {artist} from {year}.

            The question MUST:
            1. Focus on the category '{category}'
            2. Match the difficulty level '{difficulty}'
            3. Be variably formulated with diverse sentence structure
            4. Explicitly include the artist name "{artist}" and album title "{album}"
            5. Be based on REAL, VERIFIABLE FACTS

            Difficulty levels:
            - EASY: Basic, easily researchable facts (e.g., singles, chart positions, well-known songs)
            - MEDIUM: More detailed information (e.g., recording process, involved musicians, musical peculiarities)
            - HARD: Specific expert knowledge (e.g., technical details, historical context, cultural significance)

            IMPORTANT for answer options:
            - EXACTLY 4 options
            - All options must be REALISTIC and PLAUSIBLE
            - Wrong options should be historically or factually possible
            - NO obviously wrong or absurd options
            - NO letters (A, B, C...) or numbering

            The trivia explanation MUST:
            - Incorporate the correct answer into the context
            - Provide relevant background information
            - Include 2-3 verifiable facts
            - Relate to the specific album or historical context
            - Be 5-6 sentences long

            Example of a good question for the category "Production":
            "What innovative recording technique did {artist} use during the studio sessions for '{album}' in {year}?"
            (with real technical details and realistic alternatives)

            Example of a bad question:
            "What was the best recording on the album '{album}'?"
            (too subjective and not verifiable)

            Return the answer in the specified JSON format with 'question', 'options' (exactly 4), 'correctAnswer', and 'trivia'.
        """,
        'es': f"""
            Crea 1 pregunta de trivia realista y bien investigada en español para el álbum '{album}' de {artist} del año {year}.

            La pregunta DEBE:
            1. Centrarse en la categoría '{category}'
            2. Coincidir con el nivel de dificultad '{difficulty}'
            3. Estar formulada de manera variable con estructura de oración diversa
            4. Incluir explícitamente el nombre del artista "{artist}" y el título del álbum "{album}"
            5. Basarse en HECHOS REALES Y VERIFICABLES

            Niveles de dificultad:
            - FÁCIL: Hechos básicos, fácilmente investigables (ej., sencillos, posiciones en listas, canciones conocidas)
            - MEDIO: Información más detallada (ej., proceso de grabación, músicos involucrados, peculiaridades musicales)
            - DIFÍCIL: Conocimiento experto específico (ej., detalles técnicos, contexto histórico, significado cultural)

            IMPORTANTE para las opciones de respuesta:
            - EXACTAMENTE 4 opciones
            - Todas las opciones deben ser REALISTAS y PLAUSIBLES
            - Las opciones incorrectas deben ser histórica o factualmente posibles
            - NO opciones obviamente incorrectas o absurdas
            - NO letras (A, B, C...) o numeración

            La explicación de la trivia DEBE:
            - Incorporar la respuesta correcta en el contexto
            - Proporcionar información de fondo relevante
            - Incluir 2-3 hechos verificables
            - Relacionarse con el álbum específico o el contexto histórico
            - Tener 5-6 oraciones

            Ejemplo de una buena pregunta para la categoría "Producción":
            "¿Qué técnica innovadora de grabación utilizó {artist} durante las sesiones de estudio de '{album}' en {year}?"
            (con detalles técnicos reales y alternativas realistas)

            Ejemplo de una mala pregunta:
            "¿Cuál fue la mejor grabación del álbum '{album}'?"
            (demasiado subjetiva y no verificable)

            Devuelve la respuesta en el formato JSON especificado con 'question', 'options' (exactamente 4), 'correctAnswer' y 'trivia'.
        """,
        'fr': f"""
            Créez 1 question de quiz réaliste et bien documentée en français pour l'album '{album}' de {artist} de l'année {year}.

            La question DOIT:
            1. Se concentrer sur la catégorie '{category}'
            2. Correspondre au niveau de difficulté '{difficulty}'
            3. Être formulée de manière variable avec une structure de phrase diverse
            4. Inclure explicitement le nom de l'artiste "{artist}" et le titre de l'album "{album}"
            5. Être basée sur des FAITS RÉELS ET VÉRIFIABLES

            Niveaux de difficulté:
            - FACILE: Faits basiques, facilement vérifiables (ex: singles, classements, chansons connues)
            - MOYEN: Informations plus détaillées (ex: processus d'enregistrement, musiciens impliqués, particularités musicales)
            - DIFFICILE: Connaissances expertes spécifiques (ex: détails techniques, contexte historique, signification culturelle)

            IMPORTANT pour les options de réponse:
            - EXACTEMENT 4 options
            - Toutes les options doivent être RÉALISTES et PLAUSIBLES
            - Les mauvaises options doivent être historiquement ou factuellement possibles
            - PAS d'options manifestement fausses ou absurdes
            - PAS de lettres (A, B, C...) ou de numérotation

            L'explication du quiz DOIT:
            - Intégrer la bonne réponse dans le contexte
            - Fournir des informations contextuelles pertinentes
            - Inclure 2-3 faits vérifiables
            - Se rapporter à l'album spécifique ou au contexte historique
            - Comporter 5-6 phrases

            Exemple d'une bonne question pour la catégorie "Production":
            "Quelle technique d'enregistrement innovante {artist} a-t-il utilisée lors des sessions studio de '{album}' en {year}?"
            (avec des détails techniques réels et des alternatives réalistes)

            Exemple d'une mauvaise question:
            "Quel était le meilleur enregistrement de l'album '{album}'?"
            (trop subjectif et non vérifiable)

            Retournez la réponse au format JSON spécifié avec 'question', 'options' (exactement 4), 'correctAnswer' et 'trivia'.
        """,
        'it': f"""
            Crea 1 domanda di trivia realistica e ben documentata in italiano per l'album '{album}' di {artist} dell'anno {year}.

            La domanda DEVE:
            1. Concentrarsi sulla categoria '{category}'
            2. Corrispondere al livello di difficoltà '{difficulty}'
            3. Essere formulata in modo variabile con struttura della frase diversificata
            4. Includere esplicitamente il nome dell'artista "{artist}" e il titolo dell'album "{album}"
            5. Basarsi su FATTI REALI E VERIFICABILI

            Livelli di difficoltà:
            - FACILE: Fatti base, facilmente verificabili (es. singoli, posizioni in classifica, canzoni famose)
            - MEDIO: Informazioni più dettagliate (es. processo di registrazione, musicisti coinvolti, peculiarità musicali)
            - DIFFICILE: Conoscenze specifiche da esperti (es. dettagli tecnici, contesto storico, significato culturale)

            IMPORTANTE per le opzioni di risposta:
            - ESATTAMENTE 4 opzioni
            - Tutte le opzioni devono essere REALISTICHE e PLAUSIBILI
            - Le opzioni errate devono essere storicamente o fattualmente possibili
            - NESSUNA opzione palesemente errata o assurda
            - NESSUNA lettera (A, B, C...) o numerazione

            La spiegazione della trivia DEVE:
            - Incorporare la risposta corretta nel contesto
            - Fornire informazioni di background pertinenti
            - Includere 2-3 fatti verificabili
            - Riferirsi all'album specifico o al contesto storico
            - Essere composta da 5-6 frasi

            Esempio di una buona domanda per la categoria "Produzione":
            "Quale tecnica di registrazione innovativa ha utilizzato {artist} durante le sessioni in studio per '{album}' nel {year}?"
            (con dettagli tecnici reali e alternative realistiche)

            Esempio di una cattiva domanda:
            "Qual è stata la migliore registrazione dell'album '{album}'?"
            (troppo soggettiva e non verificabile)

            Restituisci la risposta nel formato JSON specificato con 'question', 'options' (esattamente 4), 'correctAnswer' e 'trivia'.
        """
    }
    return prompts.get(language, prompts['en'])  # Englisch als Fallback

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

def process_files_in_directory(input_dir, output_json_dir, finished_dir, language='de', move_files=False):
    """
    Verarbeitet alle Textdateien im Eingabeverzeichnis.

    Args:
        move_files (bool): Gibt an, ob die Dateien nach der Verarbeitung verschoben werden sollen
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

            # Nur verschieben wenn es die letzte Sprache ist
            if move_files and os.path.exists(input_file_path):
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

    for i, language in enumerate(languages):
        lang_output_dir = os.path.join(args.output_json_dir, language)
        if not os.path.exists(lang_output_dir):
            os.makedirs(lang_output_dir)

        # Nur bei der letzten Sprache die Dateien verschieben
        is_last_language = (i == len(languages) - 1)
        process_files_in_directory(args.input_dir, lang_output_dir, args.finished_dir,
                                 language, move_files=is_last_language)

if __name__ == "__main__":
    main()
