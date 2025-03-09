import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os

# Current Parent Directory
CURRENT_DIR = os.getcwd()

# Data Directory
DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'data'))
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

ACTOR_URL = "https://en.wikipedia.org/wiki/Academy_Award_for_Best_Actor#Winners_and_nominees"
ACTRESS_URL = "https://en.wikipedia.org/wiki/Academy_Award_for_Best_Actress#Winners_and_nominees"
DIRECTOR_URL = "https://en.wikipedia.org/wiki/Academy_Award_for_Best_Director"

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

# Get separate DataFrames
best_actor_df = scrape_acting_category(
    ACTOR_URL,
    "Actor"
)

best_actress_df = scrape_acting_category(
    "ACTRESS_URL",
    "Actress"
)

best_director_df = scrape_best_director()

# Save DataFrames to CSV
best_actor_df.to_csv(os.path.join(DATA_DIR, 'BestActors.csv'), index=False)
best_actress_df.to_csv(os.path.join(DATA_DIR, 'BestActresses.csv'), index=False)
best_director_df.to_csv(os.path.join(DATA_DIR, 'BestDirectors.csv'), index=False)



