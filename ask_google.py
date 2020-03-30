__author__ = 'Meital'
from consts import *
import operator
from lsa_compare import perform_tfidf
from apiclient.discovery import build
from nltk.stem.wordnet import WordNetLemmatizer

ADDITION_TEXT = ' stackoverflow'
SITES_THRESHOLD = 10
CONTENT_TO_WORDS_NUM = 5
MAX_WORD_LEN = 10


def build_query(q_id):
    """from q_id to google searchable query"""
    query = []
    post = POSTS_DB.find({'Id': str(q_id)})[0]
    title = post['Title']
    content = post['Body']
    tags = [e.replace(">", "") for e in post['Tags'].split("<") if e != ""]
    clean_post = clean_line(CODE_OUT_RE.sub("", content))
    query += [e for e in split_text(no_punctuation(title))]
    query += content_to_bag_of_words(clean_post)
    to_remove = STOP_WORDS + LANG_WORDS
    query = list(set([e for e in query if e not in to_remove and len(e) < MAX_WORD_LEN]))
    return " ".join(query)


def content_to_bag_of_words(content):
    """returns set of the most frequent words in the text"""
    count = {}
    for e in split_text(no_punctuation(content)):
        e1 = e.lower()
        if e1 not in STOP_WORDS:
            count[e1] = count.get(e1, 0) + 1
    sorted_x = sorted(count.iteritems(), key=operator.itemgetter(1))
    sorted_x.reverse()
    return [e[0] for e in sorted_x[:CONTENT_TO_WORDS_NUM]]


def find_query(query):
    """starts google search with given query, returns relevant questions ids"""
    q_bag_b = query.split()
    q_bag = set()
    lmtzr = WordNetLemmatizer()
    for e in q_bag_b:
        verb_e = lmtzr.lemmatize(e)
        if verb_e == "":
            verb_e = e
        q_bag.add(verb_e)
    print "after stemming:", " ".join(list(q_bag))
    if len(q_bag) < 10:
        #ps = list(power_set(q_bag))
        ps = list(all_possible_word_out(q_bag))
    else:
        ps = [q_bag]
    #ps.sort(key = lambda s: len(s))
    #rps = ps[::-1]
    rps = [q_bag] + ps
    q_ids = set()
    sof_urls = set()
    for i, words_bag in enumerate(rps):
        if len(words_bag) < 4:
            break
        temp_query = " ".join(words_bag)
        if len(q_ids) > 15:
            break
        service = build("customsearch", "v1", developerKey="AIzaSyDcvhrlHStaa5ZucJRayv4MCbAT5pR7rEk")
        res = service.cse().list(q=temp_query, cx='003166220260834611059:gxgjiwghzv4').execute()
        for item in res['items']:
            sof_urls.add(item["link"])
    for url in sof_urls:
        try:
            temp = url.split("questions/")[1].split("/")[0]
            int(temp)
            q_ids.add(temp)
        except:
            pass
    return list(q_ids)


def all_possible_word_out(group):
    """returns all the sub sets of group in size len(group) - 1"""
    less_word = []
    group = list(group)
    for i, val in enumerate(group):
        less_word += [group[:i] + group[i+1:]]
    return less_word


def find_the_closest(wanted, optional_set):
    """based on list of maybe related question return the closest, by tf.idf"""
    perform_tfidf(wanted, optional_set)


if __name__ == "__main__":
    q_id_in = raw_input("insert question id: ")
    query_example = build_query(q_id_in)
    print query_example
    #relevant_q_id = find_query(query_example)
    #relevant_q_id = [u'3531700', u'24831047', u'24672270', u'2543018', u'42566', u'5144738', u'11580148', u'19037376', u'4866547', u'625644', u'898266', u'3184615', u'13970028', u'7965759', u'8923407', u'16475659', u'106179', u'22123841', u'22826142', u'657482', u'4392158', u'24760256', u'1365722', u'8901651', u'12408673', u'9481865', u'13248971', u'19224811', u'22753378', u'23351054', u'263000', u'4709014', u'20153559', u'3215729', u'17917292', u'20320683', u'11876365', u'21306088', u'3232516', u'1939953', u'396819', u'21470757', u'12217708', u'5749477', u'15788453', u'4398300', u'2083598', u'6882965', u'22670966', u'16895773', u'8150283', u'14870158', u'6370017', u'3150448', u'21587452', u'3371879', u'18953391', u'24175384', u'24505550', u'3256452', u'12319836', u'24790408', u'24961919', u'9577709', u'22386497', u'21339550', u'8872807', u'11318828', u'23685015', u'14843232', u'5796215', u'1988765', u'20477868', u'16218078', u'12590244', u'24416530', u'435606', u'17147543', u'995808', u'7655512', u'3097589', u'11401897', u'24546860', u'6971556', u'6159074', u'7348711', u'23899910', u'11123639', u'1250398', u'24768199', u'12060026', u'11183989', u'98449', u'24690546', u'22062374', u'5118151', u'348614', u'23769137', u'7525702', u'8651043', u'13327220', u'21986264', u'330395', u'19960243', u'8579105', u'1409449', u'19173962', u'17505835', u'23257891', u'16688085', u'15062900', u'10339351', u'5640349', u'24562848', u'22960044', u'3425556', u'12324466', u'1204032', u'996231', u'20629927', u'13110386', u'23751635', u'15250563', u'10409700', u'23131859', u'72921', u'6622237', u'17613284', u'16749764', u'24566541', u'23202606', u'18476856', u'5691193', u'931889', u'15999367', u'10729034', u'22033694', u'20928293', u'85487', u'22727687', u'1069221', u'16615121', u'22919370', u'23512030', u'13171265', u'20711518', u'16512840', u'5248964', u'458757', u'20383440', u'14225306', u'11815412', u'18727676', u'20607727', u'14375567', u'733418', u'4101219', u'20696094', u'23936018', u'20514324', u'4390134', u'12697014', u'19032893', u'7673290', u'7570331', u'18102227', u'6803073', u'10564525', u'21689654', u'13884378', u'3364213', u'5882870', u'6050011', u'2419219', u'1935621', u'16344333', u'16380544', u'11845184', u'5505931', u'10554380', u'14088787', u'2575760', u'8660865', u'23253462']
    relevant_q_id = [u'4856030', u'1110153', u'6231360', u'5144344', u'19153105', u'4751866', u'11775980', u'1206073', u'9289148', u'20521086', u'4066538', u'4805606', u'1757214', u'21159296', u'1129216', u'9357785', u'4686849', u'369512', u'443542', u'15114586', u'5461479', u'1955789', u'2217029', u'6850611', u'8432581', u'12879598', u'21679982', u'4123462', u'6965337', u'708698', u'21389775', u'13056324', u'721577', u'13046532', u'11234561', u'10211470', u'36139', u'22648967', u'17539226', u'12672662', u'1814095', u'15389187', u'5155952', u'10390894', u'5212870', u'613183']

    if len(relevant_q_id) == 0:
        print "No google results, bummer!"
        exit()
    print relevant_q_id
    find_the_closest(q_id_in, relevant_q_id)