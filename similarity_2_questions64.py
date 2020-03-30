__author__ = 'Meital'
# main db scoring file, used to get the similarity values for db of pairs.
from consts import *
from lsa_compare import return_trained_lsa_sims, text_stemming, trained_lsa_with_tfidf
try:
   import cPickle as pickle
except:
   import pickle

DB_RES = client.web
WEB_PAIRS_DB = WEB_MAIN_DB.pairs_new

"""Web results"""
TIMED_DB = DB_RES['sep28']

# many different dbs names that are in use
ALL_LSA_DB = DB_RES['nov10lsa_tfidf_fixed_300']
ALL_LSA_DB = DB_RES['nov15lsa_tfidf_50k_300']
ALL_LSA_DB = DB_RES['nov18lsa_tfidf_1M_300']

ALL_LSA_DB = DB_RES['nov18lsa_tfidf_1M_100']

#ptobobaly not true, i think it is the same as 300
ALL_LSA_DB = DB_RES['dec1lsa_tfidf_1M_100']

ALL_LSA_DB = DB_RES['dec12lsa_tfidf_1M_100']


ALL_LSA_DB = DB_RES['dec12lsa_tfidf_1M_500']


ALL_LSA_DB = DB_RES['dec14lsa_tfidf_1M_800']

ALL_LSA_DB = DB_RES['dec14lsa_tfidf_1K_100']
ALL_LSA_DB = DB_RES['dec18lsa_tfidf_1K_100']
ALL_LSA_DB = DB_RES['dec18lsa-rand2_tfidf_1K_100']
ALL_LSA_DB = DB_RES['dec18lsa-18-30_tfidf_1K_100']
ALL_LSA_DB = DB_RES['dec18lsa-18-50_tfidf_1K_100']
ALL_LSA_DB = DB_RES['dec19lsa-10:30_tfidf_1K_100']
ALL_LSA_DB = DB_RES['dec19lsa-11:00_tfidf_1K_100']

ALL_LSA_DB = DB_RES['dec19lsa_tfidf_432_100']
ALL_LSA_DB = DB_RES['dec19lsa_tfidf_1M_1000']


"""pairs"""
WEB_PAIRS_DB = DB_RES['pairs_new']
BASE_FOLDER = r'C:\Users\Meital\OneDrive for Business\python_workspace\text_usage_64'

# t,q, c is 1M, 500 features
class LsaModel:
    """class that holds the 3 LSA models"""
    def __init__(self):
        self.title_model = None
        self.question_model = None
        self.combination_model = None

    def load_models(self):
        """load all models"""
        def load_model(name):
            """load specific model by name:
            t - title
            q - question
            c - content"""
            t = time.time()
            try:
                with open(BASE_FOLDER + "\\" + name, "rb") as model:
                    lsa = pickle.load(model)
                print "read %f" % (time.time() - t)
                return lsa
            except Exception as e:
                print "can't read"
                print e
                return_trained_lsa_sims('104420', '2612802', 1000000, None)
                return self.load_models()
        self.title_model = load_model("t1M")
        print "t"
        self.question_model = load_model("q1M")
        print "q"
        self.combination_model = load_model("c1M")
        print "c"

    def get_model_by_name(self, name):
        """get specific (already loaded) model by name. call first too load_models"""
        if name.startswith("t"):
            return self.title_model
        if name.startswith("q"):
            return self.question_model
        if name.startswith("c"):
            return self.combination_model
        return None


def get_sims(q1, q2, computed_models=None):
    """return the similarity between 2 question, title - content - both"""
    t = time.time()
    print "before trained_lsa_sims %f " % (time.time() - t)
    title, content, both, tags = return_trained_lsa_sims(q1, q2, 0, computed_models)
    return title, content, both, tags


def two_texts_sim(txt1, txt2, name):
    """given two texts return their similarity"""
    txt1 = text_stemming(no_punctuation(txt1))
    txt2 = text_stemming(no_punctuation(txt2))
    models = LsaModel()
    models.load_models()
    test_set_t_checked = [txt1, txt2]
    cos_q = trained_lsa_with_tfidf(test_set_t_checked, [], name, 500, models)
    print cos_q


def build_all_scores_db():
    """build new db that contains the similarity score of each (title, content, title+content)
    for each pair, will be used for find the best linear interpolation of them"""
    ALL_LSA_DB.ensure_index("Id", unique=True)
    db_results = WEB_PAIRS_DB.find({}, timeout=False) #TIMED_DB.find({}, timeout=False)  #
    t = time.time()
    models = LsaModel()
    models.load_models()
    print "load models done %f " % (time.time() - t)
    for res in db_results:
        pair_id = res["Id"]
        if ALL_LSA_DB.find({"Id": pair_id}).count():
            print "skip"
            continue
        entry = WEB_PAIRS_DB.find({"Id": int(pair_id)})[0]
        q1 = entry['id1']
        q2 = entry['id2']
        # TODO: pay attention, if i will add any kind of treatment to code from the same question, needs to be deleted.
        if q1 == q2:
            title, content, both, tags = (1, 1, 1, 1)
        else:
            title, content, both, tags = get_sims(q1, q2, models)
        print "id:", pair_id, "old:", entry["similarity"], "new:", title, content, both
        try:
            ALL_LSA_DB.insert({"Id": pair_id, "title_sim": str(title), "content_sim": str(content), "combined_sim": str(both), "common_tags": tags})
        except:
            pass
    db_results.close()

if __name__ == "__main__":
    #print get_sims('104420', '2612802')
    two_texts_sim("sort", "order", "t")
    #build_all_scores_db()
    print "test"