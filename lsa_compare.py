__author__ = 'Meital'
from consts import *
import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer, TfidfTransformer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import Normalizer
import numpy.linalg as LA
import time
try:
   import cPickle as pickle
except:
   import pickle

dictionary = []
FIRST = True


def get_test_data(ids):
    """returns content and titles for given ids"""
    texts = []
    titles = []
    tags = []
    not_in_db = []
    for id_num in ids:
        txt, title, tags_list = get_entry_data(id_num)
        if txt is None:
            not_in_db += [id_num]
            continue
        texts += [txt]
        titles += [title]
        tags += [tags_list]
    return texts, titles, not_in_db, tags


def get_random_test_data(size):
    """returns content, titles and tags for given number of documents
    size - number of documents"""
    curser = POSTS_DB.find({}, timeout=False)
    total = size
    texts = []
    titles = []
    tags = []
    for entry in curser:
        if total == 0:
            break
        try:
            for answer in entry["answers"]:
                if "<code>" in answer['Body']:
                    txt = no_punctuation(clean_line(CODE_OUT_RE.sub("", entry['Body'])))
                    title = no_punctuation(entry['Title'])
                    tags_list = [e for e in entry['Tags'].replace("<", "").split(">")[:-1] if e not in LANG_WORDS]
                    texts.append(txt)
                    titles.append(title)
                    tags.append(tags_list)
                    total -= 1
                    break
        except:
            pass
    curser.close()
    print total
    return texts, titles, tags


def get_entry_data(id_to_find):
    """returns content, title, and tags for given id, only for question with code in the answers"""
    x = POSTS_DB.find({'Id': id_to_find})
    try:
        for e in x[0]["answers"]:
            try:
                if "<code>" in e['Body']:
                    txt = no_punctuation(clean_line(CODE_OUT_RE.sub("", x[0]['Body'])))
                    title = no_punctuation(x[0]['Title'])
                    tags_list = [e for e in x[0]['Tags'].replace("<", "").split(">")[:-1] if e not in LANG_WORDS]
                    return txt, title, tags_list
            except:
                pass
    except:
        pass
    return None, None, None


def text_stemming(text):
    """lemmatizetion of the given word in the text"""
    stemmed = []
    for word in text.split(" "):
        lm = LMTZR.lemmatize(word, 'v')
        if lm == "":
            lm = word
        if lm == word:
            lm = LMTZR.lemmatize(word)
        stemmed += [lm]
    return " ".join(stemmed)

def texts_stemming(test_set_q):
    """stem the text"""
    res = []
    for text in test_set_q:
        res += [text_stemming(text)]
    return res


def return_trained_lsa_sims(q1, q2, size, computed_models):
    """return the similarity between 2 question ids based on already trained data if size is 0,
    otherwise build the model too and then return the similarity score"""
    if computed_models is None:
        print "starting return_trained_lsa_sims"
        t = time.time()
        test_set_q, test_set_t, tags = get_random_test_data(size)
        print "done get_test_data %f" % (time.time() - t)
        t = time.time()
        test_set_q = map(text_stemming, test_set_q)
        print "done test_set_q %f" % (time.time() - t)
        t = time.time()
        test_set_t = map(text_stemming, test_set_t)

        print "done test_set_t %f" % (time.time() - t)
    else:
        test_set_c = test_set_t = test_set_q = []

    test_set_q_checked, test_set_t_checked, not_in_db_checked, tags_checked = get_test_data([q1, q2])
    test_set_q_checked = map(text_stemming, test_set_q_checked)
    test_set_t_checked = map(text_stemming, test_set_t_checked)

    cos_q = trained_lsa_with_tfidf(test_set_q_checked, test_set_q, "q", 500, computed_models)
    if computed_models is None:
        test_set_c = []
        for i, q_txt in enumerate(test_set_q):
            test_set_c.append(test_set_t[i] + " " + q_txt)

    test_set_c_checked = []
    for i, q_txt in enumerate(test_set_q_checked):
        test_set_c_checked.append(test_set_t_checked[i] + " " + q_txt)
    del test_set_q
    cos_t = trained_lsa_with_tfidf(test_set_t_checked, test_set_t, "t", 500, computed_models)
    del test_set_t

    cos_c = trained_lsa_with_tfidf(test_set_c_checked, test_set_c, "c", 500, computed_models)
    del test_set_c

    return cos_t[0], cos_q[0], cos_c[0], []


def return_trained_lsa_from_ids(wanted, ids, size, computed_models):
    """returns the cos_dis of all parts"""
    if computed_models is None:
        print "starting return_trained_lsa_sims"
        t = time.time()
        test_set_q, test_set_t, tags = get_random_test_data(size)
        print "done get_test_data %f" % (time.time() - t)
        t = time.time()
        test_set_q = map(text_stemming, test_set_q)
        print "done test_set_q %f" % (time.time() - t)
        t = time.time()
        test_set_t = map(text_stemming, test_set_t)

        print "done test_set_t %f" % (time.time() - t)
    else:
        test_set_c = test_set_t = test_set_q = []

    test_set_q_checked, test_set_t_checked, not_in_db_checked, tags_checked = get_test_data([wanted] + ids)
    test_set_q_checked = map(text_stemming, test_set_q_checked)
    test_set_t_checked = map(text_stemming, test_set_t_checked)

    cos_q = trained_lsa_with_tfidf(test_set_q_checked, test_set_q, "q", 500, computed_models)
    if computed_models is None:
        test_set_c = []
        for i, q_txt in enumerate(test_set_q):
            test_set_c.append(test_set_t[i] + " " + q_txt)

    test_set_c_checked = []
    for i, q_txt in enumerate(test_set_q_checked):
        test_set_c_checked.append(test_set_t_checked[i] + " " + q_txt)
    del test_set_q
    cos_t = trained_lsa_with_tfidf(test_set_t_checked, test_set_t, "t", 500, computed_models)
    del test_set_t

    cos_c = trained_lsa_with_tfidf(test_set_c_checked, test_set_c, "c", 500, computed_models)
    del test_set_c
    return cos_t, cos_q, cos_c, [], not_in_db_checked


