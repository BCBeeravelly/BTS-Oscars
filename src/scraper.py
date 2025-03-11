import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os
import time
import random
from dotenv import load_dotenv

load_dotenv()

from serpapi.google_search import GoogleSearch
from tavily import TavilyClient

import logging
logging.basicConfig(level=logging.INFO)


# Current Parent Directory
CURRENT_DIR = os.getcwd()

# Data Directory
DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'data'))
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

ACTOR_URL = "https://en.wikipedia.org/wiki/Academy_Award_for_Best_Actor#Winners_and_nominees"
ACTRESS_URL = "https://en.wikipedia.org/wiki/Academy_Award_for_Best_Actress#Winners_and_nominees"
DIRECTOR_URL = "https://en.wikipedia.org/wiki/Academy_Award_for_Best_Director"
MAIN_CSV = os.path.join(DATA_DIR, 'BestPictures_updated.csv')

# Import BestPictures.csv
best_picture_df = pd.read_csv(os.path.join(DATA_DIR, 'BestPictures.csv'))

def scrape_acting_category(category_url, category_name):
    """Scrapes acting nominees/winners from Wikipedia for specified category"""
    response = requests.get(category_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    tables = soup.find_all('table', {'class': ['wikitable', 'sortable']})
    if not tables:
        raise ValueError(f"{category_name} tables not found")
    
    data = []
    
    for table in tables:
        current_year = None
        current_performer = None
        current_winner = False
        performer_remaining = 0

        for row in table.find_all('tr'):
            # Skip header rows and empty rows
            if row.find('th', {'scope': 'col'}) or not row.find_all('td'):
                continue
            
            # Year handling
            year_th = row.find('th', {'scope': 'row', 'rowspan': True})
            if year_th:
                current_year = re.sub(r'\s*[\(\[](.*?)[\)\]]', '', 
                                     year_th.get_text(strip=True))
                current_performer = None
                current_winner = False
            
            tds = row.find_all('td')
            if not tds:
                continue

            # Performer detection
            first_td = tds[0]
            if first_td.find('a', href=re.compile(r'/wiki/')) or first_td.get('rowspan'):
                current_performer = re.sub(r'[\†‡※]|\[.*?\]', '', 
                                         first_td.get_text(strip=True))
                performer_remaining = int(first_td.get('rowspan', 1)) - 1
                current_winner = 'background:#FAEB86' in first_td.get('style', '')
            elif performer_remaining > 0:
                performer_remaining -= 1
            else:
                current_performer = None
                current_winner = False

            # Film detection with safety checks
            film = None
            if len(tds) >= 3:  # Film is typically in 3rd column
                film = tds[2].get_text(strip=True)
            else:  # Fallback to italicized text
                film_td = row.find('td', string=re.compile(r'.+'))
                if film_td:
                    film = film_td.get_text(strip=True)
            
            if current_year and current_performer and film:
                data.append({
                    'Year': current_year,
                    category_name: current_performer,
                    'Film': film.strip('"'),
                    'Winner': current_winner
                })
    
    return pd.DataFrame(data).reset_index(drop=True)

def scrape_best_director():
    """Scrapes Best Director nominees and winners from Wikipedia"""
    response = requests.get(DIRECTOR_URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    tables = soup.find_all('table', {'class': 'wikitable'})
    if not tables:
        raise ValueError("Best Director tables not found on Wikipedia page")
    
    data = []
    
    for table in tables:
        current_year = None

        for row in table.find_all('tr'):
            # Skip header rows (the column headers)
            if row.find('th', {'scope': 'col'}):
                continue
            
            # Look for a <th> that has a rowspan attribute (the 'Year' cell).
            # Remove {'scope': 'row'} because some rows after 2020/21 do NOT have it.
            year_th = row.find('th', {'rowspan': True})
            if year_th:
                # Clean out parentheses, bracketed references, etc.
                raw_year = year_th.get_text(strip=True)
                # Remove bracketed or parenthetical text like "(93rd)" or "[108]"
                raw_year = re.sub(r'\s*[\(\[](.*?)[\)\]]', '', raw_year)
                raw_year = re.sub(r'\[.*?\]', '', raw_year).strip()
                current_year = raw_year

            tds = row.find_all('td')
            if len(tds) < 2:
                continue

            # Extract director and film
            director = tds[0].get_text(strip=True)
            film = tds[1].get_text(strip=True)
            
            # Clean out references/special characters in director name
            director = re.sub(r'\s*\(.*?\)$', '', director)  # remove trailing parentheses
            director = re.sub(r'[\†‡※]|\[.*?\]', '', director)
            
            # Clean out references in film
            film = re.sub(r'\[.*?\]', '', film)
            
            # Detect winners by checking if the row or these cells have a highlight style
            is_winner = any('background:#FAEB86' in str(element) 
                            for element in [row, tds[0], tds[1]])

            if current_year and director and film:
                data.append({
                    'Year': current_year,
                    'Director': director.strip(),
                    'Film': film.strip(),
                    'Winner': is_winner
                })
    
    df = pd.DataFrame(data)
    # Drop duplicates, just in case the table had repeated entries
    df = df.reset_index(drop=True)
    return df

def scrape_tomatometer_synopsis(df):
    descriptions = []
    tomatometer_ratings = []
    
    for index, row in df.iterrows():
        movie_name = row['Title']
        directors = row['Directors']
        year = row['Year']
        
        query = f"{movie_name} {year} by {directors}"
        
        try:
            params = {
                'q': query,
                'location': 'United States',
                'hl': 'en',
                'gl': 'us',
                'google_domain': 'google.com',
                'api_key': os.getenv('SERP_API_KEY'),
                'num': 1
            }
            
            # Execute Search
            search = GoogleSearch(params)
            results = search.get_dict()
            
            # Extract Knowledge Graph
            knowledge_graph = results.get('knowledge_graph', {})
            
            # Get Description
            desc = knowledge_graph.get('description', 'Not Available')
            descriptions.append(desc)
            
            # Get Tomatometer Rating
            tomato_rating = None
            for er in knowledge_graph.get('editorial_reviews', []):
                if 'Rotten Tomatoes' in er.get('title', ""):
                    tomato_rating = er.get('rating', 'Not Available')
                    break
            tomatometer_ratings.append(tomato_rating)
            print(f'{movie_name}: {desc}, {tomato_rating}, {directors}, {year}')
            # Maintain API health
            time.sleep(random.uniform(1, 3))
        except Exception as e:
            logging.error(f'Failed for {movie_name}: {str(e)}')
            descriptions.append(None)
            tomatometer_ratings.append(None)
            
            # Check for API limit error
            if 'quota' in str(e).lower():
                logging.warning(f'API limit reached for {movie_name}. Stopping further requests.')
                break
            continue
        
    return df.assign(description=descriptions, tomatometer_rating=tomatometer_ratings)

def update_main_tomatometer_ratings(chunk_paths, key='Const', rating_col='tomatometer_rating'):
    """
    Updates the 'tomatometer_rating' column in the primary dataset (BestPictures.csv)
    using the values from the chunk CSV files. Each CSV contains a 'Const' column which
    serves as the primary key.

    Parameters:
      - main_csv_path: Path to the primary CSV file.
      - chunk_paths: A list of paths to the chunk CSV files (e.g., BestPictures_1.csv, BestPictures_2.csv, ...).
      - key: The column name to use as the primary key (default 'Const').
      - rating_col: The column containing the tomatometer rating (default 'tomatometer_rating').

    Returns:
      - A pandas DataFrame with the updated tomatometer_rating values.
    """
    # Read the primary DataFrame (order preserved)
    if rating_col not in best_picture_df.columns:
        best_picture_df[rating_col] = None
    
    # Build a dictionary mapping the key to its tomatometer_rating from the chunks
    rating_dict = {}
    for chunk_file in chunk_paths:
        chunk_df = pd.read_csv(chunk_file)
        # Ensure the necessary columns exist
        if key in chunk_df.columns and rating_col in chunk_df.columns:
            for _, row in chunk_df.iterrows():
                const_val = row[key]
                rating_val = row[rating_col]
                # Only update if a valid rating exists
                if pd.notna(rating_val):
                    rating_dict[const_val] = rating_val
    
    # Use pandas Series.map to update the rating column in the primary DataFrame
    # combine_first keeps any rating already present in main_df if not updated
    best_picture_df[rating_col] = best_picture_df[key].map(rating_dict).combine_first(best_picture_df[rating_col])
    
    return best_picture_df

def add_synopsis_column():
    """
    Adds a 'Synopsis' column to the primary BestPictures DataFrame using the Tavily Search API.
    
    This function:
      1. Checks if the 'Synopsis' column exists; if not, it creates one.
      2. Initializes the Tavily client.
      3. For each movie, constructs a query in the format:
         "What is the synopsis of the movie {Title} released in the year {Year} directed by {Directors}?"
      4. Uses the Tavily API to retrieve the synopsis and updates the DataFrame.
      5. Handles exceptions by setting the synopsis to 'Not available'.
      6. Saves the updated DataFrame to the primary CSV file.
    
    Returns:
        bool: True if the update was successful, False otherwise.
    """
    try:
        # Check and create the Synopsis column if missing
        if 'Synopsis' not in best_picture_df.columns:
            best_picture_df['Synopsis'] = None
        
        # Initialize Tavily client using the API key from the environment
        tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        
        # Process each movie row
        for index, row in best_picture_df.iterrows():
            if pd.isna(row['Synopsis']) or row['Synopsis'] in ['Not available', None]:
                query = (
                    f"What is the synopsis of the movie {row['Title']} "
                    f"released in the year {row['Year']} "
                    f"directed by {row['Directors']}"
                )
                
                try:
                    # Perform the search using Tavily
                    result = tavily.search(
                        query=query,
                        search_depth="basic",
                        include_answer=True
                    )
                    
                    # Extract the synopsis from the result
                    synopsis = result.get('answer', 'Not available')
                    
                    # Clean and truncate the synopsis if available
                    if synopsis != 'Not available':
                        synopsis = synopsis.split("...")[0] + "..."
                        synopsis = synopsis.replace("  ", " ").strip()
                        
                    best_picture_df.at[index, 'Synopsis'] = synopsis
                    logging.info(f"Processed {row['Title']} ({row['Year']})")
                    
                except Exception as e:
                    logging.error(f"Failed for {row['Title']}: {str(e)}")
                    best_picture_df.at[index, 'Synopsis'] = 'Not available'
                
                # Respect rate limits by sleeping a short random interval
                time.sleep(random.uniform(1, 2.5))
        
        # Save the updated DataFrame back to the primary CSV file
        best_picture_df.to_csv(MAIN_CSV, index=False)
        logging.info("Successfully updated synopsis column")
        return True
        
    except Exception as e:
        logging.error(f"Critical error: {str(e)}")
        return False            

# Usage example:
if __name__ == "__main__":
    # Get separate DataFrames
    # best_actor_df = scrape_acting_category(
    #     ACTOR_URL,
    #     "Actor"
    # )

    # best_actress_df = scrape_acting_category(
    #     ACTRESS_URL,
    #     "Actress"
    # )

    # best_director_df = scrape_best_director()

    # Save DataFrames to CSV
    # best_actor_df.to_csv(os.path.join(DATA_DIR, 'BestActors.csv'), index=False)
    # best_actress_df.to_csv(os.path.join(DATA_DIR, 'BestActresses.csv'), index=False)
    # best_director_df.to_csv(os.path.join(DATA_DIR, 'BestDirectors.csv'), index=False)



    # # Split BestPicture DataFrame into separate DataFrames
    # # Each dataframe shall consist of 100 entries and the 7th and final dataframe will contain 11 entries
    # # The splitting is done to utilize the 100 searches/month limit of the API

    # # Split the DataFrame into chunks of 100 rows each
    # chunk_size = 100
    # chunks = [best_picture_df[i:i + chunk_size] for i in range(0, len(best_picture_df), chunk_size)]
    # # Save each chunk to a separate CSV file
    # for i, chunk in enumerate(chunks):
    #     chunk.to_csv(os.path.join(DATA_DIR, f'BestPictures_{i+1}.csv'), index=False)
    # # Save the last chunk with 11 entries
    # last_chunk = best_picture_df[len(best_picture_df)-11:]
    # last_chunk.to_csv(os.path.join(DATA_DIR, 'BestPictures_7.csv'), index=False)

    # # Get the chunk
    # chunk = pd.read_csv(os.path.join(DATA_DIR, 'BestPictures_7.csv'))

    # # Scrape tomatometer and synopsis
    # chunk = scrape_tomatometer_synopsis(chunk)
    # # Save the chunk
    # chunk.to_csv(os.path.join(DATA_DIR, 'BestPictures_7.csv'), index=False)
    # List of chunk files
    # chunk_files = [
    #     os.path.join(DATA_DIR, 'BestPictures_1.csv'),
    #     os.path.join(DATA_DIR, 'BestPictures_2.csv'),
    #     os.path.join(DATA_DIR, 'BestPictures_3.csv'),
    #     os.path.join(DATA_DIR, 'BestPictures_4.csv'),
    #     os.path.join(DATA_DIR, 'BestPictures_5.csv'),
    #     os.path.join(DATA_DIR, 'BestPictures_6.csv'),
    #     os.path.join(DATA_DIR, 'BestPictures_7.csv')
    # ]
    
    # # Update the main DataFrame with tomatometer ratings from the chunks
    # updated_df = update_main_tomatometer_ratings(chunk_files)
    
    # Save the updated DataFrame (this preserves the original order)
    # updated_df.to_csv(os.path.join(DATA_DIR, 'BestPictures.csv'), index=False)
    add_synopsis_column()