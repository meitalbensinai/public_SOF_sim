__author__ = 'Meital'
# find related questions using the web - SOF itself and common search engines: google and bing

from consts import *
import operator
from lsa_compare import texts_stemming
from get_code import get_ans_code_by_q_id
import urllib
import urllib2
import json
from bs4 import BeautifulSoup
from lsa_compare import return_trained_lsa_from_ids
from apiclient.discovery import build

ADDITION_TEXT = ' stackoverflow'
SITES_THRESHOLD = 10
CONTENT_TO_WORDS_NUM = 5
MAX_WORD_LEN = 13
SCORE_THRESHOLD = 0.5
STACKOVERFLOW_SITE = "http://stackoverflow.com/questions/"


def build_query(q_id):
    """q_id to google searchable query"""
    query = []
    post = POSTS_DB.find({'Id': str(q_id)})[0]
    title = post['Title']
    content = post['Body']
    #TODO: use it
    tags = [e.replace(">", "") for e in post['Tags'].split("<") if e != ""]
    clean_post = clean_line(CODE_OUT_RE.sub("", content))
    query += [e for e in split_text(no_punctuation(title))]
    query += content_to_bag_of_words(clean_post)
    to_remove = STOP_WORDS + LANG_WORDS
    query = texts_stemming(query)
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


def find_query(query, q_id):
    """starts google search with given query, returns relevant questions ids"""
    q_bag = query.split(" ")
    if len(q_bag) < 15:
        #ps = list(power_set(q_bag))
        ps = list(all_possible_word_out(q_bag))
    else:
        ps = []
    #ps.sort(key = lambda s: len(s))
    #rps = ps[::-1]
    rps = [q_bag] + ps
    return list(set(use_bing(rps) + list(get_related_from_sof(q_id))))


def get_related_from_sof(q_id):
    """get question ids of the related questions classified by sof"""
    url = STACKOVERFLOW_SITE + str(q_id)
    usock = urllib2.urlopen(url)
    data = usock.read()
    usock.close()
    ids = set()
    i = 0
    soup = BeautifulSoup(data, 'html.parser')
    for link in soup.find_all('a'):
        temp = link.get('href')
        if temp is None:
            continue
        if "questions" in temp:
            try:
                new_id = str(int(temp.split("/questions/")[1].split("/")[0]))
                ids.add(new_id)
            except:
                pass
    return ids


def get_only_ids(sof_urls):
    """get ids list from url list"""
    q_ids = set()
    for url in sof_urls:
        try:
            temp = url.split("questions/")[1].split("/")[0]
            int(temp)
            q_ids.add(temp)
        except:
            pass
    return list(q_ids)


def use_google(rps):
    """perform google search for the given bags"""
    sof_urls = set()
    for i, words_bag in enumerate(rps):
        if len(words_bag) < 3:
            break
        temp_query = " ".join(words_bag)
        service = build("customsearch", "v1", developerKey="AIzaSyDcvhrlHStaa5ZucJRayv4MCbAT5pR7rEk")
        res = service.cse().list(q=temp_query, cx='003166220260834611059:gxgjiwghzv4').execute()
        print "The query", temp_query, ", has", len(res['items']), "results"
        for item in res['items']:
            sof_urls.add(item["link"])
    return get_only_ids(sof_urls)


def use_bing(rps):
    """perform bing search for the given bags"""
    sof_urls = set()
    for i, words_bag in enumerate(rps):
        if len(words_bag) < 3:
            break
        temp_query = " ".join(words_bag)
        sof_urls |= set(bing_search(temp_query, "Web"))
    return get_only_ids(sof_urls)


def bing_search(query, search_type):
    """query search in bing"""
    #search_type: Web, Image, News, Video
    key = '6syXf2kfqdihIv033wvQjsXXMnJJQaqXv3I68nR53Gs='
    site = " (site: stackoverflow.com)"
    try:
        new_query = urllib.quote(query + site)
    except:
        return []
    # create credential for authentication
    user_agent = 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; FDM; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 1.1.4322)'
    credentials = (':%s' % key).encode('base64')[:-1]
    auth = 'Basic %s' % credentials
    url = 'https://api.datamarket.azure.com/Data.ashx/Bing/Search/'+search_type+'?Query=%27'+new_query+'%27&$top=50&$format=json'
    request = urllib2.Request(url)
    request.add_header('Authorization', auth)
    request.add_header('User-Agent', user_agent)
    request_opener = urllib2.build_opener()
    try:
        response = request_opener.open(request)
    except:
        return []
    response_data = response.read()
    json_result = json.loads(response_data)
    result_list = json_result['d']['results']
    print len(result_list)
    sof_urls = [e["Url"] for e in result_list]
    return sof_urls


