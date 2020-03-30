__author__ = 'Meital'
from code_to_question import get_match_questions
from utils import return_unicode

# the regression tests for the code to question process (generic)


def test_from_file():
    with open("c2q_test.txt", "rb") as reader:
        lines = reader.readlines()
    place = "out"
    codes = []
    for i, line in enumerate(lines):
        if "<--NEW CODE-->" in line:
            if "code" in place:
                codes += [(ans_id, "".join(code))]
            place = "ans"
        elif "ans" in place:
            ans_id = line.split("<--")[1].split("-->")[0]
            place = "code"
            code = []
        elif "code" in place:
            code += [line]
    codes += [(ans_id, "".join(code))]
    ret = True
    for i, e in enumerate(codes):
        temp = run_test_existence(i, e)
        ret = ret and temp

    if ret:
        print "ALL TEST PASSED!"
    else:
        print "FAILURE!"


def run_test_existence(num, element):
    """check whether wanted id is in the results group"""
    expected = element[0]
    code = element[1]
    print "run test number:", num,
    ids = get_match_questions(code)
    ret = True
    if expected in ids:
        print ids.index(expected)
        print "PASS"
    else:
        print "FAIL!"
        ret = False
    print "ALL RESULTS:", ids
    return ret


if __name__ == '__main__':
    test_from_file()