import re
import codecs
header_pat = re.compile("([^:]*):(.*)$", re.I)
def extract(email):
    data = codecs.open(email, 'r').readlines()
    headers =  {}
    prevheader = None
    boundary_set = False
    boundary = '';
    for index, line in enumerate(data):
        if boundary_set:
            if boundary in line:
                boundary_set = False
            else:
                continue
        if not line.strip():
            break 
        res = header_pat.findall(line)
        if not res:
            prevheader = (prevheader[0], prevheader[1] + line)
            if line.strip().lower().startswith('boundary'):
                boundary_set = True
                boundary = line.strip().split('=')[1].strip("'\"");
        else:

            if prevheader:
                headers[prevheader[0].strip()] = prevheader[1].strip()
            prevheader = res[0]
    
    body = "".join(data[index:])
    import nltk
    body = nltk.clean_html(body)
    print headers['Subject']
    return (headers, body)

if __name__ == "__main__":
    import sys
    import pprint
    pprint.pprint(extract(sys.argv[1]))
