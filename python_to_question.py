__author__ = 'Meital'
# python specific syntactic similarity, based on pre computed index (to build it from scratch set the FIRST flag to True
from whoosh.fields import SchemaClass, TEXT, ID
import os, os.path
from whoosh.filedb.filestore import FileStorage
import shutil
from consts import *
from process_one_question import get_orig_possible_snippets
from collections import OrderedDict
from alignment.sequence import Sequence
from alignment.vocabulary import Vocabulary
from alignment.sequencealigner import SimpleScoring, GlobalSequenceAligner

# whether to build the index
FIRST = False

#whether to work with TEST_COLLECTION or whole index
TEST_COLLECTION = False

#number of returned docs from whoosh "more like" query
DOCS_TO_FIND = 200

#aligment scores
MATCH_SCORE = 2
MISMATCH_SCORE = -1
GAP_SCORE = -2

MAX_DIFF_IN_LINES = 2

PYTHON_SEARCH_DIR = "indexdir_code_python_new"
PYTHON_SEARCH_DIR_TEST = "indexdir_code_python_test"

SYNTAX_PAIRS_PYTHON = WEB_DB['syntax_python_pairs']

#--------------------------------------

import ast
from tokenize import generate_tokens, untokenize, INDENT
from cStringIO import StringIO
from pprint import pprint
import visit_ast_to_string as v


# _dedent borrowed from the myhdl package (www.myhdl.org)
def dedent(s):
    """Dedent python code string. not working that well"""
    result = [t[:2] for t in generate_tokens(StringIO(s).readline)]
    # set initial indent to 0 if any
    if result[0][0] == INDENT:
        result[0] = (INDENT, '')
    return untokenize(result)


def parse_code(code_to_parse):
    """parse the code to create its representative string"""
    code_to_parse = code_to_parse.strip()
    try:
        code_to_parse = dedent(code_to_parse)
    except:
        print "error"
        return ""

    def parse_in_loops(c):
        while True:
            try:
                parsed_ast = ast.parse(c)
                return parsed_ast
            except Exception as e:
                if "invalid syntax (<unknown>, line" in str(e):
                    cl = c.split("\n")
                    prob_line = int(str(e).split("invalid syntax (<unknown>, line ")[1].split(")")[0])
                    if cl[prob_line - 1].startswith(">>>"):
                        c = "\n".join(
                            cl[:prob_line - 1] + [cl[prob_line - 1].replace(">>>", "").strip()] + cl[prob_line:])
                    else:
                        c = "\n".join(cl[:prob_line - 1] + cl[prob_line:])
                else:
                    print e
                    break
        return None

    p1 = parse_in_loops(code_to_parse)
    if p1 is None:
        return ""
    visitor = v.AnalysisNodeVisitor()
    visitor.visit(p1)
    return " ".join(visitor.string)


#--------------------------------------



class MySchema(SchemaClass):
    """schema used for building the index"""
    code = TEXT(stored=True)
    orig_code = TEXT(stored=True)
    question_id = TEXT(stored=True)
    answer_id = TEXT(stored=True)
    language = TEXT(stored=True)


class TestSchema(SchemaClass):
    """schema used for building the index"""
    code = TEXT(stored=True)
    orig_code = TEXT(stored=True)
    question_id = TEXT(stored=True)
    answer_id = TEXT(stored=True)
    language = TEXT(stored=True)
    code_id = TEXT(stored=True)


