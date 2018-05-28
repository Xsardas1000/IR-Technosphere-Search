import re
import unittest
import numpy as np
import bitstream_v as bitstream

SPLIT_RGX = re.compile(r'\w+|[\(\)&\|!]', re.U)


class QtreeTypeInfo:
    def __init__(self, value, op=False, bracket=False, term=False):
        self.value = value
        self.is_operator = op
        self.is_bracket = bracket
        self.is_term = term

    def __repr__(self):
        return repr(self.value)

    def __eq__(self, other):
        if isinstance(other, QtreeTypeInfo):
            return self.value == other.value
        return self.value == other


class QTreeTerm(QtreeTypeInfo):
    def __init__(self, term):
        QtreeTypeInfo.__init__(self, term, term=True)


class QTreeOperator(QtreeTypeInfo):
    def __init__(self, op):
        QtreeTypeInfo.__init__(self, op, op=True)
        self.priority = get_operator_prio(op)
        self.left = None
        self.right = None


class QTreeBracket(QtreeTypeInfo):
    def __init__(self, bracket):
        QtreeTypeInfo.__init__(self, bracket, bracket=True)


def get_operator_prio(s):
    if s == '|':
        return 0
    if s == '&':
        return 1
    if s == '!':
        return 2

    return None


def is_operator(s):
    return get_operator_prio(s) is not None


def tokenize_query(q):
    tokens = []
    for t in map(lambda w: w.encode('utf-8'), re.findall(SPLIT_RGX, q)):
        if t == '(' or t == ')':
            tokens.append(QTreeBracket(t))
        elif is_operator(t):
            tokens.append(QTreeOperator(t))
        else:
            tokens.append(QTreeTerm(t))

    return tokens


def build_query_tree(tokens):
    """ write your code here """

    if len(tokens) == 1:  # if there is one term
        return tokens[0]

    root = None
    cur_prior = 10
    depth = 0
    index = 0
    for i, token in enumerate(tokens):
        if token.is_bracket:
            if token.value == '(':
                depth += 1
            else:
                depth -= 1

        if depth > 0:
            continue

        if token.is_operator and cur_prior >= token.priority:
            cur_prior = token.priority
            root = token
            index = i

    if root:

        if root.value == '!':
            root.right = build_query_tree(tokens[1:])
        else:
            root.left = build_query_tree(tokens[:index])
            root.right = build_query_tree(tokens[index + 1:])
    else:
        return build_query_tree(tokens[1:-1])  # delete brackets

    return root


def parse_query(q):
    tokens = tokenize_query(q)
    return build_query_tree(tokens)


""" Collect query tree to sting back. It needs for tests. """


def qtree2str(root, depth=0):
    if root.is_operator:
        need_brackets = depth > 0 and root.value != '!'
        res = ''
        if need_brackets:
            res += '('

        if root.left:
            res += qtree2str(root.left, depth + 1)

        if root.value == '!':
            res += root.value
        else:
            res += ' ' + root.value + ' '

        if root.right:
            res += qtree2str(root.right, depth + 1)

        if need_brackets:
            res += ')'

        return res
    else:
        return root.value



def get_q_list_urls(q, dictionary, index_file):
    if q.is_term:
        word = q.value
        gap, size = dictionary[word.decode('utf-8')]
        if gap < 0:
            print("Error")
        else:
            index_file.seek(gap)
            blob = index_file.read(size)
            found = bitstream.decompress_varbyte_v(blob)
            #print("Found for term {}: {}".format(word, len(found)))
            return found, False

    elif is_operator(q):
        prio = get_operator_prio(q)

        left_result, right_result, flag1, flag2 = None, None, None, None
        if q.left is not None:
            left_result, flag1 = get_q_list_urls(q.left, dictionary, index_file)
        if q.right is not None:
            right_result, flag2 = get_q_list_urls(q.right, dictionary, index_file)

        if prio == 2:
            return right_result, True
        if prio == 1:
            return intersect(left_result, flag1, right_result, flag2)
        if prio == 0:
            return union(left_result, flag1, right_result, flag2)
        else:
            print("Prior error")
    else:
        print("Error while parsing")


def get_q_list_urls_simple(q, dictionary, index_file):
    if q.is_term:
        word = q.value
        gap, size = dictionary[word.decode('utf-8')]
        if gap < 0:
            print("Error")
        else:
            index_file.seek(gap)
            blob = index_file.read(size)
            found = bitstream.decompress_simple(blob)
            #print("Found for term {}: {}".format(word, len(found)))
            return found, False

    elif is_operator(q):
        prio = get_operator_prio(q)

        left_result, right_result, flag1, flag2 = None, None, None, None
        if q.left is not None:
            left_result, flag1 = get_q_list_urls_simple(q.left, dictionary, index_file)
        if q.right is not None:
            right_result, flag2 = get_q_list_urls_simple(q.right, dictionary, index_file)

        if prio == 2:
            return right_result, True
        if prio == 1:
            return intersect(left_result, flag1, right_result, flag2)
        if prio == 0:
            return union(left_result, flag1, right_result, flag2)
        else:
            print("Prior error")
    else:
        print("Error while parsing")



def intersect(list1, flag1, list2, flag2):
    ## if !term1 & !term2
    if flag1 == True and flag2 == True:
        return union(list1, list2), True

    ## if !term1 & term2
    if flag1 == True:
        return np.setdiff1d(list2, list1, assume_unique=True), False

    ## if term1 & !term2
    if flag2 == True:
        return np.setdiff1d(list1, list2, assume_unique=True), False

    ## if term1 & term2
    else:
        return np.intersect1d(list1, list2, assume_unique=True), False


def union(list1, flag1, list2, flag2):
    ## if !term1 | !term2
    if flag1 == True and flag2 == True:
        return np.intersect1d(list1, list2, assume_unique=True), True

    ## if !term1 | term2
    if flag1 == True:
        return np.setdiff1d(list1, list2, assume_unique=True), True

    ## if term1 | !term2
    if flag2 == True:
        return np.setdiff1d(list2, list1, assume_unique=True), True

    ## if term1 | term2
    else:
        return np.union1d(list1, list2), False
