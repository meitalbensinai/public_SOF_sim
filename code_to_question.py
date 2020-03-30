__author__ = 'Meital'
# generic code to question in Stackoverflow - generic semantic similarity

from whoosh.fields import SchemaClass, TEXT, ID
import os, os.path
from whoosh.filedb.filestore import FileStorage
import shutil
from consts import *
from process_one_question import get_possible_snippets
from collections import OrderedDict
from alignment.sequence import Sequence
from alignment.vocabulary import Vocabulary
from alignment.sequencealigner import SimpleScoring, GlobalSequenceAligner
import pickle

#whether to build the index
FIRST = False

#whether to work with TEST_COLLECTION or whole index
#TODO: remember to change when I'm done with the CR evaluation
TEST_COLLECTION = False

#number of returned docs from whoosh "more like" query
DOCS_TO_FIND = 200

#aligment scores
MATCH_SCORE = 2
MISMATCH_SCORE = -1
GAP_SCORE = -2

MAX_DIFF_IN_LINES = 2


class MySchema(SchemaClass):
    """schema used for building the index"""
    code = TEXT(stored=True)
    question_id = TEXT(stored=True)
    answer_id = TEXT(stored=True)
    language = TEXT(stored=True)


class TestSchema(SchemaClass):
    """schema used for building the index"""
    code = TEXT(stored=True)
    question_id = TEXT(stored=True)
    answer_id = TEXT(stored=True)
    language = TEXT(stored=True)
    code_id = TEXT(stored=True)


def add_from_file(writer):
    """used to add code fragments from an external file"""
    with open("to_test_db", "rb") as reader:
        lines = reader.readlines()
    place = "out"
    codes = []
    code = []
    for i, line in enumerate(lines):
        if "<--NEW CODE-->" in line:
            if "lang" in place:
                codes += [(q_id, ans_id, "".join(code), lang)]
            place = "q_id"
        elif "<--language" in line:
            place = "lang"
            lang = line.split("<--language=")[1].split("-->")[0]
        elif "q_id" in place:
            q_id = line.split("<--question_id=")[1].split("-->")[0]
            place = "a_id"
        elif "a_id" in place:
            ans_id = line.split("<--ans_id=")[1].split("-->")[0]
            place = "code"
            code = []
        elif "code" in place:
            code += [line]
    codes += [(q_id, ans_id, "".join(code), lang)]
    for next_id, entry in enumerate(codes):
        (q_id, ans_id, code, lang) = entry
        print next_id, entry
        writer.add_document(question_id=return_unicode(int(q_id)), answer_id=return_unicode(int(ans_id)), code=return_unicode(code), language=return_unicode(lang),code_id=return_unicode(next_id))
        CR_DOCS_DB.insert({"question_id": return_unicode(int(q_id)), "answer_id": return_unicode(int(ans_id)), "code": return_unicode(code), "language": return_unicode(lang), "code_id": return_unicode(next_id)})
    return len(codes)


def build_index():
    """building the index from scratch"""
    print "building index.."

    index_dir = INDEX_DIR_CODE
    if TEST_COLLECTION:
        index_dir = INDEX_DIR_TEST
        CR_DOCS_DB.drop()
        CR_DOCS_DB.ensure_index("code_id", unique=True)
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
    q = add_from_file(w) if TEST_COLLECTION else 0
    for i, question in enumerate(posts_with_code):
        if TEST_COLLECTION:
            q += add_one_code(w, question, q)
            if q > 999:
                break
        else:
            q += add_doc(w, question)
            if i % 1000 == 0 and not i == 0:
                print "commit number:", str(i/1000), "with", q, "codes"
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


def add_one_code(writer, entry, next_id):
    """add one question to the search engine"""
    q_id = entry['Id']
    snippets = get_possible_snippets(q_id, True)
    if not snippets is None:
        for code, lang, ans_id in snippets:
            writer.add_document(question_id=q_id, answer_id=ans_id, code=return_unicode(code), language=return_unicode(lang),code_id=return_unicode(next_id))
            CR_DOCS_DB.insert({"question_id": q_id, "answer_id": ans_id, "code": return_unicode(code), "language": return_unicode(lang), "code_id": return_unicode(next_id)})
            print return_unicode(next_id)
            return 1
    return 0


def add_doc(writer, entry):
    """adds doc to index"""
    m = 0
    q_id = entry['Id']
    snippets = get_possible_snippets(q_id, False)
    for code, lang, ans_id in snippets:
        writer.add_document(question_id=q_id, answer_id=ans_id, code=return_unicode(code), language=return_unicode(lang))
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
            code = res.fields()['code']
            info += [(q_id, res, code)]
        return info


