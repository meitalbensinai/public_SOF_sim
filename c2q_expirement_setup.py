__author__ = 'Meital'
from consts import *
from process_one_question import get_possible_snippets
from code_to_question import get_match_questions

# setup for the regression tests (code2qTest.py) for the code to question process (generic)

FILL = False


def __main__():
    if FILL:
        C2Q_EXP_DB.drop()
        C2Q_EXP_DB.ensure_index("Id", unique=True)
        posts_with_code = POSTS_DB.find({"answers.Body": {"$regex": "/.*<code>.*/"}}, timeout=False)
        m = 0
        for question in posts_with_code:
            if m == 50:
                break
            q_id = question['Id']
            snippets = get_possible_snippets(q_id, True)
            if not snippets is None:
                for code, lang, ans_id in snippets:
                    C2Q_EXP_DB.insert({"Id": m, "q_id": q_id, "a_id": ans_id, "code": code, "lang": lang})
                    m += 1
                    break
    else:
        pass_all = True
        for entry in C2Q_EXP_DB.find({}):
            matched = get_match_questions(entry['code'])
            if entry['q_id'] in matched:
                print "PASS", len(matched)
                if len(matched) > 5:
                    print entry['code']
            else:
                print "FAIL"
                pass_all = False
        print "PASS ALL" if pass_all else "EPIC FAIL"


if __name__ == "__main__":
    __main__()