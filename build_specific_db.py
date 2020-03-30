__author__ = 'Meital'
from consts import *
from from_id_to_related_ids import build_query,find_query,find_the_closest
from process_one_question import get_possible_snippets
import random
from python_types_impl import get_types as get_python_types
from java_types_impl import extract_types as get_java_types
from java_types_impl import build_class_Hierarchy

MAX_DIFFERENCE_CODE_SIZE = 4

#To avoid damage in the original pairs builder - local consts:
NEW_WEB = client.web
JAVA_NEW_DB = NEW_WEB.java_db_22oct


def score_to_place_tfidf(score):
    """deviation of the results,
    used for getting specific amount of pairs from each range
    suitable for tfidf results."""
    if score > 0.4:
        return 0
    if score > 0.3:
        return 1
    if score > 0.2:
        return 2
    if score > 0.1:
        return 3
    return 4


def score_to_place_lsa(score):
    """deviation of the results,
    used for getting specific amount of pairs from each range
    suitable for LSA results."""
    if score == 1:
        return 0
    if score > 0.5:
        return 1
    if score > 0.4:
        return 2
    if score > 0.3:
        return 3
    if score > 0.2:
        return 4
    if score > 0.1:
        return 5
    return 6


def is_expected_tags(expected, tags):
    """return whether the tags may fit to wanted question structure"""
    stop_tags = [] #["<jsp>","<pass-by","<jvm>","<jsf>","<ajax>", "<eclipse>", "<ide>","<debugging>", "<exe>", "jar",
                 # "jlabel", "ruby", "hibernate", "aop", "annotations", "java-ee", "spring", "programming","jre", "windows", "linux", "<static>","class", "<runtime>", "classpath", "compile", "environment"]
    for i in expected:
        if "<"+i+">" in tags:
            return True
    for tag in stop_tags:
        if tag in tags:
            return False
    return True


def java_db_extractor():
    """ build java-java db"""
    JAVA_NEW_DB.drop()
    JAVA_NEW_DB.ensure_index("Id", unique=True)
    first_id = JAVA_NEW_DB.count()
    new_id = first_id
    counters = [80, 40] + [20] * 3
    db_posts = set(['1462834', '4448370', '1534804', '7414299', '7111651','415953', '15038174', '1670862', '2920315', '8368111', '363681', '109383', '3481828', '326390', '4216745', '5585779', '2591098', '4716503', '2592501', '10786042', '1235179', '275944', '9655181', '1519736', '1892765', '1395551', '4040001', '3324717', '6524196', '2441501', '960431', '5287538', '923863', '415953', '473282', '1264709', '1816673', '4105331', '101439', '124671', '5958169', '9617069', '4640034', '1765579', '200746', '2435156', '304268']) #POSTS_DB.find({}, timeout=False)
    for num, q_id in enumerate(db_posts):
        print "q:", num
        try:
            res = POSTS_DB.find({"Id":q_id})[0]
        except:
            continue
        #q_id = res["Id"]
        tags = res["Tags"]
        if not is_expected_tags(["java"], tags):
            continue
        print "java!"
        all_possible_similarities = {}
        relevant_q_id = []
        if CACHE_DB.find({"Id": q_id}).count() > 0:
            relevant_q_id = CACHE_DB.find({"Id": q_id})[0]["Ids"]
        codes = get_possible_snippets(q_id)
        if codes is None or codes == []:
            print "DROOPED:", q_id
            continue
        #added to get only one code fragment from each pair of questions
        codes = codes[0:min(2, len(codes))]
        if relevant_q_id == []:
            query_example = build_query(q_id)
            relevant_q_id = find_query(query_example, q_id)
            CACHE_DB.insert({"Id": q_id, "Ids": relevant_q_id})
        related_ids, scores = find_the_closest(q_id, relevant_q_id, None)
        for j, rel_id in enumerate(related_ids):
            try:
                tags = POSTS_DB.find({"Id": rel_id})[0]['Tags']
            except:
                continue
            if not is_expected_tags(["java"], tags):
                continue
            codes2 = get_possible_snippets(rel_id)
            if codes2 is None or codes2 == []:
                continue
            #added to get only one code fragment from each pair of questions
            codes2 = [codes2[0]]
            all_possible_similarities[rel_id] = (codes2, scores[j])
        pairs = []
        for i, code1 in enumerate(codes):
            for code2 in codes[i + 1:]:
                pairs += [(code1, code2, 1, q_id)]
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
            if counters[score_to_place_tfidf(float(similarity))] == 0:
                continue
            counters[score_to_place_tfidf(float(similarity))] -= 1
            JAVA_NEW_DB.insert({"Id": new_id, "code1": code1, "code2": code2, "id1": id1, "id2": id2, "similarity": similarity, "lang1": lang1, "lang2": lang2})
            new_id += 1
            print new_id, counters
            if done(counters):
                break
    print "done!", counters


