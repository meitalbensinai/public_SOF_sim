__author__ = 'Meital'
# calc resulst using 55 pairwise tags (generic syntactic similarity)
from consts import *
from python_to_question import from_code_to_question


TAMIR_DB = client.tamir
RES_DB = TAMIR_DB.res
QUERIES_DB = TAMIR_DB.querires
QUERY2CODE = TAMIR_DB.query2code
INTIAL_DB = TAMIR_DB.initial_db


def calc_recall(tp, fn, fp, tn):
    """returns recall value"""
    try:
        return float(tp) / (tp + fn) * 100
    except:
        return 0


def calc_precision(tp, fn, fp, tn):
    """returns precision value"""
    try:
        return float(tp)/(tp + fp) * 100
    except:
        return 0


def calc_accuracy(tp, fn, fp, tn):
    """returns accuracy value"""
    try:
        return float(tp + tn) / (tp + fp + fn + tn) * 100
    except:
        return 0


def build_query2match_db():
    """build the db in the following structure:
        query: code_id, code, matches"""
    QUERY2CODE.ensure_index("code_id", unique=True)
    for query in QUERIES_DB.find({}):
        new_entry = query
        code_id = query["code_id"]
        all_matches = []
        for entry in RES_DB.find({"code_" + str(code_id): "1"}):
            all_matches += [(entry['code'], entry['code_id'])]
        new_entry['matches'] = all_matches
        QUERY2CODE.insert(new_entry)


def is_match(score, tokens):
    return float(score) > float(4)/5 * tokens


def is_match_python(score, tokens):
    return float(score) > 1.8 * tokens


def test_results():
    """get the precision and recall of the CR system based on Tamir's tags"""
    tp, fn, fp, tn = (0, 0, 0, 0)
    for query in QUERY2CODE.find({}):
        print query
        q_code = query['code']
        match_codes = []
        res_dict, tokens_num, q_scores = from_code_to_question(q_code)
        #pprint(q_scores)

        for option in res_dict.iteritems():
            if is_match(option[1], tokens_num):
                match_codes += [e[2] for e in q_scores if e[0] == option[0]]
            else:
                break

        baseline_match = [e[0] for e in query['matches']]
        #print match_codes
        #print baseline_match
        for db_val in RES_DB.find({}):
            code = db_val['code']
            if code in match_codes and code in baseline_match:
                tp += 1
            elif code in match_codes and code not in baseline_match:
                fp += 1
            elif code not in match_codes and code in baseline_match:
                fn += 1
            elif code not in match_codes and code not in baseline_match:
                tn += 1

    precision = calc_precision(tp, fn, fp, tn)
    recall = calc_recall(tp, fn, fp, tn)
    accuracy = calc_accuracy(tp, fn, fp, tn)
    print precision, recall, accuracy
    return precision, recall, accuracy


def test_results_python():
    # not in use
    """get the precision and recall of the CR system based on Tamir's tags"""
    tp, fn, fp, tn = (0, 0, 0, 0)
    counter = 0
    for query in QUERY2CODE.find({}):
        q_code = query['code']
        code_id = query['code_id']
        match_codes = []
        try:
            res_dict, tokens_num, q_scores, orig_codes = from_code_to_question(q_code)
            counter += 1
        except:
            continue
        for option in res_dict.iteritems():
            if is_match_python(option[1], tokens_num):
                match_codes += [e[0].replace("\r", "").strip() for e in orig_codes[option[0]]]
            else:
                break
        baseline_match = [e[0].replace("\r", "").strip() for e in query['matches']]
        print "__________"
        print "The code:", q_code
        print match_codes
        print baseline_match
        print "__________"
        for db_val in RES_DB.find({}):
            code = db_val['code']
            if code in match_codes and code in baseline_match:
                tp += 1
            elif code in match_codes and code not in baseline_match:
                fp += 1
            elif code not in match_codes and code in baseline_match:
                fn += 1
            elif code not in match_codes and code not in baseline_match:
                tn += 1
    print "counter:", counter
    precision = calc_precision(tp, fn, fp, tn)
    recall = calc_recall(tp, fn, fp, tn)
    accuracy = calc_accuracy(tp, fn, fp, tn)
    print tp, fn, fp, tn
    print precision, recall, accuracy
    return precision, recall, accuracy


def main():
    #build_query2match_db()
    test_results_python()

if __name__ == "__main__":
    main()