#not in current use
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
    common_words = set1 & set2
    try:
        common_words.remove("")
    except:
        pass

    words_to_index = {}
    for word in common_words:
        in1 = list1.index(word)
        in2 = list2.index(word)
        words_to_index[word] = (in1, in2)
    sorted1 = OrderedDict(sorted(words_to_index.items(), key=lambda t: t[1][0])).keys()
    sorted2 = OrderedDict(sorted(words_to_index.items(), key=lambda t: t[1][1])).keys()

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
        if alignment.score > max_score:
            max_score = alignment.score
    return max_score


def get_code_length(code):
    """get the number of real code lines"""
    ignore = ["{", "}", "(", ")", ";", ":"]
    for ig in ignore:
        code = code.replace(ig, "")
    return len([e.strip() for e in code.split("\n") if (not e.strip() == "") and (not e.strip() == u"'") and (not e.strip() == u"u'")])


def fast_from_code_to_question(to_find, ix_saved):
    """faster - given code fragment, returns an OrderdDict
    of the related question with its alignment score, ix is provided to save time"""
    question_score = search_doc(ix_saved, to_find)
    scores = {}
    wanted_len = get_code_length(to_find)
    wanted_tokens = len(set(remove_code_punc(to_find).split(" ")))
    for i, option in enumerate(question_score):
        code_len = get_code_length(option[2])
        if abs(code_len - wanted_len) > MAX_DIFF_IN_LINES:
            continue
        score = match_word_sorted(remove_code_punc(to_find), remove_code_punc(option[2]))
        scores[option[0]] = max(scores.get(option[0], 0), score)

    return OrderedDict(sorted(scores.items(), key=lambda t: -int(t[1]))), wanted_tokens, question_score


def from_code_to_question(to_find):
    """given code fragment, returns an OrderdDict
    of the related question with its alignment score"""
    index_dir = INDEX_DIR_CODE
    if TEST_COLLECTION:
        index_dir = INDEX_DIR_TEST
    storage = FileStorage(index_dir)
    ix = storage.open_index()
    question_score = search_doc(ix, to_find)
    scores = {}
    wanted_len = get_code_length(to_find)
    wanted_tokens = len(set(remove_code_punc(to_find).split(" ")))
    #print "wanted length", wanted_len, "wanted tokens", wanted_tokens
    for i, option in enumerate(question_score):
        code_len = get_code_length(option[2])
        if abs(code_len - wanted_len) > MAX_DIFF_IN_LINES:
            #print "bad length", code_len
            continue
        score = match_word_sorted(remove_code_punc(to_find), remove_code_punc(option[2]))
        scores[option[0]] = max(scores.get(option[0], 0), score)
        #print option

    # optional: add normalization
    return OrderedDict(sorted(scores.items(), key=lambda t: -int(t[1]))), wanted_tokens, question_score


def get_match_questions(to_find):
    """return the ids of matching question to given code"""
    res_dict, tokens, q_scores = from_code_to_question(to_find)
    res = []
    for key, value in res_dict.items():
        # or use any other "smarter" way
        if float(value) > float(4)/5 * tokens:
            res += [key]
    return res


def __main__():
    index_dir = INDEX_DIR_CODE
    if TEST_COLLECTION:
        index_dir = INDEX_DIR_TEST
    if FIRST:
        ix = build_index()
    else:
        storage = FileStorage(index_dir)
        ix = storage.open_index()
    with open("code_ex.txt", "rb") as reader:
        to_find = reader.read()
    t = time.time()
    get_match_questions(to_find)
    print time.time() - t
    for x in get_match_questions(to_find):
        print "found:", x


def remove_code_punc(code):
    """remove punctuation from code fragment,
        with refinement with the knowledge that is a code"""
    sec = code
    together = set(["==", "&&", "<>", "||"])
    spacing = set(["+", "-", "*", "/", "!", "^"])
    exclude = set(["=", "|", "&", "[", "]", "\r", "\n", "(", ")", "{", "}", ":", ",", ";", ".", '"', "'", ">", "<", "#", "%", "$", "~", "\\", "?"])
    new_sec = ""
    i = 0
    while i < len(sec):
        try:
            if sec[i:i + 1] in together:
                new_sec += " " + sec[i:i+1] + " "
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