def trained_lsa_with_tfidf(texts, documents, name, dimensions, computed_models):
    """return the similarity of two texts, based on already exist model
    texts - 2 compared texts
    documents - if empty load from disc,
        otherwise train and save to disc the model
    name - which model are we working with:
        t - title
        q - question
        c - combination
    dimensions - number of features to LSA model
    computed_models - if None - build or read from pickle
        otherwise - class that contains the models
    """
    if not computed_models is None:
        lsa = computed_models.get_model_by_name(name)
    elif len(documents) == 0:
        t = time.time()
        with open(name, "rb") as reader:
            lsa = pickle.load(reader)
        print "read %f" % (time.time()-t)
    else:
        t = time.time()
        vectorizer = TfidfVectorizer(stop_words=STOP_WORDS+LANG_WORDS)
        svd = TruncatedSVD(dimensions)
        lsa = make_pipeline(vectorizer, svd, Normalizer(copy=False))
        lsa.fit(documents)
        print "Model building: %f" % (time.time()-t)
        #save lsa and vectorizer
        t = time.time()
        with open(name, "wb") as writer:
            pickle.dump(lsa, writer, pickle.HIGHEST_PROTOCOL)
        print "write %f" % (time.time()-t)

    transformation = lsa.transform(texts)
    cx = lambda a, b: round(np.inner(a, b)/(LA.norm(a)*LA.norm(b)), 3)

    retval = []
    for i in range(1, len(transformation)):
        if LA.norm(transformation[0])*LA.norm(transformation[i]) != 0:
            retval += [cx(transformation[0], transformation[i])]
        else:
            print "error in div"
            retval += [0]
    return retval


def perform_tfidf(wanted, ids, file_name=None):
    """check the similarity between wanted and ids using tf.idf and cosine similarity
    return 2 sorted list (by the most related question)
    first - is the ids
    second - is the corresponding cosine similarity score.
    prints to file more detailed information"""
    # not in real use
    # score weights
    title_w = 1/float(2)
    content_w = 1/float(4)
    combination_w = 1/float(4)

    test_set_q, test_set_t, not_in_db, tags = get_test_data([wanted] + ids)
    test_set_q = texts_stemming(test_set_q)
    test_set_t = texts_stemming(test_set_t)
    test_set_c = []
    for i, q_txt in enumerate(test_set_q):
        test_set_c.append(test_set_t[i] + " " + q_txt)
    new_ids = [wanted] + [e for e in ids if not e in not_in_db]
    common_tags = []
    for x in xrange(len(new_ids)):
        common_tags += [len(set(new_ids[0]).intersection(new_ids[x]))]
    cos_dis_q, add_to_print = similarity_check(test_set_q, new_ids)
    cos_dis_t, add_to_print = similarity_check(test_set_t, new_ids)
    cos_dis_c, add_to_print = similarity_check(test_set_c, new_ids)
    total_score = []
    for i in xrange(len(cos_dis_t)):
        total_score += [title_w * cos_dis_t[i] + content_w * cos_dis_q[i] + combination_w * cos_dis_c[i]]
    x = np.array(total_score)
    related_docs_indices = x.argsort()[::-1]
    rel_docs_ids = []
    rel_docs_cos = []
    rel_docs_tags = []
    for place in related_docs_indices:
        if new_ids[place] != wanted:
            rel_docs_ids += [new_ids[place]]
            rel_docs_cos += [total_score[place]]
            rel_docs_tags += [common_tags[place]]
    return rel_docs_ids, rel_docs_cos, rel_docs_tags

def similarity_check(test_set, new_ids):
    """given set find the most similar to the first entry"""
    #CountVectorizer
    vectorizer = CountVectorizer(stop_words=STOP_WORDS + LANG_WORDS)
    trainVectorizerArray = vectorizer.fit_transform(test_set).toarray()
    #DELETE
    tfidf = TfidfTransformer()
    trainVectorizerArray = tfidf.fit_transform(trainVectorizerArray).toarray()

    cx = lambda a, b: round(np.inner(a, b)/(LA.norm(a)*LA.norm(b)), 3)
    vector = trainVectorizerArray[0]
    cos_dis = []
    for i, testV in enumerate(trainVectorizerArray):
        if LA.norm(vector)*LA.norm(testV) != 0:
            cos_dis.append(cx(vector, testV))
        else:
            print "error in div"
            cos_dis.append(0)
    x = np.array(cos_dis)
    related_docs_indices = x.argsort()[::-1]
    add_to_print = ["closest docs ", " ,".join([str(e) for e in related_docs_indices.tolist()])]
    t = 0
    while t < len(cos_dis) - 1 and cos_dis[related_docs_indices[t]] > 0.999:
        t += 1
    add_to_print += ["best cousin similarity is " + str(cos_dis[related_docs_indices[t]]) + " with q_id " + str(new_ids[related_docs_indices[t]])]
    return cos_dis, add_to_print


if __name__ == "__main__":
    get_random_test_data(1000000)
