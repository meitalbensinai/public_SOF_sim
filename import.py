# first data import
import xml.etree.cElementTree as ET
from consts import *


file_name = r'C:\Users\Meital\Desktop\Posts.xml'
questions_cnt = 0
answers_cnt = 0

if __name__ == "__main__":
    DB = client.sof_new
    POSTS_DB = DB.posts
    #POSTS_DB.drop()
    POSTS_DB.ensure_index("Id", unique=True)

    for event, elem in ET.iterparse(file_name, events=("start", "end")):
        if event == 'start':
            post_type = elem.get('PostTypeId')
            if post_type == '1':
                title = elem.get('Title')
                tags = elem.get('Tags')
                post_id = elem.get('Id')
                if POSTS_DB.find({"Id": post_id}).count() == 0:
                    rep_id = POSTS_DB.insert(elem.attrib, w=0)
                    questions_cnt += 1
                else:
                    print 'id ' + id + ' already exists'
            elem.clear()

    print 'inserted:' + str(questions_cnt)
    for event, elem in ET.iterparse(file_name, events=("start", "end")):
        if event == 'start':
            post_type = elem.get('PostTypeId')
            if post_type == '2':
                parentId = elem.get('ParentId')
                parent = POSTS_DB.find_one( { "Id" : parentId })
                if parent is None:
                    continue
                POSTS_DB.update( { "Id" : parentId}, { "$addToSet": { "answers" : elem.attrib} })
                answers_cnt += 1
            elem.clear()

    print 'inserted answers:' + str(answers_cnt)
