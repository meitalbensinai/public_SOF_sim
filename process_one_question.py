__author__ = 'Meital'
# the process steps that may be taken given one question id
from consts import *
from get_code import get_ans_code_by_q_id

THRESHOLD_Q = 3
THRESHOLD_A = 3
BLACK_LIST_TAGS = []


def get_orig_possible_snippets(q_id, filter_score=True):
    """given question id, returns the list of snippets
     that are candidates for similarity"""
    try:
        question = POSTS_DB.find({"Id": str(q_id)})[0]
    except:
        return None
    if int(question['Score']) < THRESHOLD_Q and filter_score:
        return None
    tags = [e.replace(">","") for e in question['Tags'].split("<")[1:]]
    q_lang = ""
    for tag in tags:
        if tag in BLACK_LIST_TAGS and filter_score:
            #print "unwanted tags is included"
            return None
        if tag in LANG_WORDS and q_lang == "":
            q_lang = tag
    ans_dict = get_ans_code_by_q_id(str(q_id))
    snippets = []
    q_txt = clean_line(CODE_OUT_RE.sub("", question['Body'] + question['Title'])).replace("\n\n", "\n")
    if q_lang == "":
        q_lang = try_to_find_lang(q_txt)
    for ans_id in ans_dict.keys():
        lang = q_lang
        (text, codes, score, body) = ans_dict[ans_id]
        a_lang = try_to_find_lang(text)
        if not a_lang == "":
            lang = a_lang
        if score < THRESHOLD_A and filter_score:
            continue
        in_line_code = []
        code_number = 0
        for line in body.split("\n"):
            if "<code>" in line and not line.split("<code>")[0] in ["<pre>","<p>"]:
                in_line_code += [code_number]
            elif "</code>" in line and not line.split("</code>")[1] in ["</pre>", "</p>"]:
                in_line_code += [code_number]
            if "</code>" in line:
                code_number += 1
        filterd_codes = [e for num, e in enumerate(codes) if num not in in_line_code]
        # the too long or short codes are filtered separately to avoid elimination of important parts of the code
        if len(filterd_codes) == 1 and MIN_CODE_LEN < len(filterd_codes[0]) < MAX_CODE_LEN:
            snippets += [(filterd_codes[0], lang, ans_id)]
    return snippets


def get_possible_snippets(q_id, filter_score=True):
    """given question id, returns the list of snippets
     that are candidates for similarity"""
    try:
        question = POSTS_DB.find({"Id": str(q_id)})[0]
    except:
        #print "The question is not in the db, sorry and goodbye!"
        return None
    if int(question['Score']) < THRESHOLD_Q and filter_score:
        #print q_id, "has score of", question['Score'], "and this is too low"
        return None
    tags = [e.replace(">","") for e in question['Tags'].split("<")[1:]]
    q_lang = ""
    for tag in tags:
        if tag in BLACK_LIST_TAGS and filter_score:
            #print "unwanted tags is included"
            return None
        if tag in LANG_WORDS and q_lang == "":
            q_lang = tag
    ans_dict = get_ans_code_by_q_id(str(q_id))
    snippets = []
    q_txt = no_punctuation(clean_line(CODE_OUT_RE.sub("", question['Body'] + question['Title'])).replace("\n\n", "\n"))
    if q_lang == "":
        q_lang = try_to_find_lang(q_txt)
    for ans_id in ans_dict.keys():
        lang = q_lang
        (text, codes, score, body) = ans_dict[ans_id]
        a_lang = try_to_find_lang(text)
        if not a_lang == "":
            lang = a_lang
        if score < THRESHOLD_A and filter_score:
            continue
        in_line_code = []
        code_number = 0
        for line in body.split("\n"):
            if "<code>" in line and not line.split("<code>")[0] in ["<pre>","<p>"]:
                in_line_code += [code_number]
            elif "</code>" in line and not line.split("</code>")[1] in ["</pre>", "</p>"]:
                in_line_code += [code_number]
            if "</code>" in line:
                code_number += 1
        filterd_codes = [e for num, e in enumerate(codes) if num not in in_line_code]
        # the too long or short codes are filtered separately to avoid elimination of important parts of the code
        if len(filterd_codes) == 1 and MIN_CODE_LEN < len(filterd_codes[0]) < MAX_CODE_LEN:
            snippets += [(filterd_codes[0], lang, ans_id)]
    return snippets


def try_to_find_lang(txt):
    """find lang words in txt"""
    words = re.split('\n| ', txt)
    for lang in LANG_WORDS:
        if lang in words:
            return lang
    return ""


if __name__ == "__main__":
    #q_id = raw_input("insert question id: ")
    snippets = get_possible_snippets(962953)
    for snippet in snippets:
        print snippet
        print "________"