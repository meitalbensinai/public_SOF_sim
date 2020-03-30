__author__ = 'Meital'
import subprocess
from consts import *
from lsa_compare import get_entry_data
import os
import java_ast as j
import python_ast as p
from pymongo import Connection


# local dbs, were created using different configurations
DB_RES = client.web
WEIGHTS_DB = DB_RES['adw_jan23_titles']
WEIGHTS_DB = DB_RES['adw_feb2_titles_lep']
WEIGHTS_DB = DB_RES['adw_both_feb7']
WEIGHTS_DB = DB_RES['spec_adw_both_feb12']
WEIGHTS_DB = DB_RES['adw_both_feb12']

WEIGHTS_DB = DB_RES['spec_adw_both_mar1']
WEIGHTS_DB = DB_RES['adw_both_mar7']

# 100k pairs dbs
##################
DB_BIG = client.big
WEIGHTS_DB = DB_BIG['adw_both_mar9']
##################

#WEIGHTS_DB = DB_RES['adw_jan23_content']
#WEIGHTS_DB = DB_RES['adw_jan23_combination']
"""Web results"""
TIMED_DB = DB_RES['sep28']
TIMED_DB = DB_RES['dec14_ltdow']
TIMED_DB = DB_RES['feb7']


# remote dbs
client = Connection('mongodb://meitalbs:n40h10@ds063929.mongolab.com:63929/af_ltdow-meitalbensinai')
CUR_DB = client.get_default_database()
TIMED_DB = CUR_DB["results_with_related"]


# 100k pairs dbs
#####################
TIMED_DB = DB_BIG['pairs_100k']
SAVED_SIGS = DB_BIG['sigs_mar10']
#####################

IN1_FILE = r"C:\Users\Meital\OneDrive for Business\python_workspace\SOF_similarities\tmp\title1"
IN2_FILE = r"C:\Users\Meital\OneDrive for Business\python_workspace\SOF_similarities\tmp\title2"
OUT_FILE = r"C:\Users\Meital\OneDrive for Business\python_workspace\SOF_similarities\tmp\adw_output"


def call_jar(in_file1, in_file2, out_file):
    """call ADW jar as called from eclipse, use that way only from performance concerns"""
    cd = os.getcwd()
    cmd = r'"C:\Program Files\Java\jdk1.8.0_25\bin\javaw.exe" -Dfile.encoding=Cp1255 -classpath "C:\Users\Meital\git\ADW\target\classes;C:\Users\Meital\git\ADW\lib\SEWordSim.jar;C:\Users\Meital\.m2\repository\com\google\collections\google-collections\1.0\google-collections-1.0.jar;C:\Users\Meital\.m2\repository\net\sourceforge\collections\collections-generic\4.01\collections-generic-4.01.jar;C:\Users\Meital\.m2\repository\commons-logging\commons-logging\1.1.3\commons-logging-1.1.3.jar;C:\Users\Meital\.m2\repository\commons-configuration\commons-configuration\1.5\commons-configuration-1.5.jar;C:\Users\Meital\.m2\repository\commons-collections\commons-collections\3.2\commons-collections-3.2.jar;C:\Users\Meital\.m2\repository\commons-lang\commons-lang\2.3\commons-lang-2.3.jar;C:\Users\Meital\.m2\repository\commons-digester\commons-digester\1.8\commons-digester-1.8.jar;C:\Users\Meital\.m2\repository\commons-beanutils\commons-beanutils\1.7.0\commons-beanutils-1.7.0.jar;C:\Users\Meital\.m2\repository\commons-beanutils\commons-beanutils-core\1.7.0\commons-beanutils-core-1.7.0.jar;C:\Users\Meital\git\ADW\lib\jlt-2.0.0.jar;C:\Users\Meital\.m2\repository\junit\junit\4.11\junit-4.11.jar;C:\Users\Meital\.m2\repository\org\hamcrest\hamcrest-core\1.3\hamcrest-core-1.3.jar;C:\Users\Meital\.m2\repository\net\sf\trove4j\trove4j\3.0.3\trove4j-3.0.3.jar;C:\Users\Meital\.m2\repository\edu\stanford\nlp\stanford-corenlp\3.5.0\stanford-corenlp-3.5.0.jar;C:\Users\Meital\.m2\repository\com\io7m\xom\xom\1.2.10\xom-1.2.10.jar;C:\Users\Meital\.m2\repository\xml-apis\xml-apis\1.3.03\xml-apis-1.3.03.jar;C:\Users\Meital\.m2\repository\xerces\xercesImpl\2.8.0\xercesImpl-2.8.0.jar;C:\Users\Meital\.m2\repository\xalan\xalan\2.7.0\xalan-2.7.0.jar;C:\Users\Meital\.m2\repository\joda-time\joda-time\2.1\joda-time-2.1.jar;C:\Users\Meital\.m2\repository\de\jollyday\jollyday\0.4.7\jollyday-0.4.7.jar;C:\Users\Meital\.m2\repository\javax\xml\bind\jaxb-api\2.2.7\jaxb-api-2.2.7.jar;C:\Users\Meital\.m2\repository\com\googlecode\efficient-java-matrix-library\ejml\0.23\ejml-0.23.jar;C:\Users\Meital\.m2\repository\javax\json\javax.json-api\1.0\javax.json-api-1.0.jar;C:\Users\Meital\.m2\repository\edu\stanford\nlp\stanford-corenlp\3.5.0\stanford-corenlp-3.5.0-models.jar;C:\Users\Meital\.m2\repository\edu\mit\jwi\2.2.3\jwi-2.2.3.jar;C:\Users\Meital\.m2\repository\org\apache\commons\commons-math3\3.2\commons-math3-3.2.jar" TextSim'
    cmd += ' "' + in_file1 + '" ' + '"' + in_file2 + '" ' + '"' + out_file + '"'
    os.chdir(r'C:\Users\Meital\git\ADW')
    subprocess.Popen(cmd, shell=True).wait()
    os.chdir(cd)


