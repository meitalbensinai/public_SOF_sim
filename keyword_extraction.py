# keyword extraction, using tf.idf. not code similarity directly related.

from __future__ import division, unicode_literals
import math
from consts import *
from lsa_compare import text_stemming, get_random_test_data
from process_one_question import get_orig_possible_snippets
try:
   import cPickle as pickle
except:
   import pickle

from q_data import *
from pymongo import Connection

# get to my remote mongodb
client = Connection('mongodb://meitalbs:n40h10@ds039251.mongolab.com:39251/af_tagme-meitalbensinai')
local_client = Connection("mongodb://localhost")
DB = client.get_default_database()
LOCAL_DB = local_client.git
WEB_RES_DB = DB['results_with_related']
GIT_DB = LOCAL_DB.base

PIC_FILE = "pickeled_idf"
N = 10


def tf(word, blob):
    """term count"""
    return blob.count(word) / len(blob)

def n_containing(word, bloblist):
    """term count in the corpus"""
    return sum(1 for blob in bloblist if word in blob)

def idf(word, bloblist):
    """inverse document frequency"""
    return math.log(len(bloblist) / (1 + n_containing(word, bloblist)))

def tfidf(word, blob, bloblist):
    """tf.idf"""
    return tf(word, blob) * idf(word, bloblist)

def main():
    #build_idf()
    build_db()
    q_dict = dict_of_info[28942758]
    code = q_dict['code']
    title = q_dict['title']
    content = q_dict['content']
    tags = q_dict['tags']
    scores = extract_keywords(title, content, tags, code)
    final_keywords(scores)


def build_db():
    """build db fot the site, 'tag me if you can', should be used for the evaluation"""
    ##############
    WEB_RES_DB = DB["new_web_res"]
    #############

    pair_id = WEB_RES_DB.count()
    ids_to_look_for1 = ['104420', '3319586', '3371879', '613183', '89228', '952914', '2068372', '480214', '1207406', '4836710', '38987', '682367', '1450393', '22676', '519633', '82831', '931092', '354038', '2793150', '363681', '109383', '153724', '2784514', '4216745', '3481828', '469695', '1555262', '140131', '46898', '921262', '160970', '1359689', '80476', '1625234', '240546', '2885173', '5585779', '2808535', '41107', '724043', '139076', '304268', '999172', '4205980', '122105', '1128723', '1102891', '428918', '693997', '525212', '225337']
    ids_to_look_for2 = ['53513', '5767325', '82831', '221294', '1789945', '4240080', '613183', '41107', '236129', '363681', '472906', '5585779', '46898', '29361031', '29095967', '28942758']
    ids_to_look_for = ids_to_look_for1 + ids_to_look_for2

    #########################
    ids_to_look_for = []
    i = 0
    print "look for ids"
    flag = False
    for x in POSTS_DB.find({}):
        i += 1
        if i < 1000:
            continue
        if x["Id"] == "5427618":
            print "start"
            flag = True
        if i % 2 == 0:
            continue
        if len(ids_to_look_for) > 100000:
            break
        if flag:
            ids_to_look_for.append(x["Id"])
    print "start building"
    ######################

    for q_id in ids_to_look_for:
        codes = get_orig_possible_snippets(q_id)
        if codes is None or codes == []:
            print "DROOPED:", q_id
            continue
        question = POSTS_DB.find({"Id": str(q_id)})[0]
        title = no_punctuation(clean_line(QUOTE_OUT_RE.sub("", CODE_OUT_RE.sub("", question['Title']))).replace("\n\n", "\n"))
        content = no_punctuation(clean_line(QUOTE_OUT_RE.sub("", CODE_OUT_RE.sub("", question['Body']))).replace("\n\n", "\n"))
        tags = " ".join(question["Tags"].replace("<", "").split(">"))
        code = codes[0][0]
        scores = extract_keywords(title, content, tags, code)
        tag1, tag2, tag3, tag4 = final_keywords(scores)

        WEB_RES_DB.insert({"pair_id": pair_id, "code1": code, "tag1": tag1, "tag2": tag2, "tag3": tag3, "tag4": tag4, "q_id": q_id})
        print({"pair_id": pair_id, "code1": code, "tag1": tag1, "tag2": tag2, "tag3": tag3, "tag4": tag4})
        pair_id += 1


def final_keywords(scores_dict):
    """extract final keywords from the scores dict"""
    sorted_words = sorted(scores_dict.items(), key=lambda x: x[1], reverse=True)
    ret_val = []
    for word in sorted_words:
        if len(ret_val) == 3:
            if sorted_words[2][1] - word[1] < 0.2:
                ret_val.append(word[0])
            else:
                ret_val.append("")
            break
        if len(ret_val) < 3:
            if text_stemming(word[0]) not in ret_val:
                ret_val.append(word[0])
    while len(ret_val) < 4:
        ret_val.append("")
    return ret_val


def build_idf():
    """build the idf dict and store it on disc"""
    test_set_q, test_set_t, tags = get_random_test_data(1000000)
    all_texts = [".".join([test_set_q[e], test_set_t[e]]) for e in range(len(test_set_q))]
    filterd = []
    for doc in all_texts:
        filterd.append(" ".join([e for e in doc.split() if e not in STOP_WORDS + LANG_WORDS]))
    idf_dump = {}
    for i, blob in enumerate(filterd):
        for word in blob.split():
            idf_dump[word] = idf(word, blob)
    with open(PIC_FILE, "wb") as writer:
        pickle.dump(idf_dump, writer, pickle.HIGHEST_PROTOCOL)


def extract_keywords(title, content, tags, code):
    """extract keywords from the given title, content, tags and code"""
    with open(PIC_FILE, "rb") as reader:
        idf_dump = pickle.load(reader)
    def one_part_scores(text):
        t = no_punctuation(clean_line(CODE_OUT_RE.sub("", text)))
        t = [e for e in t.split() if e not in STOP_WORDS+LANG_WORDS and len(t) > 1]
        return {word: tf(word, t) * idf_dump.get(word, 0.1) for word in t}

    words = (title + " " + content).split()
    add_words = []
    for word in code.split():
        if word in words:
            add_words.append(word)
    content = content + " " + " ".join(add_words)

    tit_scores = one_part_scores(title)
    cont_scores = one_part_scores(content)
    tags_scores = one_part_scores(tags)
    code_scores = one_part_scores(code)

    scores = {}
    for key in tit_scores.keys() + code_scores.keys() + tags_scores.keys() + cont_scores.keys():
        # the weights should be chosen in a better way of course..
        scores[key] = 2 * tit_scores.get(key, 0) + cont_scores.get(key, 0) + tags_scores.get(key, 0) + 0 * code_scores.get(key, 0)
    sorted_words = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    ret_val = {}
    for word, score in sorted_words[:min(N, len(sorted_words))]:
            print("\tWord: {}, TF-IDF: {}".format(word, round(score, 5)))
            ret_val[word] = round(score, 5)
    return ret_val

if __name__ == '__main__':
    main()


