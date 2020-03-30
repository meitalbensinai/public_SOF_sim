__author__ = 'Meital'
# code examples, used for type sigs testing (from python_ast)

#real example with flow
code = """x = {'a':1, 'b': 2}\ny = {'b':10, 'c': 11}\nz4 = {}\nz4.update(x)\nz4.update(y)"""

#try-catch example
code = """try:\n\twith open('filename') as f: pass\nexcept IOError as e:\n\tprint 'Oh dear.'"""

#import + function example
code = """import os.path, sys\nos.path.exists(file_path)\nif(True):\n    continue"""

#double assignment example
code = """x=1\ny=2\nx=y"""

#AugAssign
code="""x+=1"""

#Assign 1
code="x=1+2\ny=2"

#Assign 2
code="x=[1,2,3]\ny={'a':1}\nz=(1,2)"

#Assing 3
code="x=[1,2,3]\ny=[x,1,2]"

#List compherhension
code="[x for x in xrange(1,5)]"

#functions
code = "z=x.func(f.func2(1),'str')"

#real code
code = """>>> sum(l, [])
[1, 2, 3, 4, 5, 6, 7, 8, 9]"""

code = """from subprocess import call
call(["ls", "-l"])"""


code = """from subprocess import Popen, PIPE
cmd = "ls -l ~/"
p = Popen(cmd , shell=True, stdout=PIPE, stderr=PIPE)
out, err = p.communicate()
print "Return code: ", p.returncode
print out.rstrip(), err.rstrip()"""

code = """>>> subprocess.check_output(["ls", "-l", "/dev/null"])
'crw-rw-rw- 1 root root 1, 3 Oct 18  2007 /dev/null'"""

code = """>>> 'hello world'[::-1]
'dlrow olleh'"""

code = """ x=str(34)\ny = 1 + 2\nm=y"""

code = """>>> sum(l, [])
[1, 2, 3, 4, 5, 6, 7, 8, 9]"""

code = """x = 1 + 2\ny = x\nm = y.someFunc("x")\nt=[1,2,3]\ns={"x": 4}\nr.func("123", m, y)"""


code = """def permutations(head, tail=''):
if len(head) == 0: print tail
else:
    for i in range(len(head)):
        permutations(head[0:i] + head[i+1:], tail+head[i])"""

code = """import fileinput

for line in fileinput.input():
print line"""

code = """import operator
x = {1: 2, 3: 4, 4:3, 2:1, 0:0}
sorted_x = sorted(x.iteritems(), key=operator.itemgetter(1))"""

code = """for x in [1, 2, 3]:
print x
r = 8
[1,2]"""

code = """x = 1 + 2\ny = x\nm = y.someFunc("x")\nt=[1,2,3]\ns={"x": 4}\nr.func("123", m, y)"""

code = "x.func(f.func2(1),'str')"

code = """>>> import requests
>>> url = "http://download.thinkbroadband.com/10MB.zip"
>>> r = requests.get(url)
>>> print len(r.content)
"""

code = """from itertools import chain
x = {'a':1, 'b': 2}
y = {'b':10, 'c': 11}
dict(chain(x.iteritems(), y.iteritems()))"""

code = """import urllib2
response = urllib2.urlopen('http://www.example.com/')
html = response.read()"""

code = """import itertools
itertools.permutations([1,2,3])"""



code = """def permutations (orig_list):
    if not isinstance(orig_list, list):
        orig_list = list(orig_list)

    yield orig_list

    if len(orig_list) == 1:
        return

    for n in sorted(orig_list):
        new_list = orig_list[:]
        pos = new_list.index(n)
        del(new_list[pos])
        new_list.insert(0, n)
        for resto in permutations(new_list[1:]):
            if new_list[:1] + resto <> orig_list:
                yield new_list[:1] + resto"""


# TODO!!!!! an example to learn from
code = """import os

asps = []
for root, dirs, files in os.walk(r'C:\web'):
    for file in files:
     if file.endswith('.asp'):
      asps.append(file)"""

code = """def permutations(head, tail=''):
    if len(head) == 0: print tail
    else:
        for i in range(len(head)):
            permutations(head[0:i] + head[i+1:], tail+head[i])"""

code = """somelist[:] = [tup for tup in somelist if determine(tup)]"""

code = """def all_perms(elements):
    if len(elements) <=1:
        yield elements
    else:
        for perm in all_perms(elements[1:]):
            for i in range(len(elements)):
                #nb elements[0:1] works in both string and list contexts
                yield perm[:i] + elements[0:1] + perm[i:]"""




code = """from itertools import chain
x = {'a':1, 'b': 2}
y = {'b':10, 'c': 11}
dict(chain(x.iteritems(), y.iteritems()))"""

code ="""def f7(seq):
    seen = set()
    seen_add = seen.add
    return [ x for x in seq if x not in seen and not seen_add(x)]"""



code = """import os

asps = []
for root, dirs, files in os.walk(r'C:\web'):
    for file in files:
     if file.endswith('.asp'):
      asps.append(file)"""




code = """from itertools import groupby
[ key for key,_ in groupby(sortedList)]"""


