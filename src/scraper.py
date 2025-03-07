import requests
from bs4 import BeautifulSoup
import pandas as pd

def scrape_best_picture():
    """Scrapes Best Picture nominees and winners from Wikipedia"""
    url = "https://en.wikipedia.org/wiki/Academy_Award_for_Best_Picture"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    tables = soup.find_all('table', {'class': 'wikitable'})
    
    all_data = []
    
    for table in tables:
        headers = [th.get_text(strip=True) for th in table.find_all('th')]
        if "Year of Film Release" not in headers:
            continue

        current_year = None

        for row in table.find_all('tr'):
            year_th = row.find('th', {'rowspan': True})
            if year_th:
                # Grab the raw year text (e.g., "1927/28 (1st)" or "1927/28[1]")
                year_text = year_th.get_text(strip=True)
                # Remove any bracketed references or parentheses
                year_text = year_text.split('[')[0].split('(')[0].strip()

                if '/' in year_text:
                    # Example: "1927/28" → split('/')[-1] = "28"
                    second_half = year_text.split('/')[-1]
                    year_text = '19' + second_half  # "1928"

                current_year = year_text

            tds = row.find_all('td')
            if len(tds) >= 2:
                # Winner detection (old highlight style in Wikipedia)
                is_winner = 'background:#FAEB86' in row.get('style', '')

                film = tds[0].get_text(strip=True)
                film = film.split('[')[0].strip()

                all_data.append({
                    'Year': current_year,
                    'Film': film,
                    'Winner': is_winner
                })

    df = pd.DataFrame(all_data)

    # Convert 'Year' to integer
    df['Year'] = df['Year'].astype(int)
    
    # Write to CSV (optional)
    df.to_csv('best_picture.csv', index=False)
    return df

if __name__ == "__main__":
    best_picture_data = scrape_best_picture()
    print(best_picture_data)
