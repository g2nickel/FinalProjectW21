#################################
##### Name: Greg Nickel  ########
##### Uniqname: gnickel  ########
#################################

import requests
import json
from bs4 import BeautifulSoup
import numpy as np

import secrets

CACHE_DICT = {}

def cache_loader():
    pass

def cache_saver():
    pass

def article_fetcher(search_keyword):
    """
    For a given search term return a list of up to 10 URL's for related NYT Articles

    Parameter
    ---------
    search_keyword (string)

    Return
    ---------
    url_list (list)
    """

    key = secrets.nytimes
    params = {
        'q' : search_keyword,
        'api-key' : key
    }
    response = requests.get("https://api.nytimes.com/svc/search/v2/articlesearch.json",params=params)
    returned_response = json.loads(response.text)
    url_list = []
    for x in returned_response["response"]["docs"]:
        article_url = x["web_url"]
        url_list.append(article_url)
    return url_list

def article_text_collector(url,cache=CACHE_DICT):
    """
    For a URL, the function checks to see if the story has been cached. It has not
    been cached, the function gets the article, searches for body pargraphs and then
    creates one a single string of the body of the article.

    Parameter
    ---------
    url (string)

    Return
    ---------
    story_text (string)
    """
    try:
        story_text = cache[url]
    except KeyError:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        story = soup.find_all('p', class_='css-axufdj evys1bk0')
        story_text  = ""
        for section in story:
            if section.string is not None:
                story_text += section.string
        cache[url] = story_text
    return story_text

def article_parser(story):

    print(story)

def article_processor(list_of_urls):
    """


    Parameter
    ---------

    Return
    ---------

    """
    if empty:
        pass


def word_classifer(word):

    key = secrets.wordkey
    params= {
         'key' : key
    }
    response = requests.get(f"https://www.dictionaryapi.com/api/v3/references/collegiate/json/{word}",params)
    words = json.loads(response.text)
    print(type(words[0]))
# # for key,val in words[0].items():
# #     print(key + str(type(val)))
# #     print(val)

def proper_noun_classifier():
    pass

def usage_trend(search_word,year_start=1900):
    '''
    Given an word and a start year, the time series data for useage in Ngram/Google Books
    will be collected. A correlation coefficient (Pearson's) will be calcululated.
    The correlation coefficient is translated into a verbal description.
    Words |r|<0.5 are noted as 'flat'
    Words -1<r<-0.8 are 'archaic'
    Words -0.8<r<-0.5 are 'losing popularity'
    Words 0.5<r<0.8 are 'graining popularity'
    words 0.8<r<1.0 are 'trendy'

    Parameters
    ----------
    search_word (String)
    year_start (String/int) default of 1900

    Returns
    -------
    TBD
    '''
    param = {
        'content': search_word,
        'year_start': str(year_start),
        'year_end': "2018",
        "corpus":"26",
    }
    response = requests.get("https://books.google.com/ngrams/json",params=param)
    useage_data = json.loads(response.text)
    time_series = useage_data[0]["timeseries"]

    int_start =int(year_start)
    int_end = 2019

    x = np.arange(int_start,int_end)
    y = np.array(time_series)
    print(len(y))
    print(len(x))
    r = np.corrcoef(x, y)

    print(r[0, 1])





def output_maker():
    pass
    """
    https://books.google.com/ngrams/graph?content=mouse&year_start=1920&year_end=2000&corpus=26&smoothing=3&direct_url=t1%3B%2Cmouse%3B%2Cc0
    """



if __name__ == "__main__":
    pass
    # phase = 0
    # print("Welcome to the New Word search. The purpose of the app is to allow you explore the different ways language is used.")

    # if phase == 0:
    #     print("You will be asked a sequence of questions to help you tailer your experience.")

    # search_term01 = input("Please enter your first search term: ")
    # search_term02 = input("please enter your second search term: ")

    # ### Start date 50 year incremeents
    # ### Ignore proper nouns
    #Keyword or Person?
    # ### Open page when done?
    # ### Article Limit?
