import os
from numpy import *
from argparse import ArgumentParser
import pickle
from scipy.sparse import lil_matrix
from sklearn.svm.sparse import SVC
import psycopg2
import psycopg2.extensions
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)
from vocab import create_vocab
import logging
import time
from dbconfig import get_db_config

log = logging.getLogger('super')
hdlr = logging.FileHandler('super.log')
log.addHandler(hdlr) 
log.setLevel(logging.DEBUG)

user, password, dbname = get_db_config('db.cnf')
conn = psycopg2.connect(database=dbname, user=user, password=password)
cur = conn.cursor()
SELECTSQL = "SELECT ds from  emailcache where email=%s;"

def generate_features(emails, vocab):
    print len(emails), len(vocab)
    vocab_len = len(vocab)
    features = lil_matrix((len(emails), len(vocab)+4), dtype=dtype('int8'))
    for index, email in enumerate(emails):
        cur.execute(SELECTSQL, (email,))
        data = eval(cur.fetchone()[0])
        feature =  [0] * len(vocab) + list(data[1:-1])
        stems = data[-1]
        for stem in stems:
            if stem in vocab:
                features[index, vocab[stem]] = 1
        html, texts, images, videos, applications = data[1:-1]
        features[index, vocab_len] = html
        features[index, vocab_len+1] = images
        features[index, vocab_len+2] = videos
        features[index, vocab_len+3] = applications
            #features[index, vocab_len + index] = item
        #features.append(feature)

    return features.tocsr()

def load_vocab(pklfile):
    pkl = open(pklfile, 'rb')
    data = pickle.load(pkl)
    vocab = [(key, index) for (index, key) in enumerate(data.keys())]
    vocab = dict(vocab)
    return vocab

def load_emails(emailfile):
    emails = open(emailfile).readlines()
    emails = [email.replace('../', '').strip() for email in emails]
    emails = [email.split()[::-1] for email in emails if email]
    return dict(emails)

def grid_search(training_features, training_results, validation_features, validation_results):
    gamma = [pow(2, -10), pow(2, -5), pow(2, -2), pow(2, 0), pow(2, 2)]
    C = [pow(2, -5), pow(2, -2), pow(2, 0), pow(2, 2), pow(2, 5), pow(2, 10)]
    error_rates = []
    for g in gamma:
        for c in C:
            log.info("Tracking gamma:%s C:%s " %(g, c))
            error_rate = classify(training_features, training_results, validation_features, validation_results, c, g)
            log.info("parameters gamma:%s C:%s Error Rate: %s" %(g, c, error_rate))
            error_rates.append((error_rate, g, c))
    error_rates.sort()
    return error_rates[0]

def classify(features, results, test_features, test_results, C, gamma):
    cli = "%s@%s" %(C, gamma) 
    st = time.time()
    log.info("Classifier begins")
    classifier = SVC(C=C, gamma=gamma, kernel="rbf")
    classifier.fit(features, results)
    st2 = time.time()
    prediction = classifier.predict(test_features)
    log.info("id: %s Training time: %s, Prediction time: %s" %(cli, st2-st, time.time()-st2) )
    error = 0
    for index, value in enumerate(prediction):
        if test_results[index] != value:
            error += 1
    return (error/float(len(test_results))) * 100


def main(datadir):
    training_emails = load_emails(os.path.join(datadir, 'datasets/supervised'))
    log.info("Size of training emails: %s" %len(training_emails))
    vocab = create_vocab(training_emails)
    log.info("Size of vocab = %s" %(len(vocab),))
    features = generate_features(training_emails, vocab)
    results = [ int(y=='spam') for x,y in training_emails.iteritems()]

    validation_emails = load_emails(os.path.join(datadir, 'datasets/validation'))
    validation_features = generate_features(validation_emails, vocab)
    validation_results = [ int(y=='spam') for x,y in validation_emails.iteritems()]

    log.info("Grid Search is about to begin") 
    error_rate, gamma, C = grid_search(features, results, validation_features, validation_results)
    testing_emails = load_emails(os.path.join(datadir, 'datasets/test'))
    testing_features = generate_features(testing_emails, vocab)
    testing_results = [ int(y=='spam') for x,y in testing_emails.iteritems()]
    error_rate = classify(features, results, testing_features, testing_results, C, gamma)
    print "Test data has been classified with the error rate of", error_rate
    log.info("Test data has been classified with the error rate of %s" %(error_rate,))
    #prediction = classifier.predict(testing_features)
    #failure = 0
    #for index, value in enumerate(prediction):
    #    if testing_results[index] != value:
    #        failure += 1

    #print failure



        

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("datadir", help="The untarred trec data directory for example /path/to/trec05p-1")
    args = parser.parse_args()
    if args.datadir:
        main(args.datadir)
