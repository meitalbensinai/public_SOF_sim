__author__ = 'Meital'
# used to build the original pairs db
from consts import *
from from_id_to_related_ids import build_query,find_query,find_the_closest, find_the_closest_NEW
from process_one_question import get_possible_snippets
from similarity_2_questions64 import LsaModel


SCORE_SIM_THRESHOLD = 0.4
SCORE_DIFF_THRESHOLD = 0.04

MAX_DIFFERENCE_CODE_SIZE = 4
DB_SIZE = 6000
DB_SIZE = 100000

BIG_DB = client.big
PAIRS_DB_NEW = BIG_DB['pairs_100k']
CHECKED_DB_NEW = BIG_DB['checked_new']


def score_to_place(score):
    """similar, totally different, less than 0.1, less than 0.2, less than 0.3, out of bound"""
    if score > SCORE_SIM_THRESHOLD:
        return 0
    if score < SCORE_DIFF_THRESHOLD:
        return 1
    if score < 0.1:
        return 2
    if score < 0.2:
        return 3
    if score < 0.3:
        return 4
    return 5


def extract_matches():
    """extract pairs of snippets to db, some of the lines are commented out due two second use in different scenarios"""
    models = LsaModel()
    models.load_models()
    PAIRS_DB_NEW.ensure_index("Id", unique=True)
    CACHE_DB.ensure_index("Id", unique=True)
    CHECKED_DB.ensure_index("Id")
    first_id = PAIRS_DB_NEW.count()
    new_id = first_id
    # similar, totally different, less than 0.1, less than 0.2, less than 0.3
    #counters = [DB_SIZE / 2, DB_SIZE / 4, DB_SIZE / 12, DB_SIZE / 12, DB_SIZE / 12, 0]
    #ids_to_look_for = ['104420', '3319586', '3371879', '613183', '89228', '952914', '2068372', '480214', '1207406', '4836710', '38987', '682367', '1450393', '22676', '519633', '82831', '931092', '354038', '2793150', '363681', '109383', '153724', '2784514', '4216745', '3481828', '469695', '1555262', '140131', '46898', '921262', '160970', '1359689', '80476', '1625234', '240546', '2885173', '5585779', '2808535', '41107', '724043', '139076', '304268', '999172', '4205980', '122105', '1128723', '1102891', '428918', '693997', '525212', '225337']
    #ids_to_look_for = [e['Id'] for e in POSTS_DB.find()]
    ids_to_look_for = []
    i = 0
    for x in POSTS_DB.find({}):
        i += 1
        if i < 100000:
            continue
        if len(ids_to_look_for) > 1000000:
            break
        ids_to_look_for.append(x["Id"])
    print "done loading ids"
    for num_q, q_id in enumerate(ids_to_look_for):
        if new_id > 100000:
            break
        all_possible_similarities = {}
        #all_possible_difference = {}
        if CHECKED_DB_NEW.find({"Id": q_id}).count() > 0:
            print "skip"
            continue
        relevant_q_id = []
        CHECKED_DB_NEW.insert({"Id": q_id})
        if CACHE_DB.find({"Id": q_id}).count() > 0:
            relevant_q_id = CACHE_DB.find({"Id": q_id})[0]["Ids"]
        codes = get_possible_snippets(q_id)
        if codes is None or codes == []:
            print "DROOPED:", q_id
            continue
        if relevant_q_id == []:
            query_example = build_query(q_id)
            relevant_q_id = find_query(query_example, q_id)
            CACHE_DB.insert({"Id": q_id, "Ids": relevant_q_id})
        """try:
            not_relevant_q_id = ids_to_look_for[num_q + 1:]
        except:
            not_relevant_q_id = []
        related_ids, scores = find_the_closest(q_id, relevant_q_id, None)"""
        scored_dict, not_in_db = find_the_closest_NEW(q_id, relevant_q_id, models)
        print scored_dict
        for j, rel_id in enumerate([e for e in relevant_q_id if e not in not_in_db]):
            codes2 = get_possible_snippets(rel_id)
            if codes2 is None or codes2 == []:
                continue
            try:
                all_possible_similarities[rel_id] = (codes2, scored_dict[rel_id])
            except:
                print "error loading score"

        """
        try:
            #not_related_ids, bad_scores = find_the_closest(q_id, not_relevant_q_id, None)
            scored_dict2 = find_the_closest_NEW(q_id, not_relevant_q_id, models)
        except:
            print "problem"
            continue

        not_related_ids = not_related_ids[::-1]
        bad_scores = bad_scores[::-1]
        for j, rel_id in enumerate(related_ids):
            codes2 = get_possible_snippets(rel_id)
            if codes2 is None or codes2 == []:
                continue
            all_possible_similarities[rel_id] = (codes2, scores[j])
        for j, not_rel_id in enumerate(not_related_ids):
            codes2 = get_possible_snippets(not_rel_id)
            if codes2 is None or codes2 == []:
                continue
            all_possible_difference[not_rel_id] = (codes2, bad_scores[j])
        """
        pairs = []
        for i, code1 in enumerate(codes):
            for code2 in codes[i + 1:]:
                pairs += [(code1, code2, (1, 1, 1), q_id)]
        for code1 in codes:
            pairs += build_pairs(code1, all_possible_similarities)
            #pairs += build_pairs(code1, all_possible_difference)

        id1 = q_id
        for pair in pairs:
            code1 = pair[0][0]
            code2 = pair[1][0]
            lang1 = pair[0][1]
            lang2 = pair[1][1]
            similarity = pair[2]
            id2 = pair[3]
            if len(code1) > MAX_DIFFERENCE_CODE_SIZE * len(code2) or len(code2) > MAX_DIFFERENCE_CODE_SIZE * len(code1):
                continue
            """
            if counters[score_to_place(float(similarity))] == 0:
                continue
            counters[score_to_place(float(similarity))] -= 1"""
            #WEB_DB.insert({"Id": new_id, "code1": code1, "code2": code2, "id1": id1, "id2": id2, "similarity": similarity, "lang1": lang1, "lang2": lang2})
            PAIRS_DB_NEW.insert({"Id": new_id, "code1": code1, "code2": code2, "id1": id1, "id2": id2, "t": similarity[0], "q": similarity[1], "c": similarity[2], "lang1": lang1, "lang2": lang2})
            new_id += 1
    print "done!", new_id


