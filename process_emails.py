import os.path
from collections import defaultdict
from emailextract import extract
import nltk
import time
import glob
import string
import json
from email.parser import FeedParser
from email.Iterators import typed_subpart_iterator
from argparse import ArgumentParser
import pickle
import psycopg2
import psycopg2.extensions
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)
from dbconfig import get_db_config

user, password, dbname = get_db_config('db.cnf')
conn = psycopg2.connect(database=dbname, user=user, password=password)
cur = conn.cursor()
INSERTSQL = "INSERT INTO emailcache (email, ds) VALUES (%s, %s);"

def get_charset(message, default="ascii"):
    """Get the message charset"""

    if message.get_content_charset():
        return message.get_content_charset()

    if message.get_charset():
        return message.get_charset()

    return default

def fixaliases_charset(charset):
    aliases = {'big-5':'big5'}
    if charset in aliases:
        return aliases[charset]
    else:
        return charset

class EmailProcessor(object):
    def __init__(self):
        self.tokenizer = nltk.tokenize.WhitespaceTokenizer()
        self.stemmer = nltk.stem.porter.PorterStemmer()
        self.stopwords = open('/home/sharmi/nltk_data/corpora/stopwords/english').readlines()
        self.stopwords = set([word.strip() for word in self.stopwords if word.strip()])
        

    def extract_multipart(self, message):
        text_parts = [part for part in typed_subpart_iterator(message)]
        body = []
        html = 0
        for part in text_parts:
            charset = get_charset(part, get_charset(message))
            charset = fixaliases_charset(charset)
            if part.get_content_subtype() != 'plain':
                html = html + 1
            try:
                body.append(unicode(part.get_payload(decode=True),
                                    charset,
                                    "replace"))
            except LookupError:
                body.append(unicode(part.get_payload(decode=True),
                                    'utf8',
                                    "replace"))
                
        texts = "\n".join(body)
        images = len([part for part in typed_subpart_iterator(message, 'image')])
        videos = len([part for part in typed_subpart_iterator(message, 'video')])
        applications = len([part for part in typed_subpart_iterator(message, 'application')])
        return (texts, html, images, videos, applications)
            
    def parse_email(self, email):
        fp = FeedParser()
        fp.feed(open(email).read())
        message = fp.close()
        if message.is_multipart():
            texts, html, images, videos, applications = self.extract_multipart(message)
        else:
            texts, html, images, videos, applications = (message.get_payload(), 0,0,0, 0)
        return (message.items(), html, texts, images, videos, applications)


    def processemail(self, email):
        headers, html, texts, images, videos, applications = self.parse_email(email)
        body = nltk.clean_html(texts)
        tokens = self.tokenizer.tokenize(body)
        tokens = [token for token in tokens if token not in self.stopwords]
        stems = [self.stemmer.stem(word.strip(string.punctuation)).lower() for word in tokens]
        return (headers, html, texts, images, videos, applications, stems)


def main(datadir):
    st = time.time()
    ep = EmailProcessor()
    inputfiles = glob.glob(os.path.join(datadir, 'data/*/*'))
    for email in inputfiles:
        data = ep.processemail(email)
        cur.execute(INSERTSQL, (email.split('trec05p-1/')[-1], repr(data)))
        conn.commit()
    print time.time() - st    
        


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("datadir", help="The untarred trec data directory for example /path/to/trec05p-1")
    args = parser.parse_args()
    if args.datadir:
        main(args.datadir)