def check_db_matches():
    """created in order to build the importance of data graph.. probably should be changed in order to be reused"""
    FIRST_RUN = False
    #ALL_FILE = "all_queries_big"
    #DB_FILE = "all_dbs_big"
    ALL_FILE = "all_queries"
    DB_FILE = "all_dbs"
    START_FROM = "number"
    ALL_NUM = "all_num_from_new"
    ALL_NUM = "all_num_from_4_5_full_17"

    ALL_FIXED_q = "all_fixed_queries" + str(17)
    ALL_FIXED_dbs = "all_fixed_dbs" + str(17)
    biggest = 20
    max_db_size = 20
    all_queries = {}
    db = [{}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}]
    found = [0] * biggest
    ret_val = []
    if FIRST_RUN:
        #raw_input("are you sure you want to rewrite the db?!")
        storage_main = FileStorage(INDEX_DIR_CODE)
        ix_main = storage_main.open_index()
        try:
            """
            with open(START_FROM, "rb") as file_h:
                (curr_db, count, db_sizes) = pickle.load(file_h)
            with open(ALL_FIXED_q, "rb") as file_h:
                all_queries = pickle.load(file_h)
            with open(ALL_FIXED_dbs, "rb") as file_h:
                db = pickle.load(file_h)
            print len(all_queries.keys())
            print "Real size", [len(e.keys()) for e in db]
            print "left", db_sizes
            print curr_db, count
            """
            with open(START_FROM, "rb") as file_h:
                (curr_db, count, db_sizes) = pickle.load(file_h)
            print "read", curr_db, count
            with open(ALL_FILE+str(curr_db - 1), "rb") as file_h:
                all_queries = pickle.load(file_h)
            with open(DB_FILE+str(curr_db - 1), "rb") as file_h:
                db = pickle.load(file_h)
            print "Real size", [len(e.keys()) for e in db]
        except:
            curr_db = 0
            count = 0
            db_sizes = [2 ** i for i in range(1, biggest + 1)]
        new_count = 0
        print "start reading posts"
        q_db = POSTS_DB.find({}, timeout=False)
        print "done reading posts"
        print "start with", curr_db
        for question in q_db:
            if curr_db == max_db_size:
                print "break"
                break
            new_count += 1
            if new_count < count:
                continue
            if db_sizes[curr_db] % 1000 == 0:
                print "BUILD:", curr_db, "I'm Alive, more", db_sizes[curr_db], "togo!"
            snips = get_possible_snippets(question['Id'])
            if snips is None or len(snips) == 0:
                continue
            (db[curr_db])[question['Id']] = snips[0]
            db_sizes = db_sizes[:curr_db] + [e-1 for e in db_sizes[curr_db:]]
            if db_sizes[curr_db] == 0:
                t = time.time()
                print "find matches for", curr_db, "size is", len(db[curr_db].keys())
                for place, key in enumerate(db[curr_db].keys()):
                    if place % 1000 == 0:
                        print "FIND: I'm Alive", place
                    code = db[curr_db][key][0]
                    res_dict, tokens, q_scores = fast_from_code_to_question(code, ix_main)
                    if all_queries.get(key, None) is None:
                        all_queries[key] = (tokens, res_dict)
                curr_db += 1
                try:
                    print "saved", time.time() - t
                    with open(ALL_FILE + str(curr_db), "wb") as file_h:
                        pickle.dump(all_queries, file_h)
                    with open(DB_FILE + str(curr_db), "wb") as file_h:
                        pickle.dump(db, file_h)
                    with open(START_FROM, "wb") as file_h:
                        pickle.dump((curr_db, new_count, db_sizes), file_h)
                except:
                    print "to much to write"
                print "start", 2 ** (curr_db + 1)
        q_db.close()
        num = 0
    else:
        print "reading files.."
        t = time.time()
        """with open(ALL_FILE+str(max_db_size), "rb") as file_h:
            all_queries = pickle.load(file_h)
        with open(DB_FILE+str(max_db_size), "rb") as file_h:
            db = pickle.load(file_h)"""
        with open(ALL_FIXED_q, "rb") as file_h:
            all_queries = pickle.load(file_h)
        with open(ALL_FIXED_dbs, "rb") as file_h:
            db = pickle.load(file_h)
        print "done reading", time.time() - t
        print [len(e.keys()) for e in db]

        try:
            with open(ALL_NUM, "rb") as file_h:
                num, found = pickle.load(file_h)
            print "read", num, found
        except:
            num = 0

    curr_num = 0
    print num, len(all_queries.keys())
    for query in all_queries.keys():
        curr_num += 1
        if curr_num < num:
            continue
        if curr_num % 1000 == 0:
            print "MATCHES: I'M Alive!", curr_num, query

        matches = get_matches(query, all_queries[query])
        flag_f = False
        for match in matches:
            if flag_f:
                break
            for i in range(len(db)):
                if match in db[i].keys() and query in db[i].keys():
                    found[i] += 1
                    flag_f = True
                    break

    if curr_num - 1 > num:
        with open(ALL_NUM, "wb") as file_h:
            pickle.dump((curr_num, found), file_h)
    print found
    """
    #saved in _n
    small_db = [0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 8] # 3/5
    small_db = [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 4] # 4/5
    for i, val in enumerate(small_db):
        try:
            found[i] += val
        except:
            print "shorter db"

    print found"""
    for i in range(len(found) - 1):
        found[i + 1] += found[i]
    print(found)
    for place, i in enumerate([2 ** i for i in range(1, max_db_size + 1)]):
        ret_val.append(float(found[place])/i * 100)
    print ret_val


