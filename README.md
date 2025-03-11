# BTS-Oscars

**An amazing storytelling and statistical project to uncover the secrets behind the nominations and winners of the Academy Awards.**

This repository explores Oscar categories, such as _Best Picture_, _Best Actor_, _Best Actress_, and _Best Director_.

---

## Overview

This project aims to:

- **Scrape** historical Oscar data (nominees and winners) for Best Actor, Best Actress, and Best Director.

---

## The `scraper.py` Script

**`scraper.py`** is the main script that automates the entire data collection and enrichment process. It leverages Python libraries such as `requests`, `BeautifulSoup`, and `pandas` for web scraping and data manipulation. It also integrates external APIs like SerpAPI and Tavily to retrieve additional movie details.

### What Does It Do?

1. **Scrape Wikipedia Data:**

   - **Best Actor & Best Actress:**
     - URLs:
       - [Academy Award for Best Actor](https://en.wikipedia.org/wiki/Academy_Award_for_Best_Actor#Winners_and_nominees)
       - [Academy Award for Best Actress](https://en.wikipedia.org/wiki/Academy_Award_for_Best_Actress#Winners_and_nominees)
     - Extracts nominees and winners along with their films and corresponding years.
     - Handles complex table structures with rowspan elements and detects winners via highlighted styles.
   - **Best Director:**
     - URL: [Academy Award for Best Director](https://en.wikipedia.org/wiki/Academy_Award_for_Best_Director)
     - Extracts nominees, winners, films, and the year information.

2. **Enrich Best Pictures Data:**

   - **Primary BestPictures.csv:**
     - The list of Best Pictures is pre-compiled (with some manual corrections) and stored as `BestPictures.csv` in the `data` directory.
   - **Chunking & Tomatometer Ratings Update:**
     - To comply with API rate limits (100 searches/month per API key), the primary BestPictures dataset is split into 7 chunks.
     - Each chunk (saved as `BestPictures_1.csv`, `BestPictures_2.csv`, …, `BestPictures_7.csv`) is processed to extract the movie description and Rotten Tomatoes rating using SerpAPI.
     - A function then reads all the chunk files and updates the primary dataset’s tomatometer rating based on a unique key (`Const`), ensuring that the original order of the primary dataset is preserved.
   - **Adding Synopsis via Tavily Search:**
     - The script checks whether the primary dataset has a `Synopsis` column. If not, it creates one.
     - For each movie, it formulates a query:  
       `"What is the synopsis of the movie {Title} released in the year {Year} directed by {Directors}?"`
     - It then uses the Tavily Search API to retrieve the synopsis. If a synopsis is not found or an error occurs, `"Not available"` is stored.

3. **Data Output:**
   - All scraped and enriched data is saved as CSV files in the `data` directory.
   - The primary dataset (with updated tomatometer ratings and synopses) is saved as `BestPictures_updated.csv`.

---

### How It Works

- **Web Scraping:**  
  The script uses `requests` and `BeautifulSoup` to fetch and parse Wikipedia pages, handling complex table structures (e.g., using `rowspan` for year grouping) and cleaning text by removing references.

- **API Integration:**
  - **SerpAPI:** Used to extract movie descriptions and Rotten Tomatoes ratings from Google’s knowledge graph.
  - **Tavily Search:** Used to fetch movie synopses by constructing a natural language query.
- **Data Management:**  
  The data is managed with Pandas DataFrames. The primary Best Pictures dataset is split into chunks to work within API limits and later merged back using a unique identifier (`Const`).

- **Error Handling & Rate Limiting:**  
  Each API call is wrapped in try/except blocks to gracefully handle errors (such as API quota limits) and includes random sleep intervals to reduce the risk of overloading APIs.

---

For the full code, see [scraper.py](scraper.py) in this repository.
