__author__ = 'Meital'
# consts file, many of the consts are writen again in other files, pay attention!
from utils import *
from pymongo import MongoClient
import time
import subprocess
import re
from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer


# try to connect to mongo
try:
    client = MongoClient()
except:
    #open server if not available
    print "opening mongo.."
    print subprocess.Popen("mongod")
    time.sleep(5)
    print "mongo is up!"
    client = MongoClient()

#db consts
DB = client.sof
TEST_DB = client.test
WEB_MAIN_DB = client.web
CODE_DB = client.code

WEB_PAIRS_DB = WEB_MAIN_DB.pairs_new
MAPPING_DB = DB.mapping
POSTS_DB = DB.posts
CLOSE_Q_DB = DB.qmatch
TRAIN_DB = DB.train_set
TFIDF_DB = DB.tfidf
PAIRS_DB = DB.pairs
CHECKED_DB = DB.checked
WEB_DB = DB.web
TEST_WEB_DB = DB.test_web
WEB_RES_DB = DB.web_res
WEB_ERROR_DB = DB.web_errors
CACHE_DB = DB.cache_sep20
C2Q_EXP_DB = DB.c2q_exp
CR_DOCS_DB = TEST_DB.cr_docs
CR_QUERIES_DB = TEST_DB.cr_queries

#re that recognizes code sections
CODE_OUT_RE = re.compile(r'<code>.*?</code>', re.DOTALL)
QUOTE_OUT_RE = re.compile(r'<blockquote>.*?</blockquote>', re.DOTALL)

#stop words
LANG_WORDS = ['python', 'java', 'c#', 'c++', 'scala', 'ruby', 'c', 'perl']  # temp list
STOP_WORDS = stopwords.words('english') + ['im', 'pythonic']
with open(r"C:\Users\Meital\OneDrive for Business\python_workspace\SOF_similarities\pl.txt", "rb") as reader:
    LANG_WORDS = [a.replace("\r\n", "").lower() for a in reader.readlines() if " " not in a and not a.startswith("-")]
PROMPT_TEXT = '>>>'
INDEX_DIR = "indexdir"
INDEX_DIR_CODE = "indexdir_code"
INDEX_DIR_TEST = "indexdir_test"
MIN_CODE_LEN = 35
MAX_CODE_LEN = 600

BASE_FILE_NAME = r"results/res_for_id_"

LMTZR = WordNetLemmatizer()

SET_OF_CLASSES = ["file", "list", "number", "string", "dictionary", "bool", "object", "set"]
from pprint import pprint

#TODO: chang if I want the old db!!!
INDEX_DIR_CODE = "indexdir_code_new"
DB = client.sof_new
POSTS_DB = DB.posts