def build_index():
    """building the index from scratch"""
    print "building index.."

    index_dir = PYTHON_SEARCH_DIR
    if TEST_COLLECTION:
        index_dir = PYTHON_SEARCH_DIR_TEST
        #CR_DOCS_DB.drop()
        #CR_DOCS_DB.ensure_index("code_id", unique=True)
    if os.path.exists(index_dir):
        shutil.rmtree(index_dir)
    os.mkdir(index_dir)
    schema = get_schema()
    storage = FileStorage(index_dir)
    ix = storage.create_index(schema)
    w = ix.writer()
    print "finding posts.."
    posts_with_code = POSTS_DB.find({"answers.Body": {"$regex": "/.*<code>.*/"}}, timeout=False)
    print "adding files.."
    q = 0
    for i, question in enumerate(posts_with_code):
        q += add_doc(w, question)
        if i % 1000 == 0 and not i == 0:
            print "commit number:", str(i / 1000), "with", q, "codes"
            w.commit()
            w = ix.writer()

    w.commit()
    posts_with_code.close()
    print "the index was built!"
    return ix


def get_schema():
    """returns the schema used"""
    if TEST_COLLECTION:
        return TestSchema()
    return MySchema()




def add_doc(writer, entry):
    """adds doc to index"""
    m = 0
    q_id = entry['Id']
    snippets = get_orig_possible_snippets(q_id, False)
    for code, lang, ans_id in snippets:
        if not lang == "python":
            continue
        abstract_code = parse_code(code)
        print "AST:", abstract_code
        if abstract_code == "":
            continue
        writer.add_document(question_id=q_id, answer_id=ans_id, code=return_unicode(abstract_code), orig_code=return_unicode(code),
                            language=return_unicode(lang))
        m += 1
    return m


def search_doc(ix, to_search):
    """finds similar docs in index"""
    with ix.searcher() as searcher:
        results = searcher.more_like(None, 'code', text=return_unicode(to_search), top=DOCS_TO_FIND)
        info = []
        for res in results:
            q_id = res.fields()['question_id']
            score = res.score
            code = res.fields()['code'].replace("'", "")
            info += [(q_id, res, code)]
        return info


def index_word_pairs(word, seq):
    """return paris of (word, index in seq)"""
    indices = [i for i, x in enumerate(seq) if x == word]
    res = []
    for i in indices:
        res += [(word, i)]
    return res


def match_word_sorted(code1, code2):
    """return the max scored alignment between the two input codes"""
    list1 = code1.split(" ")
    list2 = code2.split(" ")
    set1 = set(list1)
    set2 = set(list2)
    common_words = set1 | set2
    try:
        common_words.remove("")
    except:
        pass

    words1 = []
    words2 = []
    for word in common_words:
        words1 += index_word_pairs(word, list1)
        words2 += index_word_pairs(word, list2)
    sorted1 = sorted(words1, key=lambda t: t[1])
    sorted2 = sorted(words2, key=lambda t: t[1])

    a = Sequence(sorted1)
    b = Sequence(sorted2)
    v = Vocabulary()
    a_encoded = v.encodeSequence(a)
    b_encoded = v.encodeSequence(b)
    scoring = SimpleScoring(MATCH_SCORE, MISMATCH_SCORE)
    aligner = GlobalSequenceAligner(scoring, GAP_SCORE)
    score, encoders = aligner.align(a_encoded, b_encoded, backtrace=True)
    max_score = 0
    for i, encoded in enumerate(encoders):
        alignment = v.decodeSequenceAlignment(encoded)
        #print alignment
        #print 'Alignment score:', alignment.score
        #print 'Percent identity:', alignment.percentIdentity()
        if alignment.score > max_score:
            max_score = alignment.score
    return max_score


def get_code_length(code):
    """get the number of real code lines"""
    ignore = ["{", "}", "(", ")", ";", ":"]
    for ig in ignore:
        code = code.replace(ig, "")
    return len([e.strip() for e in code.split("\n") if
                (not e.strip() == "") and (not e.strip() == u"'") and (not e.strip() == u"u'")])


