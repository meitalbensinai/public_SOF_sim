__author__ = 'Meital'
import re
import itertools
import string


def clean_line(line):
    """move irrelevant parts of text, html overhead"""
    new_line = re.sub(r'<.*?>', "", line).replace("\n\n","\n")
    return new_line.strip()


def return_unicode(base):
    """returns unicode representation of the string"""
    return repr(base).decode('unicode-escape')


def power_set(iterable):
    """returns the power set"""
    s = list(iterable)
    return itertools.chain.from_iterable(itertools.combinations(s, r) for r in range(len(s)+1))


def no_punctuation(init_text):
    """prepares the text: lowercase, removes punctuation and replace them with space,
    add space when there is upper case in the middle of a words"""
    new_text = ""
    exclude = set(string.punctuation)
    exclude.remove('#')
    exclude.remove('+')
    for i, ch in enumerate(init_text):
        if ch in exclude:
            new_text += " "
        elif i == 0:
            new_text += ch.lower()
        elif ch.isupper() and init_text[i-1].islower():
            new_text += " " + ch.lower()
        elif not ch.isdigit():
            new_text += ch.lower()
    words = new_text.split(" ")
    return ' '.join(words)



def split_text(txt):
    """splits text by space or EOL"""
    return re.split(' |\n', txt)

if __name__ == "__main__":
    print no_punctuation("array.contains(obj) in JavaScript")