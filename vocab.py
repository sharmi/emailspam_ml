from supervisor_learn import load_vocab
import re
from optparse import OptionParser
from collections import defaultdict
import pickle
import psycopg2
import psycopg2.extensions
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)

emailre = re.compile('[a-zA-Z0-9+_\-\.]+@[0-9a-zA-Z][.-0-9a-zA-Z]*.[a-zA-Z]+', re.I)
urlre = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', re.I)
numre = re.compile("[0-9]+")
count_num = 0
count_email = 0
count_url = 0

conn = psycopg2.connect(database="ml", user="sharmi", password="sherlock")
cur = conn.cursor()
SELECTSQL = "SELECT ds from  emailcache where email=%s;"
def analyse_vocab(vocab):
    num = url = email = 0
    for term in vocab.keys():
        if numre.findall(term): 
            num += 1
        if urlre.findall(term):
            url += 1
        if emailre.findall(term):
            email += 1
    print num, url, email

def reduce_vocab(vocab):
    for term in vocab.keys():
        if numre.findall(term): 
            del vocab[term]
        elif urlre.findall(term):
            del vocab[term]
        elif emailre.findall(term):
            del vocab[term]
    return vocab

def create_vocab(emails):
    lex = defaultdict(int)    
    for index, email in enumerate(emails):
        cur.execute(SELECTSQL, (email,))
        data = eval(cur.fetchone()[0])
        stems = set(data[-1])
        for stem in stems:
            lex[stem] = lex[stem] + 1
        for key in lex.keys():
            if lex[key] < 2:
                del lex[key]

    return reduce_vocab(lex)
    
if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-r", "--reduce", action="store_true",
                      dest="reduce", default=False,
                                        help="removes non conforming terms from vocab")

    (options, args) = parser.parse_args()
    if options.reduce:
        reduce_vocab('email.pkl')
    else:
        analyse_vocab('email.pkl')


