# not in use - old version
from bs4 import BeautifulSoup
from consts import *

"""
atext: code snippet -> its answer text 
ratext: code snippet -> text of related answers (answers to the same question)
qtext: code snippet -> text of the question 
"""

if __name__ == "__main__":
    MAPPING_DB.drop()
    posts_with_code = POSTS_DB.find({"answers.Body": {"$regex": "/.*<code>.*/"}})
    print posts_with_code.count()
    print "it may take long time.."
    for i, post in enumerate(posts_with_code):
        #print i
        ratext = []
        ratId = []
        fragment_entries = []
        answers = post['answers']
        for answer in answers:
            ratext += [(answer['Body'])]
            ratId += [(answer['Id'])]
            soup = BeautifulSoup(answer['Body'])
            c = soup.findAll('code')

            for frag in c:
                code = frag.prettify(formatter=None)
                if len(code) < 50:
                    continue
                raw_code = []
                if PROMPT_TEXT in code:
                    for code_line in code.split("\n"):
                        if PROMPT_TEXT in code_line:
                            raw_code += [code_line.split(PROMPT_TEXT)[1]]
                    code = "\n".join([e for e in raw_code if e != "\n"])
                    print code
                code = code.replace("<code>","").replace("</code>", "")
                fragment_entries += [{
                    'code': code,
                    'answerId': answer['Id'],
                    'questionId': post['Id'],
                    'title': post['Title'],
                    'questionScore': post['Score'],
                    'answerScore': answer['Score'],
                    'atext': answer['Body'],
                    'ratext': [],
                    'ratId': [],
                    'qtext': post['Body']
                }]

        for i, entry in enumerate(fragment_entries):
            entry['ratext'] = ratext[:i] + ratext[i + 1:]
            entry['ratId'] = ratId[:i] + ratId[i + 1:]
            MAPPING_DB.insert(entry)