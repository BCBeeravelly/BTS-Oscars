import pandas as pd
import os

# Current Directory
CURRENT_DIR = os.getcwd()

# Data Directory
DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'data'))

# Data paths
ACTORS_DATA = os.path.join(DATA_DIR, 'BestActors.csv')
ACTRESSES_DATA = os.path.join(DATA_DIR, 'BestActresses.csv')
DIRECTORS_DATA = os.path.join(DATA_DIR, 'BestDirectors.csv')
MOVIES_DATA = os.path.join(DATA_DIR, 'BestPictures_updated.csv')

def handle_columns(data_path = MOVIES_DATA):
    """
    This function removes redundant columns, renames the columns of the data and handles the data in a needed format.
    """
    
    data = pd.read_csv(data_path)
    
    # Drop columns
    try:
        data.drop(columns = ['Position', 'Created', 'Modified', 'Original Title', 'Title Type', 'Num Votes', 'Release Date'], inplace = True)
        
    except KeyError:
        print('Columns have already been removed or do not exist.')
        
    # Rename columns
    try:
        data.rename(columns = {'Const': 'id', 'IMDb Rating': 'IMDb', 'Runtime (mins)': 'Runtime', 'tomatometer_rating': 'Tomatometer'}, inplace = True)
    except KeyError:
        print('Columns have already been renamed or do not exist.')
        
    # Convert Tomatometer to float
    # Ex: 96% -> 9.6
    try:
        data['Tomatometer'] = data['Tomatometer'].str.replace('%', '').astype(float) / 10
    except KeyError:
        print('Tomatometer column does not exist.')
    except AttributeError:
        print('Tomatometer column is already in float format.')
        
    print('Columns have been handled.')
    
    # Rewrite the data in Description columns
    # If the value is NaN, replace it with False.
    # If the value is not NaN, replace it with True.
    try:
        data['Description'] = data['Description'].notnull()
    except KeyError:
        print('Description column does not exist.')
    
    data.to_csv(data_path, index = False)
    print('Movies Data has been saved.')

def mapping_id(actors_path = ACTORS_DATA, actresses_path = ACTRESSES_DATA, directors_path = DIRECTORS_DATA, movies_path = MOVIES_DATA):
    """
    This function maps the movies id to the actors, actresses and directors data.
    """
    
    actors_df = pd.read_csv(actors_path)
    actresses_df = pd.read_csv(actresses_path)
    directors_df = pd.read_csv(directors_path)
    movies_df = pd.read_csv(movies_path)
    
    # Create a mapping from (Title, Year) to movie_id
    movie_id_map = movies_df.set_index(['Title', 'Year'])['id'].to_dict()
    
    # Add the movie_id column to actos, actresses and directors data
    actors_df['movie_id'] = actors_df.apply(lambda row: movie_id_map.get((row['Film'], row['Year'])), axis = 1)
    actresses_df['movie_id'] = actresses_df.apply(lambda row: movie_id_map.get((row['Film'], row['Year'])), axis = 1)
    directors_df['movie_id'] = directors_df.apply(lambda row: movie_id_map.get((row['Film'], row['Year'])), axis = 1)
    
    # Reorder the columns to place movie_id at the beginning
    actor_columns = ['movie_id'] + [col for col in actors_df.columns if col != 'movie_id']
    actors_df = actors_df[actor_columns]
    
    actress_columns = ['movie_id'] + [col for col in actresses_df.columns if col != 'movie_id']
    actresses_df = actresses_df[actress_columns]
    
    director_columns = ['movie_id'] + [col for col in directors_df.columns if col != 'movie_id']
    directors_df = directors_df[director_columns]
    
    # Save the data
    actors_df.to_csv(actors_path, index = False)
    actresses_df.to_csv(actresses_path, index = False)
    directors_df.to_csv(directors_path, index = False)
    
def split_rows(data_path = DIRECTORS_DATA):
    '''
    Few movies are directed by multiple directors. This function splits the rows for each director.
    '''
    directors_df = pd.read_csv(data_path)
    
    # Explode the rows
    directors_df['Director'] = directors_df['Director'].str.split(', ')
    directors_df = directors_df.explode('Director', ignore_index=True)
    
    # Save the data
    directors_df.to_csv(data_path, index = False)

    

    
    
    