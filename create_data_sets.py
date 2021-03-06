import random
from argparse import ArgumentParser
import os

def create_datasets(datadir):
    data = open(os.path.join(filename,'full/index')).readlines()
    spam = [line for line in data if line.startswith('spam')]
    ham = [line for line in data if line.startswith('ham')]
    random.shuffle(spam)
    random.shuffle(ham)
    test = spam[:1000] + ham[:1000]
    validation = spam[1000:2000] + ham[1000:2000]
    training = spam[2000:] + ham[2000:]
    create_files(datadir, test, validation, training, 'datasets')

def writelines(filename, data):
    outfile = open(filename, 'w')
    outfile.writelines(data)
    outfile.close()

def create_files(datadir, test, validation, training, folder):
    datasets = os.path.join(datadir, folder)
    if not os.path.exists(datasets):    
        os.mkdir(datasets)
    writelines(os.path.join(folder, 'test'), test)
    writelines(os.path.join(folder, 'validation'), validation)
    writelines(os.path.join(folder, 'supervised'), training)
    for index, val in enumerate(range(0,len(training), 5000)):
        writelines(os.path.join(folder, 'semisuper_'+str(index)), training[val: val+5000])

    
if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("datadir", help="The untarred trec data directory for example /path/to/trec05p-1")
    args = parser.parse_args()
    if args.datadir:
        create_datasets(datadir)
