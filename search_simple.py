import cPickle
import re
import parser
import time


if __name__ == "__main__":
    with open("url_file.txt", "rb") as url_file:
        urls = cPickle.load(url_file)

    with open('dict_file.txt', 'rb') as dict_file:
        dict = cPickle.load(dict_file)

    index_file = open("index.txt", "rb")

    while True:
        try:
            line = raw_input()

            #print("input raw line: {}".format(line))
            print(line)
            question = line.decode('utf-8').lower()

            q = parser.parse_query(question)
            #print("query: {}".format(q))

            number_of_urls = 0
            result, flag = parser.get_q_list_urls_simple(q, dict, index_file)

            print(len(result))
            for doc_id in result:
                try:
                    print(urls[doc_id])
                except:
                    print(doc_id)
        except:
            index_file.close()
            break