def get_matches(q_id, res):
    """get the code matches, using any similarity criteria"""
    tokens = res[0]
    opt_dict = res[1]
    ret_val = []
    for opt in opt_dict.keys():
        if opt == q_id:
            continue
        if float(opt_dict[opt]) > float(4)/5 * tokens:
            ret_val.append(opt)
    return ret_val


def fix_db():
    """not in use anymore, used for combination between fragmented objects"""
    ALL_FIXED_q = "all_fixed_queries"
    ALL_FIXED_dbs = "all_fixed_dbs"
    print "reading files.."
    with open("all_queries_up1111", "rb") as file_h:
        all_queries11 = pickle.load(file_h)
    with open("all_dbs_up1111", "rb") as file_h:
        dbs11 = pickle.load(file_h)
    print [len(e.keys()) for e in dbs11]
    with open("all_queries17", "rb") as file_h:
        all_queries = pickle.load(file_h)
    with open("all_dbs17", "rb") as file_h:
        dbs = pickle.load(file_h)

    print "done reading.."
    print "all len1", len(all_queries.keys())
    dbs = dbs11[0:11] + dbs[11:]

    print [len(e.keys()) for e in dbs]
    all_queries.update(all_queries11)
    print "all len2", len(all_queries.keys())
    print "done update"
    del all_queries11
    del dbs11
    print "reading files 2.."
    with open("all_queries16", "rb") as file_h:
        all_queries16 = pickle.load(file_h)
    with open("all_dbs16", "rb") as file_h:
        dbs16 = pickle.load(file_h)
    print "done reading 2"
    dbs = dbs[:15] + [dbs16[15]] + dbs[16:]
    print [len(e.keys()) for e in dbs]
    all_queries.update(all_queries16)
    print "done update2"
    print "all len3", len(all_queries.keys())
    with open(ALL_FIXED_q + str(17), "wb") as file_h:
        pickle.dump(all_queries, file_h)
    with open(ALL_FIXED_dbs + str(17), "wb") as file_h:
        pickle.dump(dbs, file_h)
    print "saved!"


def number_matches():
    """return the average and maximum values of matches in db"""
    ALL_FIXED_q = "all_fixed_queries" + str(17)
    ALL_FIXED_dbs = "all_fixed_dbs" + str(17)
    try:
        with open("matches", "rb") as file_h:
            db_length = pickle.load(file_h)
    except:
        print "reading files.."
        t = time.time()
        """with open(ALL_FILE+str(max_db_size), "rb") as file_h:
            all_queries = pickle.load(file_h)
        with open(DB_FILE+str(max_db_size), "rb") as file_h:
            db = pickle.load(file_h)"""
        with open(ALL_FIXED_q, "rb") as file_h:
            all_queries = pickle.load(file_h)
        with open(ALL_FIXED_dbs, "rb") as file_h:
            db = pickle.load(file_h)
        print "done reading", time.time() - t
        print [len(e.keys()) for e in db]
        print len(all_queries.keys())
        db_length = {}
        curr_num = 0
        for query in all_queries.keys():
            curr_num += 1

            if curr_num % 1000 == 0:
                print "MATCHES: I'M Alive!", curr_num, query

            matches = get_matches(query, all_queries[query])
            db_length[query] = len(matches)
            print "save data"
        with open("matches", "wb") as file_h:
            pickle.dump(db_length, file_h)
            print "saved!"
    #pprint(db_length)
    flag = False
    sorted_d = OrderedDict(sorted(db_length.items(), key=lambda x: x[1]))
    for x in sorted_d:
        if not flag:
            print "FIRST", sorted_d[x]
            flag = True
    print "LAST", sorted_d[x]
    print "AVG:", float(sum(db_length.values()))/len(db_length.keys())


if __name__ == "__main__":
    number_matches()
    #check_db_matches()
    #__main__()