def get_adw_sim(q1, q2):
    """get the similarity of one of the component od the two questions"""
    txt1, title1, tags1_list = get_entry_data(q1)
    txt2, title2, tags2_list = get_entry_data(q2)

    #added
    title1 = " ".join([e for e in title1.split(" ") if e not in LANG_WORDS])
    title2 = " ".join([e for e in title2.split(" ") if e not in LANG_WORDS])

    for i in range(5):
        try:
            with open(IN1_FILE, "wb") as writer:
                writer.write((title1).encode("utf-8"))
            with open(IN2_FILE, "wb") as writer:
                writer.write((title2).encode("utf-8"))
                break
        except:
            time.sleep(1)
    if i == 4:
        print "error ", e
        return ["-", "-"]
    t = time.time()
    call_jar(IN1_FILE, IN2_FILE, OUT_FILE)
    print "time: " + str(time.time() - t)
    for i in range(5):
        try:
            with open(OUT_FILE, "rb") as reader:
                res = reader.read()
            break
        except:
            time.sleep(1)
    if i == 4:
        print "error ", e
        return ["-", "-"]
    return res.split(",")


def build_all_scores_db():
    """build new db that contains the similarity score of each pair"""
    WEIGHTS_DB.ensure_index("Id", unique=True)
    db_results = TIMED_DB.find({}, timeout=False)
    for res in db_results:
        pair_id = res["Id"]
        if WEIGHTS_DB.find({"Id": pair_id}).count():
            if WEIGHTS_DB.find({"Id": pair_id})[0]['cosine'] == "-":
                print WEIGHTS_DB.remove({"Id": pair_id})
                print "removed"
            else:
                print "skip"
                continue
        #entry = WEB_PAIRS_DB.find({"Id": int(pair_id)})[0]
        entry = TIMED_DB.find({"Id": int(pair_id)})[0]

        q1 = entry['id1']
        q2 = entry['id2']
        # pay attention, possible treatment to code from the same question
        if q1 == q2:
            title = [1, 1]
        else:
            title = get_adw_sim(q1, q2)
        print "id:", pair_id, "new:", title
        try:
            WEIGHTS_DB.insert({"Id": pair_id, "overlap": title[0], "cosine": title[1]})
        except Exception as e:
            print "error ", e
    db_results.close()


def build_all_sigs_db():
    """used for sigs extraction of the 100k db"""
    for pair_res in TIMED_DB.find({}):
        if SAVED_SIGS.find({"Id": pair_res['Id']}).count() == 0:
            sigs = get_pair_sigs_sim(pair_res)
            SAVED_SIGS.insert({"Id": pair_res['Id'], "in1": sigs[0], "in2": sigs[1], "out1": sigs[2], "out2": sigs[3]})
            print ({"Id": pair_res['Id'], "in1": sigs[0], "in2": sigs[1], "out1": sigs[2], "out2": sigs[3]})
        else:
            print "skip"


def get_pair_sigs_sim(pair):
    """get the to code fragments type signatures"""
    lang1 = pair["lang1"]
    lang2 = pair["lang2"]
    code1 = pair["code1"]
    code2 = pair["code2"]
    if lang1 == "java":
        try:
            in_v1, out_v1 = j.save_graph(code1, "")
        except Exception as e:
            print e
            in_v1 = None
            out_v1 = None
    elif lang1 == "python":
        in_v1, out_v1 = p.save_graph(code1, "")
    else:
        in_v1 = None
        out_v1 =None
    if lang2 == "java":
        try:
            in_v2, out_v2 = j.save_graph(code2)
        except:
            in_v1 = None
            out_v1 = None
    elif lang2 == "python":
        in_v2, out_v2 = p.save_graph(code2)
    else:
        in_v2 = None
        out_v2 = None
    return in_v1, in_v2, out_v1, out_v2



def main():
    build_all_sigs_db()
    #build_all_scores_db()

if __name__ == "__main__":
    main()

