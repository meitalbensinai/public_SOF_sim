__author__ = 'Meital'
from consts import *
from bs4 import BeautifulSoup


def get_ans_code_by_q_id(q_id):
    """returns all the code snippets from the question's answers
    in dictionary where the key is the answer's id and the corresponding
    value is a tuple (content, codes, score) when
    content - the text of the answer (without code)
    codes - list of all code snippets
    score - the score of the answer
    full answer - the body of the answer"""
    q = POSTS_DB.find({'Id': q_id})
    try:
        answers = q[0]['answers']
    except:
        return {}
    a_dict = {}
    for answer in answers:
        codes = get_code(answer['Body'])
        a_id = answer['Id']
        score = answer['Score']
        txt = no_punctuation(clean_line(QUOTE_OUT_RE.sub("", CODE_OUT_RE.sub("", answer['Body']))).replace("\n\n","\n"))
        a_dict[a_id] = (txt, codes, int(score), answer['Body'])
    return a_dict


def get_code(content):
    """return code frafments from text"""
    soup = BeautifulSoup(content)
    c = soup.findAll('code')
    codes = []
    for frag in c:
        code = frag.prettify(formatter=None)
        """
        raw_code = []
        #if it is python code, remove prompt sign
        if PROMPT_TEXT in code:
            for code_line in code.split("\n"):
                if PROMPT_TEXT in code_line:
                    raw_code += [code_line.split(PROMPT_TEXT)[1]]
                elif "..." in code_line:
                    raw_code += [code_line.split("...")[1]]
            code = "\n".join([e for e in raw_code if e != "\n"])
        """
        codes += [code.replace("<code>", "").replace("</code>", "")]
    return codes

if __name__ == "__main__":
    d = get_ans_code_by_q_id("613183")
    for key in d:
        print key
        print d[key][0]
        print d[key][1]
        print d[key][2]