def get_types(code, lang, all_classes):
    """get types, using the appropriate function, chosen by the PL"""
    # note - the older version of type extraction, the newer version is using the AST's which is much better approach!!
    if lang == "python":
        return get_python_types(code)
    return get_java_types(code, all_classes)


def done(counters):
    """the counter list contains only 0 - done!"""
    for i in counters:
        if not i == 0:
            return False
    return True


def build_pairs(code, all_possible):
    """create the pairs using the code and all the possile matches"""
    pairs = []
    r = 2
    for i, key in enumerate(all_possible.keys()):
        if i < r:
            score = all_possible[key][1]
            for code2 in all_possible[key][0]:
                pairs += [(code, code2, score, key)]
    return pairs


def spec_extractor(lan_list):
    """build db with the given languages"""
    SPECIFIC_DB = NEW_WEB.java_python_25oct
    SPECIFIC_DB = NEW_WEB.java_python_7Nov
    SPECIFIC_DB = NEW_WEB.java_python_8Nov
    SPECIFIC_DB = NEW_WEB.java_python_9Nov

    ALL_LSA_DB = NEW_WEB['oct14lsa_tfidf_fixed_q_all']
    SPECIFIC_DB.drop()
    SPECIFIC_DB.ensure_index("Id", unique=True)
    all_classes = build_class_Hierarchy()
    first_id = SPECIFIC_DB.count()
    new_id = first_id
    counters = [0, 150, 0, 0, 0, 0, 0]
    db_pairs = WEB_PAIRS_DB.find({})
    counter = 0
    for res in db_pairs:
        counter += 1
        if not counter % 6 == 0:
            continue
        pair_id = res["Id"]
        id1 = res["id1"]
        id2 = res["id2"]
        code1 = res["code1"]
        code2 = res["code2"]
        lang1 = res["lang1"]
        lang2 = res["lang2"]
        ok = [False, False]
        for i in lan_list:
            if lang1 == i:
                ok[0] = True
            if lang2 == i:
                ok[1] = True
        if not ok[0] or not ok[1]:
            continue

        title_w = 0.4
        content_w = 0
        combination_w = 0.6
        from_w = ALL_LSA_DB.find({"Id": pair_id})[0]
        no_neg = lambda x: float(from_w[x]) if float(from_w[x]) > 0 else 0
        similarity = title_w * no_neg('title_sim') + content_w * no_neg('content_sim') + combination_w * no_neg('combined_sim')
        if counters[score_to_place_lsa(float(similarity))] == 0:
            continue
        counters[score_to_place_lsa(float(similarity))] -= 1
        types1 = get_types(code1, lang1, all_classes)
        types2 = get_types(code2, lang2, all_classes)
        print types1, types2
        SPECIFIC_DB.insert({"Id": new_id, "code1": code1, "code2": code2, "id1": id1, "id2": id2, "similarity": similarity, "lang1": lang1, "lang2": lang2, "orig_pair_id": pair_id, "types1": types1, "types2": types2})
        new_id += 1
        print new_id, counters
        if done(counters):
            print "finish"
            break
    print "done!", counters


if __name__ == "__main__":
    #java_db_extractor()
    spec_extractor(["java", "python"])
