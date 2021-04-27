# FinalProjectW21
This program allows users to explore the word usage in news articles related to different topics.

This script makes use of two API's which require authentication. For the program to run without modification, users should create a 'secrets.py' file in the same folder that the main script resides. 

Merriam Webster API (Free) https://dictionaryapi.com/
Store as 'wordkey' in 'secrets.py'

New York Times API (Free) https://developers.nytimes.com/
Store as 'nytimes' in 'secrets.py'

The program requires the following built-in packages:
requests, json, webbrowser

The program requires the following additional packages
bs4 (https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
numpy (https://numpy.org/)
plotly.graph_objects (https://plotly.com/python/graph-objects/)
