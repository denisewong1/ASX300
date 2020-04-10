import re
import nltk
#from collections import Counter
from nltk import word_tokenize
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
nltk.download('stopwords')
nltk.download('punkt')


# http://brandonrose.org/clustering
# tokenise and stem text
lstStemmer = SnowballStemmer("english")
def tokenize_and_stem(text):
    # first tokenize by sentence, then by word to ensure that punctuation is caught as it's own token
    tokens = [word for sent in nltk.sent_tokenize(text) for word in nltk.word_tokenize(sent)]
    filtered_tokens = []
    # filter out any tokens not containing letters (e.g., numeric tokens, raw punctuation)
    for token in tokens:
        if re.search('[a-zA-Z]', token):
            filtered_tokens.append(token)
    stems = [lstStemmer.stem(t) for t in filtered_tokens]
    return stems


# tokenise text
def tokenize_only(text):
    # first tokenize by sentence, then by word to ensure that punctuation is caught as it's own token
    tokens = [word.lower() for sent in nltk.sent_tokenize(text) for word in nltk.word_tokenize(sent)]
    filtered_tokens = []
    # filter out any tokens not containing letters (e.g., numeric tokens, raw punctuation)
    for token in tokens:
        if re.search('[a-zA-Z]', token):
            filtered_tokens.append(token)
    return filtered_tokens


# preprocess text clean up
def preprocess(texts,lstExclude):
    texts = (' XXXXX '.join(texts))
    texts = re.sub(r"&", "", texts) # replace ampersand
    texts = re.sub(r":", "", texts) # replace colon
    texts = re.sub(r"'s", "", texts) # replace apostrophe
    texts = re.sub(r"/", " ", texts) # replace forward slash
    texts = re.sub(r"-", "", texts) # replace hyphen
    texts = ' '.join(filter(lambda x: x not in lstExclude,  texts.split()))  # remove specific words
    texts = [s for s in re.split(" XXXXX ", texts)]
    texts = [w.lower() for w in texts] # make lower case
    return(texts)


# expects text file in bytes
def getanchors(xfilename):
    anchors = []
    with open(xfilename, 'rb') as f:
        xform = f.read()
    xform = xform.split(b'\n')
    for line in xform:
        if line.strip() : # if not blank row
            xanchor = line.decode('utf-8').replace('\t','').replace(u'\xa0', ' ').replace('+', '')
            xanchor = xanchor.replace(')',') ')
            xanchor = xanchor.strip()
            anchors.append(xanchor)
    return(anchors)


# havent used these yet
# get list of acronyms
def lstAcronyms(texts,lstCode):
    
    texts = ('\n'.join(texts))
    acronyms = re.sub(r"\b[A-Z][a-z\.]{1,}\b", "", texts)
    acronyms = re.sub(r"\b[a-z\.]{1,}\b", "", acronyms)
    acronyms = re.sub(r"\b[0-9\.]{1,}\b", "", acronyms)
    acronyms = word_tokenize(acronyms)
    #acronyms =[word.upper() for word in acronyms if word.isalpha() and len(word)>=2 and len(word)<=6]
    acronyms =[word.upper() for word in acronyms if word.isalpha() and word not in lstCode and len(word)>2 and len(word)<=6]

    return(acronyms)


# get list of tokens
def lstTokens(texts,acronyms,stoplist) :
    
    texts = ('\n'.join(texts))
    texts = re.sub(r'/',' ', texts)
    tokens = word_tokenize(texts)
    tokens = [token.lower() for token in tokens if token not in acronyms and token.lower() not in stoplist and len(token)>2]
    
    return(tokens)



