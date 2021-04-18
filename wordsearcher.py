#################################
##### Name: Greg Nickel  ########
##### Uniqname: gnickel  ########
#################################

import requests
import json
from bs4 import BeautifulSoup
import numpy as np
import plotly.graph_objects as go

import secrets

CACHE_DICT = {} #Temporary storage. Stores articles texts and topic results

def word_cache_loader():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary

    Parameters
    ----------
    None

    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open('word_cache.json', 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict

def word_cache_saver(word_cache):
    ''' Saves the current state of the cache to disk

    Parameters
    ----------
    word_cache: dict
        The dictionary to save

    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(word_cache)
    fw = open('word_cache.json',"w")
    fw.write(dumped_json_cache)
    fw.close()

class Topic_Results:
    def __init__(self,topic,sentence_count,word_count,word_dict):
        self.topic = topic
        self.sentence_count = sentence_count
        self.word_count = word_count
        self.word_dict = word_dict

        #Empty/Default values until updated by methods
        self.word_objects = []
        self.search_number = 0

        self.most_used_word = "" #No restrictions
        self.most_popular_words = [] #Ignoring words to ignore
        self.most_popular_words_counts = []
        self.syllable_count = 0
        self.origin_counts = {}
        self.flesch_score = 0

    def __str__(self):
        return f"Search for {self.topic} returned {self.word_count} words in {self.sentence_count} sentences with a total of {self.syllable_count} syllables."

    def word_list_builder(self):
        """
        Takes the word_dict of counts and creates a list of Word objects. The word 
        'name' and 'count are created and stored when the articles are parsed.
        This is combed with word classification information is stored in a cache
        or can be collected by the word_classifer() function.
        """
        progress_count = 0
        for key, val in self.word_dict.items():
            try:
                classification_data = word_cache[key]
            except KeyError:
                classification_data = word_classifer(key)

            name = classification_data[0]
            syllables = classification_data[1]
            part_of_speech = classification_data[2]
            origins = classification_data[3]
            ignore = classification_data[4]

            new_word = Word(name,part_of_speech,syllables,origins,ignore)
            new_word.counts = val
            self.word_objects.append(new_word)
            progress_count += 1
            if progress_count%50 == 0:
                print(f'Processed {progress_count} unique words.')

    def syllable_counter(self):
        """
        Counts the number of syllables. Used in computing reding scores.
        """
        for word in self.word_objects:
            occurences = self.word_dict[word.word.lower()][3]
            self.syllable_count += word.syllable*occurences

    def Flesch_reading_ease(self):
        """
        Calculates a reading score for the articles based on word count, sentence count and syllable count
        100.00–90.00	5th grade	Very easy to read. Easily understood by an average 11-year-old student.
        90.0–80.0	6th grade	Easy to read. Conversational English for consumers.
        80.0–70.0	7th grade	Fairly easy to read.
        70.0–60.0	8th & 9th grade	Plain English. Easily understood by 13- to 15-year-old students.
        60.0–50.0	10th to 12th grade	Fairly difficult to read.
        50.0–30.0	College	Difficult to read.
        30.0–10.0	College graduate	Very difficult to read. Best understood by university graduates.
        10.0–0.0	Professional	Extremely difficult to read. Best understood by university graduates
        https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests
        """
        score = 206.835 - 1.1015*(self.word_count/self.sentence_count)-84.6*(self.syllable_count/self.word_count)
        self.flesch_score = score

    def popular_words(self):
        """
        The the most used word (no restriction) and a list of the 5 most common
        words (excluding words form the ignore list)
        """
        max = 0
        max_ig = 0
        ranks = {}
        ranks_ignore = {}
        for word in self.word_objects:
            if word.ignore:
                if word.counts[3] not in ranks_ignore.keys():
                    ranks_ignore[word.counts[3]] = [word.word]
                else:
                    ranks_ignore[word.counts[3]].append(word.word)
                if word.counts[3] > max_ig:
                    max_ig = word.counts[3]
            else:
                if word.counts[3] not in ranks.keys():
                    ranks[word.counts[3]] = [word.word]
                else:
                    ranks[word.counts[3]].append(word.word)
                if word.counts[3] > max:
                    max = word.counts[3]
        self.most_used_word = ranks_ignore[max_ig][0]
        if len(ranks[max]) > 5:
            self.most_popular_words = ranks[max][:5]
            self.most_popular_words_counts = [max,max,max,max,max]
        else:
            self.most_popular_words = ranks[max]
            for x in ranks[max]:
                self.most_popular_words_counts.append(max)
            remaining = 5 - len(ranks[max])
            for x in range(max):
                if max-(x+1) in ranks.keys():
                    if len(ranks[max-(x+1)]) > remaining:
                        self.most_popular_words.extend(ranks[max-(x+1)][:remaining])
                        for x in range(remaining):
                            self.most_popular_words_counts.append(max-(x+1))
                        break #Stop looking for more words
                    else:
                        self.most_popular_words.extend(ranks[max-(x+1)])
                        for x in range(len(ranks[max-(x+1)])):
                            self.most_popular_words_counts.append(max-(x+1))

    def origin_agreggator(self):
        """
        Agreggates the word origins into percentages, counts unique words.
        """
        origin_counts = {
            "Greek": 0,
            "Latin": 0,
            "French": 0,
            "English": 0,
            "German": 0,
            "Norse" : 0,
            "Other" : 0
        }
        for word in self.word_objects:
            any_origin_count = 0
            for key in origin_counts.keys():
                if key in word.origins:
                    origin_counts[key] += word.counts[3]
                    any_origin_count += 1
            if any_origin_count == 0:
                origin_counts['Other'] += word.counts[3]
        self.origin_counts = origin_counts

    def origins_bar_graph_maker(self):
        """
        Pulls the origins data and creates an HTML file with a bar graph using Plotly
        """
        labels = []
        values = []
        for key, val in self.origin_counts.items():
            labels.append(key)
            values.append(val)

        fig = go.Figure(data=[go.Bar(x=labels, y=values)])
        fig.write_html(f"originbar{self.search_number}.html", auto_open=False)

    def pos_pie_graph_maker(self):
        """
        Loops over word_objects to count parts of speech, then creates pie chart for that data
        """
        pos_dict = {
            'adjective' : 0,
            'noun' : 0,
            'pronoun' : 0,
            'preposition' : 0,
            'verb' : 0,
            'adverb' : 0,
            'article' : 0,
            'Other' : 0
        }
        for word in self.word_objects:
            classified = 0
            for key in pos_dict.keys():
                if key in word.part_of_speech:
                    pos_dict[key] += word.counts[3]
                    classified += 1 #gaurantee that each word gets put into at least one category
            if classified == 0:
                pos_dict["Other"] += word.counts[3]

        labels = []
        values = []
        for key,val in pos_dict.items():
            labels.append(key)
            values.append(val)
        pie_data = go.Pie(labels=labels, values=values)
        fig = go.Figure(data=pie_data)
        fig.write_html(f"pospie{self.search_number}.html", auto_open=False)

    def html_report(self):
        """
        Takes a results object and pulled out data and drops into a html table cell.
        Basically, it's madlibs. https://www.madlibs.com/

        Parameters:
        -----------
        results (Self)

        Return:
        html_cell (string)
        """
        href = "https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests"
        score = round(self.flesch_score,2)
        if score > 90:
            person = "the average 5th grader"
        elif score > 80:
            person = 'the average 6th grader'
        elif score > 70:
            person = "the average 6th grader"
        elif score > 60:
            person  = 'the typical 8th or 9th grader'
        elif score > 50:
            person  = 'the typical 10th or 12th grader'
        elif score > 30:
            person  = 'the typical undergraduate student'
        elif score > 10:
            person = 'a typical college graduate'
        else:
            person = 'someone with a professional degree'

        flesch_sentence = f"""
        The articles, on avearge, have a <A href={href}> Flesch
        reading Ease</A> score of {score}. That corresponds to something that is 
        written for {person}.
        """

        common_words_table = "<table>"
        for x in range(5):
            word = self.most_popular_words[x]
            results = usage_trend(word)
            common_words_table += f"""
            <TR><TD><font size=5><B>{word}</B></font><BR>(Used {self.most_popular_words_counts[x]} times)</TD>
            <TD><IMG SRC="z_{results[0]}.png" ALT='This word is {results[1]}' width=50 height=50></TD></TR>
            """
        common_words_table += "</table>"

        html_cell = f"""
        <TD WIDTH='425'>
        <H1>{self.topic}</H1>
        <p>Your search for {self.topic} yielded {self.word_count} words in {self.sentence_count}
        sentences. {flesch_sentence}</p>
        <HR>
        <P>
        The most commonly used word is (not surprisingly) <B><I>{self.most_used_word}</I></B>,
        but that is a pretty common word.
        </P>
        <P>
        Ignoring <A HREF='http://xpo6.com/list-of-english-stop-words/'>stop words</A>, the
        most commonly words used were:</P>
        {common_words_table}
        <HR>
        <p><B>Parts of Speech</B></p>
        <iframe src="pospie{self.search_number}.html"
        height="300" width="400">
        </iframe>
        <HR>
        <p><B>Lanuage of Origin</B></p>
        <iframe src="originbar{self.search_number}.html"
        height="300" width="400">
        </iframe>
        </TD>
        """
        return html_cell

class Word:
    def __init__(self,word,part_of_speech,syllable,origins,ignore):
        self.word = word
        self.part_of_speech = part_of_speech
        self.syllable = syllable
        self.origins = origins
        self.ignore = ignore
        self.counts = [0,0,0,0]

words_to_ignore = ("i", "a", "about", "above", "above", "across", "after", "afterwards", 
        "again", "against", "all", "almost", "alone", "along", "already", "also","although",
        "always","am","among", "amongst", "amoungst", "amount",  "an", "and", "another", 
        "any","anyhow","anyone","anything","anyway", "anywhere", "are", "around", "as",
        "at", "back","be","became", "because","become","becomes", "becoming", "been",
        "before", "beforehand", "behind", "being", "below", "beside", "besides", "between",
        "beyond", "bill", "both", "bottom","but", "by", "call", "can", "cannot", "cant",
        "co", "con", "could", "couldnt", "cry", "de", "describe", "detail", "do", "done",
        "down", "due", "during", "each", "eg", "eight", "either", "eleven","else",
        "elsewhere", "empty", "enough", "etc", "even", "ever", "every", "everyone",
        "everything", "everywhere", "except", "few", "fifteen", "fify", "fill",
        "find", "fire", "first", "five", "for", "former", "formerly", "forty", "found",
        "four", "from", "front", "full", "further", "get", "give", "go", "had", "has",
        "hasnt", "have", "he", "hence", "her", "here", "hereafter", "hereby", "herein",
        "hereupon", "hers", "herself", "him", "himself", "his", "how", "however",
        "hundred", "ie", "if", "in", "inc", "indeed", "interest", "into", "is", "it",
        "its", "itself", "keep", "last", "latter", "latterly", "least", "less", "ltd",
        "made", "many", "may", "me", "meanwhile", "might", "mill", "mine", "more",
        "moreover", "most", "mostly", "move", "much", "must", "my", "myself", "name", "namely",
        "neither", "never", "nevertheless", "next", "nine", "no", "nobody", "none", "noone",
        "nor", "not", "nothing", "now", "nowhere", "of", "off", "often", "on", "once",
        "one", "only", "onto", "or", "other", "others", "otherwise", "our", "ours",
        "ourselves", "out", "over", "own","part", "per", "perhaps", "please", "put",
        "rather", "re", "same", "see", "seem", "seemed", "seeming", "seems", "serious",
        "several", "she", "should", "show", "side", "since", "sincere", "six", "sixty",
        "so", "some", "somehow", "someone", "something", "sometime", "sometimes",
        "somewhere", "still", "such", "system", "take", "ten", "than", "that", "the",
        "their", "them", "themselves", "then", "thence", "there", "thereafter", "thereby",
        "therefore", "therein", "thereupon", "these", "they", "thick", "thin", "third",
        "this", "those", "though", "three", "through", "throughout", "thru", "thus", "to",
        "together", "too", "top", "toward", "towards", "twelve", "twenty", "two", "un",
        "under", "until", "up", "upon", "us", "very", "via", "was", "we", "well", "were",
        "what", "whatever", "when", "whence", "whenever", "where", "whereafter",
        "whereas", "whereby", "wherein", "whereupon", "wherever", "whether",
        "which", "while", "whither", "who", "whoever", "whole", "whom", "whose",
        "why", "will", "with", "within", "without", "would", "yet", "you", "your",
        "yours", "yourself", "yourselves", "the")

def article_url_fetcher(search_keyword):
    """
    For a given search term return a list of up to 10 URL's for related NYT Articles

    Parameter
    ---------
    search_keyword (string)

    Return
    ---------
    url_list (list)
    """
    print(f"Looking up articles for {search_keyword}.")
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

def search_word_grouper(url_list):
    """
    For a list of URL, the function use the article_text_collector() to collect
    the body of each article. Then, this function further complies the bodies into one
    long string

    Parameter
    ---------
    url_list (list of strings)

    Return
    ---------
    seach_word_text (string) combined boby text for a given search word
    """
    search_word_text = ""
    for url in url_list:
        search_word_text += article_text_collector(url)
    return search_word_text

def text_parser(articles,search_keyword,cache=CACHE_DICT):
    """
    Given the combine 

    Parameter
    ---------
    articles (string)

    Return
    ---------
    Results article
    """
    #Phase 1, eliminate puntucation.
    no_punctuation = ""
    sentence_count = 0
    for x in articles:
        if x in "1234567890@#$%^&*()-+_=[],:;/'"+'"'+'“”—':
            pass
        elif x in ".?!":
            sentence_count += 1
            no_punctuation += " " #The paragraphs are sometimes run into each other.
        else:
            no_punctuation += x

    articles_as_word_list = no_punctuation.split()
    word_count = 0

    word_dict = {}
    for word in articles_as_word_list:
        word_count += 1
        word = word.strip()
        if word.lower() in word_dict.keys():
            if word.islower():
                word_dict[word.lower()][0] += 1
            elif word.istitle():
                word_dict[word.lower()][1] +=1
            else:
                word_dict[word.lower()][2] +=1
            word_dict[word.lower()][3] +=1
        else:
            word_dict[word.lower()]=[0,0,0,0]
            if word.islower():
                word_dict[word.lower()][0] += 1
            elif word.istitle():
                word_dict[word.lower()][1] +=1
            else:
                word_dict[word.lower()][2] +=1
            word_dict[word.lower()][3] +=1

    cache[search_keyword] = Topic_Results(search_keyword,sentence_count,word_count,word_dict)
    return cache[search_keyword]

def word_classifer(word):
    """
    Given a word, this function first looks at Datamuse. If the word as written doesn't
    match the first word result, then word is classified as an Other, an estimation
    of the syllable count is made and the Origins are empty/unknown.
    If the word matches the initial results, the number of syllables is collected and the function
    continues to use the M-W Api to collect part of speech and word origin data.

    Word origins are a list containing (or not) the six most common sources of English words
    "Greek", "Latin", "French", (old/middle)"English", "German", "Norse"

    Finally, the program classifies each words as a common word to ignore or not using an existing list.

    Parameter
    ---------
    word (string)

    Return
    ---------
    Results (List of attributes)
    """
    origins = []

    response = requests.get(f"https://api.datamuse.com/words?sl={word}")
    datamuse_resp = json.loads(response.text)

    if datamuse_resp[0]["word"] == word:
        syllables = datamuse_resp[0]["numSyllables"]

        key = secrets.wordkey
        params= {
              'key' : key
        }
        response = requests.get(f"https://www.dictionaryapi.com/api/v3/references/collegiate/json/{word}",params)
        word_data = json.loads(response.text)
        if isinstance(word_data[0],dict):
            try:
                part_of_speech = word_data[0]['fl']
            except KeyError:
                part_of_speech = word_data[1]['fl']
            try:
                raw_origins = word_data[0]['et'][0][1]
                for lang in ["Greek", "Latin", "French", "English", "German", "Norse"]:
                    if raw_origins.__contains__(lang):
                        origins.append(lang)
            except KeyError:
                pass #origins remain empty
        else:
            part_of_speech = "Other"
    else:
        syllables = syllable_estimator(word)
        part_of_speech = 'Other'

    if word.lower() in words_to_ignore:
        ignore = True
    else:
        ignore = False

    word_cache[word.lower()] = [word.lower(),syllables,part_of_speech,origins,ignore]

    return word_cache[word.lower()]

def syllable_estimator(word):
    """
    For words that do not appear in the Datamuse database, this function makes an
    estimated syllable count by looking at vowel clusters.

    The function assumes no silent e's at the end of words. Words that are input into
    this function are likely to be proper-nouns or non-English words, so that seems
    like a safe assumption.

    Parameter
    ---------
    word (string)

    Return
    ---------
    syllable_count (int)
    """
    syllable_count = 0
    translated_word = ""
    #For each letter, translate it into a binary V for vowel or C for consonant
    for x in word.lower():
        if x in ['a','e','i','o','u']:
            translated_word += "V"
        else:
            translated_word += "C"

    #If a word ends in y, assume that it is used as a vowel
    #Also, because the algorthm compares consecutive words, a conconant is added
    #to the end of every word.
    if word[-1] == 'y':
        translated_word = translated_word[:-1] + "VC"
    else:
        translated_word += "C"

    #Counts the number of vowel clusters
    for i in range(len(translated_word)-1):
        if translated_word[i] == "V" and translated_word[i] != translated_word[i+1]:
            syllable_count += 1
    return syllable_count

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
    list [trend, description]
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
    r = np.corrcoef(x, y)

    pearson_r = (r[0, 1])

    if pearson_r > 0.8:
        return ['up', 'trendy']
    elif pearson_r > 0.5:
        return ['inc', 'gaining popularity']
    elif pearson_r > -0.5:
        return ['flat', 'flat']
    elif pearson_r > -0.8:
        return ['dec', 'losing popularity']
    else:
        return ['down','archaic']

def results_object_generator(urls,search_keyword,search_count):
    """
    Given a search word, calls the two functions required combine text and 
    parse text to create a Topic_Results object. Then, calls all
    methods to populate the remaining attributes for a Topic_Results object.

    Parameters
    ----------
    search_keyword (string)
    search_count (int) indexes search counts

    Returns
    ----------
    Topic_Results (object)
    """
    text = search_word_grouper(urls)
    results_object = text_parser(text,search_keyword)

    results_object.word_list_builder()
    results_object.syllable_counter()
    results_object.Flesch_reading_ease()
    results_object.popular_words()
    results_object.origin_agreggator()
    results_object.search_number = search_count
    results_object.origins_bar_graph_maker()
    results_object.pos_pie_graph_maker()
    return results_object

def output_maker(results01,results02):
    """
    """
    pass


if __name__ == "__main__":
    word_cache = word_cache_loader()


    search_reports= {}
    search_count = 0
    print("Welcome to the New Word search. The purpose of the app is to allow you explore the different ways language is used.")
    print("At any point, type 'exit!' to quit the program.")
    while True:
        print("Would you like to search of an author's name or topic keyword? ")
        mode = input('Type "author" or "keyword" or type "help" for help. ')
        if mode.lower() == 'exit!':
            break
        elif mode.lower() == 'author':
            pass
        elif mode.lower() == 'keyword':
            pass
        elif mode.lower() == 'help':
            pass

        search_term = input("Please enter your first search term: ")

        if search_term.lower() == 'exit!':
            break
        elif search_term.lower() == 'help':
            pass #do help stuff
        else:
            urls = article_url_fetcher("medicine")
            if len(urls) < 1:
                print("No results were returned, please try again.")
                continue
            else:
                search_count += 1
                results_object = results_object_generator(urls,search_term,search_count)
                print(results_object)
                search_reports[search_term] = results_object.html_report()
        if search_count >= 2:
            report_mode = input('Would you like to print a report? Type "yes" or "no": ')
            if report_mode.lower() == "exit!":
                break
            elif report_mode.lower() in ['yes','ye','y']:
                pass
            else:
                print("I'll take that as a 'no'.")







    #DO NOT DELETE AFTER THIS LINE
    word_cache_saver(word_cache)