def build_pairs(code, all_possible):
    """build possible pairs from the code and its matches"""
    pairs = []
    for key in all_possible.keys():
        score = all_possible[key][1]
        for code2 in all_possible[key][0]:
            pairs += [(code, code2, score, key)]
    return pairs


def extract_matches_03():
    """ extract only matches between 0.3-0.4,
        aims to make the db full, to correct previous problems.."""
    NEW_WEB = client.web
    PAIRS_NEW_DB = NEW_WEB.add03
    PAIRS_OLD_DB = NEW_WEB.pairs_new
    PAIRS_NEW_DB.ensure_index("Id", unique=True)
    first_id = PAIRS_OLD_DB.count()
    new_id = first_id
    counter = DB_SIZE / 12
    ids_to_look_for = ['104420', '3319586', '3371879', '613183', '89228', '952914', '2068372', '480214', '1207406', '4836710', '38987', '682367', '1450393', '22676', '519633', '82831', '931092', '354038', '2793150', '363681', '109383', '153724', '2784514', '4216745', '3481828', '469695', '1555262', '140131', '46898', '921262', '160970', '1359689', '80476', '1625234', '240546', '2885173', '5585779', '2808535', '41107', '724043', '139076', '304268', '999172', '4205980', '122105', '1128723', '1102891', '428918', '693997', '525212', '225337']
    for num_q, q_id in enumerate(ids_to_look_for):
        all_possible_similarities = {}
        relevant_q_id = []
        if CACHE_DB.find({"Id": q_id}).count() > 0:
            relevant_q_id = CACHE_DB.find({"Id": q_id})[0]["Ids"]
        codes = get_possible_snippets(q_id)
        if codes is None or codes == []:
            print "DROOPED:", q_id
            continue
        if relevant_q_id == []:
            query_example = build_query(q_id)
            relevant_q_id = find_query(query_example, q_id)
            CACHE_DB.insert({"Id": q_id, "Ids": relevant_q_id})
        related_ids, scores = find_the_closest(q_id, relevant_q_id, None)
        for j, rel_id in enumerate(related_ids):
            codes2 = get_possible_snippets(rel_id)
            if codes2 is None or codes2 == []:
                continue
            codes2 = [codes2[0]]
            if scores[j] < 0.3 or scores[j] > 0.4:
                continue
            all_possible_similarities[rel_id] = (codes2, scores[j])
        pairs = []
        for code1 in codes:
            try:
                pairs += build_pairs(code1, all_possible_similarities)
            except:
                pass
        id1 = q_id
        for pair in pairs:
            code1 = pair[0][0]
            code2 = pair[1][0]
            lang1 = pair[0][1]
            lang2 = pair[1][1]
            similarity = str(pair[2])
            id2 = pair[3]
            if len(code1) > MAX_DIFFERENCE_CODE_SIZE * len(code2) or len(code2) > MAX_DIFFERENCE_CODE_SIZE * len(code1):
                continue
            if counter == 0:
                break
            counter -= 1
            PAIRS_NEW_DB.insert({"Id": new_id, "code1": code1, "code2": code2, "id1": id1, "id2": id2, "similarity": similarity, "lang1": lang1, "lang2": lang2})
            new_id += 1
            print new_id
    print "done!",

if __name__ == "__main__":
    extract_matches()