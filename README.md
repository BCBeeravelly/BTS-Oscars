# BTS-Oscars

**An amazing storytelling and statistical project to uncover the secrets behind the nominations and winners of the Academy Awards.**

This repository explores Oscar categories, such as _Best Picture_, _Best Actor_, _Best Actress_, and _Best Director_.

---

## Overview

This project aims to:

- **Scrape** historical Oscar data (nominees and winners) for Best Actor, Best Actress, and Best Director.

---

## The `scraper.py` Script

**`scraper.py`** is the main script that automates data collection from Wikipedia. It uses Python’s `requests` and `BeautifulSoup` libraries to parse HTML tables.

### What Does It Scrape?

1. **Best Actor**
   - URL: [Academy Award for Best Actor](https://en.wikipedia.org/wiki/Academy_Award_for_Best_Actor#Winners_and_nominees)
   - Scrapes winners and nominees, their films, and the corresponding year.
2. **Best Actress**
   - URL: [Academy Award for Best Actress](https://en.wikipedia.org/wiki/Academy_Award_for_Best_Actress#Winners_and_nominees)
   - Scrapes winners and nominees, their films, and the corresponding year.
3. **Best Director**
   - URL: [Academy Award for Best Director](https://en.wikipedia.org/wiki/Academy_Award_for_Best_Director)
   - Scrapes winners and nominees, their films, and the corresponding year.

### How It Works

1. **Best Pictures Data**: Fortunately, we found the list of Best Pictures Nominees and Awards from [imDB](https://www.imdb.com/list/ls009487211/). However, we manually added a few missing entries.
2. **Requests**: We fetch the Wikipedia pages using `requests.get()`.
3. **BeautifulSoup**: We parse the page’s HTML to find the specific `<table>` elements containing the Oscar data.
4. **Rowspan Handling**: Some rows contain multiple nominees under a single year cell. The script keeps track of the “current year” or “current performer/director” to handle `rowspan`.
5. **Highlight Detection**: We detect winners by checking for a highlight style (e.g., `background:#FAEB86`) in the table row or cell.
6. **Output**: We collect the data in Pandas DataFrames and save them to CSV in a `data` directory.

For the full code, see [scraper.py](scraper.py) in this repository.