def all_possible_word_out(group):
    """limited power set, list of all the options to move one word from the group"""
    less_word = []
    group = list(group)
    for i, val in enumerate(group):
        less_word += [group[:i] + group[i+1:]]
    return less_word


def find_the_closest(wanted, optional_set, file_name):
    """based on list of maybe related question return the closest, by tf.idf"""
    return return_trained_lsa_from_ids(wanted, optional_set)
    #return perform_tfidf(wanted, optional_set, file_name)


def find_the_closest_NEW(wanted, optional_set, models):
    x = return_trained_lsa_from_ids(wanted, optional_set, 0, models)
    scores_dict = {}
    for i in range(len(x[0])):
        scores_dict[optional_set[i]] = (x[0][i], x[1][i], x[2][i])
    return scores_dict, x[3]


def print_code_to_file(q_id):
    """print to file the code snippets -> debugging, not relevant"""
    res = ["\n***********" + q_id + "***********"]
    ans_dic = get_ans_code_by_q_id(q_id)
    for key in ans_dic:
        for code in ans_dic[key][1]:
            res += ["_________"] + [code.replace("\n\n", "\n")] + ["_________"]
    with open(file_name, "ab") as writer:
        writer.write("\n".join(res))

if __name__ == "__main__":
    q_id = "977796"
    query = build_query(q_id)
    find_query(query, q_id)

    q_id_in = raw_input("insert question id: ")
    file_name = BASE_FILE_NAME + q_id_in + ".txt"
    query_example = build_query(q_id_in)
    print query_example
    #relevant_q_id = find_query(query_example, q_id_in)
    #relevant_q_id = [u'3531700', u'24831047', u'24672270', u'2543018', u'42566', u'5144738', u'11580148', u'19037376', u'4866547', u'625644', u'898266', u'3184615', u'13970028', u'7965759', u'8923407', u'16475659', u'106179', u'22123841', u'22826142', u'657482', u'4392158', u'24760256', u'1365722', u'8901651', u'12408673', u'9481865', u'13248971', u'19224811', u'22753378', u'23351054', u'263000', u'4709014', u'20153559', u'3215729', u'17917292', u'20320683', u'11876365', u'21306088', u'3232516', u'1939953', u'396819', u'21470757', u'12217708', u'5749477', u'15788453', u'4398300', u'2083598', u'6882965', u'22670966', u'16895773', u'8150283', u'14870158', u'6370017', u'3150448', u'21587452', u'3371879', u'18953391', u'24175384', u'24505550', u'3256452', u'12319836', u'24790408', u'24961919', u'9577709', u'22386497', u'21339550', u'8872807', u'11318828', u'23685015', u'14843232', u'5796215', u'1988765', u'20477868', u'16218078', u'12590244', u'24416530', u'435606', u'17147543', u'995808', u'7655512', u'3097589', u'11401897', u'24546860', u'6971556', u'6159074', u'7348711', u'23899910', u'11123639', u'1250398', u'24768199', u'12060026', u'11183989', u'98449', u'24690546', u'22062374', u'5118151', u'348614', u'23769137', u'7525702', u'8651043', u'13327220', u'21986264', u'330395', u'19960243', u'8579105', u'1409449', u'19173962', u'17505835', u'23257891', u'16688085', u'15062900', u'10339351', u'5640349', u'24562848', u'22960044', u'3425556', u'12324466', u'1204032', u'996231', u'20629927', u'13110386', u'23751635', u'15250563', u'10409700', u'23131859', u'72921', u'6622237', u'17613284', u'16749764', u'24566541', u'23202606', u'18476856', u'5691193', u'931889', u'15999367', u'10729034', u'22033694', u'20928293', u'85487', u'22727687', u'1069221', u'16615121', u'22919370', u'23512030', u'13171265', u'20711518', u'16512840', u'5248964', u'458757', u'20383440', u'14225306', u'11815412', u'18727676', u'20607727', u'14375567', u'733418', u'4101219', u'20696094', u'23936018', u'20514324', u'4390134', u'12697014', u'19032893', u'7673290', u'7570331', u'18102227', u'6803073', u'10564525', u'21689654', u'13884378', u'3364213', u'5882870', u'6050011', u'2419219', u'1935621', u'16344333', u'16380544', u'11845184', u'5505931', u'10554380', u'14088787', u'2575760', u'8660865', u'23253462']
    #relevant_q_id = [u'4856030', u'1110153', u'6231360', u'5144344', u'19153105', u'4751866', u'11775980', u'1206073', u'9289148', u'20521086', u'4066538', u'4805606', u'1757214', u'21159296', u'1129216', u'9357785', u'4686849', u'369512', u'443542', u'15114586', u'5461479', u'1955789', u'2217029', u'6850611', u'8432581', u'12879598', u'21679982', u'4123462', u'6965337', u'708698', u'21389775', u'13056324', u'721577', u'13046532', u'11234561', u'10211470', u'36139', u'22648967', u'17539226', u'12672662', u'1814095', u'15389187', u'5155952', u'10390894', u'5212870', u'613183']
    relevant_q_id = [u'8903560', u'12590462', u'1024471', u'20916072', u'22431637', u'3179931', u'20985588', u'19276281', u'5643004', u'186131', u'19968106', u'4240080', u'8648120', u'7918806', u'21780320', u'13780947', u'10508343', u'13109710', u'24793317', u'8306654', u'13901641', u'24022901', u'9049628', u'23370280', u'18153419', u'14243296', u'10468153', u'19819374', u'3862191', u'756055', u'1526046', u'16639463', u'24215353', u'5175329', u'24608981', u'5058219', u'820845', u'20108621', u'8554202', u'6501224', u'20001045', u'24161066', u'6367932', u'1207856', u'1506078', u'361', u'4074991', u'11208446', u'3766661', u'11425070', u'11075788', u'3319586', u'2920315', u'11233355', u'8948819', u'1503072', u'19967626', u'4180101', u'10782285', u'1634880', u'3621494', u'8845918', u'6963922', u'7560363', u'2556871', u'14855690', u'2736260', u'17991483', u'16271350', u'7149271', u'2872959', u'9430568', u'19589263', u'11120985', u'3079633', u'9493098', u'19676109', u'21806617', u'24594313', u'1274506', u'9028250', u'20656586', u'2396578', u'24059190', u'2834320', u'22161818', u'1554366', u'2799078', u'6924216', u'22059773', u'8411602', u'14329696', u'93353', u'10063717', u'3583697', u'8843977', u'6890356', u'9039265', u'24944454', u'16972106', u'18451010', u'1942429', u'2772884', u'3467914', u'10305153', u'1720978', u'6716847', u'38502', u'20823449', u'20521612', u'23312998', u'17688435', u'23750204', u'6074226', u'18696716', u'10852839', u'10620461', u'8940470', u'18293633', u'11475392', u'24079911', u'5506888', u'2944987', u'3689097', u'2892202', u'10803186', u'873413', u'1760185', u'722749', u'7902391', u'12884428', u'10211243', u'11515970', u'20935315', u'21490119', u'21120272', u'19549630', u'9338052', u'11205191', u'14421630', u'13408213', u'352203', u'11199707', u'18389756', u'6913460', u'4619162', u'18384140', u'2084816', u'2345734', u'20285858', u'14135873', u'14522044', u'12160843', u'23427492', u'21174773', u'3172179', u'21016192', u'4408998', u'8480487', u'710670', u'9843574', u'8130411', u'4120743', u'24621993', u'20035471', u'1119699', u'20778514', u'8839034', u'19862412', u'2839221', u'23065082', u'1942785', u'7730360', u'2189303', u'774457', u'5128615', u'19993073', u'8609644', u'104420', u'2710713', u'11395990', u'9233615', u'14264163', u'7072768', u'5751091', u'23722473', '5313900', '20331757', '20102359', '3829457', '394809', '960557', '2556871', '480397', '23699378', '4074991']

    if len(relevant_q_id) == 0:
        print "No google results, bummer!"
        exit()
    print "search results: ", relevant_q_id
    after_tfidf_q_ids, cos_dis = find_the_closest(q_id_in, list(set(relevant_q_id)), file_name)
    print_code_to_file(q_id_in)
    if len(cos_dis) > 0:
        t = 0
        while cos_dis[t] > SCORE_THRESHOLD:
            print_code_to_file(after_tfidf_q_ids[t])
            t += 1
