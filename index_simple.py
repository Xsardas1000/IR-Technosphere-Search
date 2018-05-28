import docreader
from docreader import DocumentStreamReader
import bitstream_v as bitstream
import cPickle
import os
import time
from collections import defaultdict
import doc2words


def get_data():
    reader = DocumentStreamReader(docreader.parse_command_line().files)
    terms = defaultdict(list)
    ind = 0
    urls = []
    for doc in reader:
        for word in set(doc2words.extract_words(doc.text)):
            terms[word].append(ind)
        ind += 1
        urls.append(doc.url)
    return terms, urls


if __name__ == "__main__":
    terms, urls = get_data()
    buffer = [] ## sequence of bytearrays for each term
    dictionary = dict()

    start = time.time()

    for key, dl in terms.iteritems():
        prev_len = len(buffer)
        compr_sim = bitstream.compress_simple(dl)

        buffer.extend(compr_sim)
        dictionary[key] = (prev_len, len(compr_sim))

    print(time.time() - start)

    with open("index.txt", "wb") as index_file:
        index_file.write(bytearray(buffer))

    with open("url_file.txt", "wb") as url_file:
        cPickle.dump(urls, url_file)

    with open('dict_file.txt', 'wb') as dict_file:
        cPickle.dump(dictionary, dict_file)

    print(time.time() - start)