def from_code_to_question(to_find):
    """givan code fragment, returns an OrderdDict
    of the related question with its aligment score"""
    index_dir = PYTHON_SEARCH_DIR
    if TEST_COLLECTION:
        index_dir = PYTHON_SEARCH_DIR_TEST
    storage = FileStorage(index_dir)
    ix = storage.open_index()
    abs_code = parse_code(to_find)
    print abs_code
    if abs_code == "":
        raise Exception
    question_score = search_doc(ix, abs_code)
    scores = {}
    question_to_codes = {}
    wanted_tokens = len(abs_code.split(" "))
    for i, option in enumerate(question_score):
        if abs(len(option[2].split(" ")) - wanted_tokens) > 8:
            continue
        score = match_word_sorted(abs_code, option[2])
        scores[option[0]] = max(scores.get(option[0], 0), score)
        question_to_codes[option[0]] = question_to_codes.get(option[0], []) + [(option[1]['orig_code'], score)]
    return OrderedDict(sorted((scores.items()), key=lambda t: -int(t[1]))), wanted_tokens, question_score, question_to_codes


def get_match_questions(to_find):
    """return the ids of matching question to given code"""
    res_dict, tokens, q_scores, orig_codes = from_code_to_question(to_find)
    res = []
    for key, value in res_dict.items():
        if float(value) > 1.8 * tokens:
            for code in orig_codes[key]:
                if code[1] == value:
                    res += [(key, code[0], code[1])]
    return res


def build_pairs_db():
    """build the pairs db, used for the python specific syntactic similarity evaluation"""
    SYNTAX_PAIRS_PYTHON.drop()
    SYNTAX_PAIRS_PYTHON.ensure_index("Id", unique=True)
    pair_id = 0
    posts_with_code = POSTS_DB.find({"answers.Body": {"$regex": "/.*<code>.*/"}}, timeout=False)
    for i, entry in enumerate(posts_with_code):
        if pair_id > 1000:
            break
        q_id = entry['Id']
        snippets = get_orig_possible_snippets(q_id, False)
        try:
            for code, lang, ans_id in snippets:
                if not lang == "python":
                    continue
                for m in get_match_questions(code):
                        print {"Id": pair_id, "code1": code, "code2": m[1], "score": m[2], "question1": q_id, "question2": m[0]}
                        SYNTAX_PAIRS_PYTHON.insert({"Id": pair_id, "code1": code, "code2": m[1], "score": m[2], "question1": q_id, "question2": m[0]})
                        pair_id += 1
        except Exception as e:
            print "EXP:", e



def __main__():
    index_dir = PYTHON_SEARCH_DIR
    if TEST_COLLECTION:
        index_dir = PYTHON_SEARCH_DIR_TEST
    if FIRST:
        ix = build_index()
    else:
        storage = FileStorage(index_dir)
        ix = storage.open_index()
    """
    with open("code_ex.txt", "rb") as reader:
        to_find = reader.read()
    t = time.time()
    get_match_questions(to_find)
    print time.time() - t
    for x in get_match_questions(to_find):
        print "found:", x
    """
    #build_pairs_db()
    #print len(list(ix.searcher().documents()))




def remove_code_punc(code):
    """remove punctuation from code fragment,
        with refinement with the knowledge that is a code"""

    sec = code
    together = set(["==", "&&", "<>", "||"])
    spacing = set(["+", "-", "*", "/", "!", "^"])
    exclude = set(
        ["=", "|", "&", "[", "]", "\r", "\n", "(", ")", "{", "}", ":", ",", ";", ".", '"', "'", ">", "<", "#", "%", "$",
         "~", "\\", "?"])
    new_sec = ""
    i = 0
    while i < len(sec):
        try:
            if sec[i:i + 1] in together:
                new_sec += " " + sec[i:i + 1] + " "
                i += 2
                continue
        except:
            print "last"
        if sec[i] in exclude:
            new_sec += " "
        elif sec[i] in spacing:
            new_sec += " " + sec[i] + " "
        else:
            new_sec += sec[i]
        i += 1
    new_sec = new_sec.replace("  ", " ")
    return new_sec



if __name__ == "__main__":
    __main__()