code = """#! /usr/bin/env python

#Given a secuencia of integer numbers through stdin
#returns its sum through stdout

import sys
import re
num=0
for line in sys.stdin:
    regexp = re.compile("-?[0-9]+")
    numeros=[int(i) for i in regexp.findall(line)]

    for j in range(0,len(numeros)):
      num = num + numeros[j]
    print num
    num=0"""


code= """def permutations (orig_list):
    if not isinstance(orig_list, list):
        orig_list = list(orig_list)

    yield orig_list

    if len(orig_list) == 1:
        return

    for n in sorted(orig_list):
        new_list = orig_list[:]
        pos = new_list.index(n)
        del(new_list[pos])
        new_list.insert(0, n)
        for resto in permutations(new_list[1:]):
            if new_list[:1] + resto <> orig_list:
                yield new_list[:1] + resto"""


code = """def all_perms(elements):
    if len(elements) <=1:
        yield elements
    else:
        for perm in all_perms(elements[1:]):
            for i in range(len(elements)):
                #nb elements[0:1] works in both string and list contexts
                yield perm[:i] + elements[0:1] + perm[i:]"""


#TODO
code = """def call_func(x):
    print x

    call_func(1)"""

code = """import urllib2
res = urllib2.urlopen('http://www.example.com')
html = res.read()"""

code ="""def p (head, tail=''):
  if len(head) == 0:
    print tail
  else:
    for i in range(len(head)):
        p(head[0:i] + head[i+1:],
                    tail + head[i])"""


code ="""def all_perms(elements):
    if len(elements) <= 1:
        yield elements  # Only permutation possible = no permutation
    else:
        # Iteration over the first element in the result permutation:
        for (index, first_elmt) in enumerate(elements):
            other_elmts = elements[:index]+elements[index+1:]
            for permutation in all_perms(other_elmts):
                yield [first_elmt] + permutation"""

code = """import itertools
itertools.permutations("abc")"""

code = """def permutations(iterable, r=None):
    # permutations('ABCD', 2) --> AB AC AD BA BC BD CA CB CD DA DB DC
    # permutations(range(3)) --> 012 021 102 120 201 210
    pool = tuple(iterable)
    n = len(pool)
    r = n if r is None else r
    if r > n:
        return
    indices = range(n)
    cycles = range(n, n-r, -1)
    yield tuple(pool[i] for i in indices[:r])
    while n:
        for i in reversed(range(r)):
            cycles[i] -= 1
            if cycles[i] == 0:
                indices[i:] = indices[i+1:] + indices[i:i+1]
                cycles[i] = n - i
            else:
                j = cycles[i]
                indices[i], indices[-j] = indices[-j], indices[i]
                yield tuple(pool[i] for i in indices[:r])
                break
        else:
            return"""


code = """#!/usr/bin/env python

def perm(a,k=0):
   if(k==len(a)):
      print a
   else:
      for i in xrange(k,len(a)):
         a[k],a[i] = a[i],a[k]
         perm(a, k+1)
         a[k],a[i] = a[i],a[k]

perm([1,2,3])"""

code = """def permutList(l):
    if not l:
            return [[]]
    res = []
    for e in l:
            temp = l[:]
            temp.remove(e)
            res.extend([[e] + r for r in permutList(temp)])

    return res"""

code = """def all_perms(elements):
    if len(elements) <=1:
        yield elements
    else:
        for perm in all_perms(elements[1:]):
            for i in range(len(elements)):
                # nb elements[0:1] works in both string and list contexts
                yield perm[:i] + elements[0:1] + perm[i:]"""

code = """def permutations(head, tail=''):
    if len(head) == 0: print tail
    else:
        for i in range(len(head)):
            permutations(head[0:i] + head[i+1:], tail+head[i])"""

code = """def permutList(l):
    if not l:
            return [[]]
    res = []
    for e in l:
            temp = l[:]
            temp.remove(e)
            res.extend([[e] + r for r in permutList(temp)])

    return res"""

code = """
def addperm(x,l):
        return [ l[0:i] + [x] + l[i:]  for i in range(len(l)+1) ]

def perm(r):
    if len(r) == 0:
        return [[]]
    return [m for y in perm(r[1:]) for m in addperm(r[0],y) ]

print perm("abc")"""

"""
code =
def g():
    return ["abc","cde"]
def f():
    return g()
print f()
"""

code = """#!/usr/bin/env python

def perm(a,k=0):
   if(k==len(a)):
      print a
   else:
      for i in xrange(k,len(a)):
         a[k],a[i] = a[i],a[k]
         perm(a, k+1)
         a[k],a[i] = a[i],a[k]

perm([1,2,3])"""


code ="""def all_perms(elements):
    if len(elements) <= 1:
        yield elements  # Only permutation possible = no permutation
    else:
        # Iteration over the first element in the result permutation:
        for (index, first_elmt) in enumerate(elements):
            other_elmts = elements[:index]+elements[index+1:]
            for permutation in all_perms(other_elmts):
                yield [first_elmt] + permutation"""


code = """
def p (head, tail=''):
  if len(head) == 0:
      print tail
  else:
    for i in range(len(head)):
        p(head[0:i] + head[i+1:], tail + head[i])
print p("abc")
"""
