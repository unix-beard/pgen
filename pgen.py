#!/usr/bin/env python

import logging
import random
import time
import string

###########################################################
logger = logging.getLogger('pgen')
#logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(funcName)s: %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)
###########################################################


class PGenParsingException(Exception):
    pass


class AstNode:
    """AST for patterns"""

    Pattern, PatternID, Char, Quantifier, StringLiteral = range(5)

    def __init__(self, typeid=None, value=None, children=None):
        self.typeid = typeid
        self.value = value
        self.children = children
        # If the node's typeid id is `Quantifier`,
        # then it should be bound to some pattern (AST)
        self.quantifier = None
        logger.debug('Node {0} created; children: {1}'.format(self, children))

    def __str__(self):
        return '<typeid: {0}; value: {1}; quantifier: {2}; id: {3}>'.format(self.typeid, self.value, self.quantifier, hex(id(self)))

    def addChild(self, child):
        if self.children is None:
            self.children = []
        self.children.append(child)

    def getValue(self):
        if type(self.value) is tuple:
            return random.choice(range(int(self.value[0]), int(self.value[-1]) + 1))
        else:
            return self.value


def printAST(astNode, indent=0):
    if indent == 0:
        logger.info('`' + str(astNode))
    else:
        logger.info(' ' * indent + '`---' + str(astNode))

    if not astNode.children:
        return

    for child in astNode.children:
        printAST(child, indent + 4)


class PatternLookupTable:
    """
    The only purpose of this class is to answer the question:
    Was some pattern previously defined or not?
    """

    def __init__(self):
        self._set = set()

    def __contains__(self, patternId):
        return True if patternId in self._set else False

    def add(self, patternId):
        logger.debug('Added pattern ID "{0}" to PLT'.format(patternId))
        self._set.add(patternId)


class Pattern:
    """
    Grammar:
        Expr -> Term Expr
        Term -> `{` Expr `}` | `{` [id | quantifier] `}`

        quantifier -> digit+ | `+` | `?` | `*`
        char -> any valid unicode char
        digit -> [0-9]
        id -> [a-zA-Z]+
    """

    _plt = PatternLookupTable()

    def __init__(self, patternStr, patternId=''):
        #self._vowels = ['e','y','u','i','o','a']
        #self._cons = [l for l in string.ascii_lowercase if l not in self._vowels]
        
        self._vowels = ['у','е','ё','ы','э','а','о','я','и','ю']
        self._cons = ['й','ц','к','н','г','ш','щ','з','х','ъ','ф','в','п','р','л','д','ж','ч','с','м','т','ь','б']

        self._root = AstNode(typeid=AstNode.Pattern)
        self._nodeStack = []
        self.patternStr = patternStr
        self.patternId = patternId 
        self._pos = 0
        self._curChar = self.patternStr[self._pos]

    def __add__(self, other):
        return Pattern(self.patternStr + other.patternStr)

    def __iadd__(self, other):
        self.patternStr += other.patternStr
        return self

    def _reset(self):
        pass

    def _parseString(self):
        """This method corresponds to the Expr production rule"""
        self.patternStr += '\x00' * 2

        while self._curChar != '\x00':
            node = AstNode()
            if self._curChar == '{':
                node.typeid = AstNode.Pattern
                self._parsePatternExpr(node)
            elif self._curChar == '\\':
                node.typeid = AstNode.Char
                self._parseEscapedChar(node)
            elif str.isalnum(self._curChar):
                node.typeid = AstNode.Char
                self._consumeChar(astNode=node)
            elif self._curChar not in ['{', '}']:
                node.typeid = AstNode.Char
                self._consumeChar(astNode=node)
            else:
                raise PGenParsingException('Unexpected character "{0}"'.format(self._curChar))

            self._root.addChild(node)

        logger.debug('Saw NULL character. Parsing is done!')

    def _parsePatternExpr(self, astNode):
        """This method corresponds to the Term production rule"""

        # Consume pattern's open curly brace
        self._consumeChar(keep=False)

        self._parsePatternTerm(astNode)

        if self._curChar == '{':
            self._parsePatternExpr(astNode)

        # Pop the current node
        self._nodeStack.pop()

    def _parsePatternTerm(self, astNode=None):
        node = AstNode()

        # Push the current node on the stack
        self._nodeStack.append(node)

        if str.isalpha(self._curChar):
            self._parsePatternId(node)
        elif str.isdigit(self._curChar) or self._curChar in ['?', '+', '*']:
            self._parseQuantifier(node)
            self._nodeStack[-2].quantifier = node
            logger.debug('Last node on the stack: {0}'.format(self._nodeStack[-2]))
        elif self._curChar == '{':
            self._parsePatternExpr(node)
        else:
            raise PGenParsingException('Unexpected character "{0}"'.format(self._curChar))

        # Don't add quantifiers
        if node.typeid != AstNode.Quantifier:
            astNode.addChild(node)

        # Consume pattern's close curly brace
        self._consumeChar(expect='}', keep=False)


    def _parseQuantifier(self, astNode):

        def _parseRangeQuantifier():
            '''Parse {number:number} quantifier'''
            
            ######################################
            # TODO: Improve range parsing
            ######################################

            rangeQuantifier = ''
            while str.isdigit(self._curChar):
                rangeQuantifier += self._curChar
                self._consumeChar(keep=False)

            if self._curChar == ':':
                self._consumeChar(keep=False)
                rangeQuantifier += ':'
                rangeQuantifier += _parseRangeQuantifier()
                
            return rangeQuantifier
        
        def _parseGeneralQuantifier():
            '''Parse ?, +, * quantifiers'''
            q = self._curChar
            self._consumeChar(keep=False)
            return q
            

        def _filterRange(rangeStr):
            li = [elem for elem in rangeStr.split(':') if elem != '']
            # Return the first and the last elements of the range
            return (li[0], li[-1])

        astNode.typeid = AstNode.Quantifier
        astNode.value = _filterRange(_parseRangeQuantifier()) if str.isdigit(self._curChar) else _parseGeneralQuantifier()
        logger.debug('parsed quantifier: {0}'.format(astNode.value))

    def _parseStringLiteral(self):
        """Not implemented yet"""
        pass

    def _parsePatternId(self, astNode=None):
        logger.debug('Parsing pattern id')
        patternId = ''
        while str.isalpha(self._curChar):
            patternId += self._curChar
            self._consumeChar(keep=False)

        logger.debug('Pattern ID: "{0}"'.format(patternId))
        Pattern._plt.add(patternId)
        astNode.typeid = AstNode.PatternID
        astNode.value = patternId

    def _consumeChar(self, expect=None, keep=True, astNode=None):
        """If keep is False, then consume the character but don't store it inside astNode"""

        logger.debug('Consuming character "{0}" (expect={1}, keep={2})'.format(self._curChar, expect, keep))

        if expect:
            # Assert that the current character is the one we're expecting
            if self._curChar != expect:
                raise PGenParsingException('Expected "{0}", but found "{1}" instead'.format(expect, self._curChar))

        if keep:
            astNode.value = self._curChar

        self._pos += 1
        self._curChar = self.patternStr[self._pos]

        logger.debug('Current character is "{0}"'.format(self._curChar))

    def _parseEscapedChar(self, astNode=None):
        nextChar = self._peek()
        logger.debug(nextChar)
        if nextChar not in ['n', 't', '\\', '{', '}']:
            raise PGenParsingException('Unknown escape character "{0}{1}"'.format(self._curChar, nextChar))

        if nextChar in ['n', 't']:
            astNode.value = self._curChar + nextChar
        else: 
            astNode.value = nextChar

        self._consumeChar(keep=False)
        self._consumeChar(keep=False)

    def _peek(self, lookahead=1):
        return self.patternStr[self._pos + lookahead]

    def generate(self):
        """Traverse AST and generate the string"""
        #logger.info('Parsing pattern "{0}"\n{1}'.format(self.patternStr, '#' * 80))
        self._parseString()
        #printAST(self._root)

        # Should be empty by now!
        assert(self._nodeStack == [])
        #logger.debug(self._nodeStack)

        while True:
            yield self._generateFromAST(self._root)

    def _generateFromAST(self, astNode):
        return self._walkAST(astNode, '')

    def _walkAST(self, astNode, input):
        s = input
        if not astNode.children:
            if astNode.value == 'vowel':
                s = self._applyQuantifier(astNode, random.choice, self._vowels)
            elif astNode.value == 'cons':
                s = self._applyQuantifier(astNode, random.choice, self._cons)
            elif astNode.value == 'digit':
                s = self._applyQuantifier(astNode, random.choice, range(10))
            elif astNode.value == 'alpha':
                s = self._applyQuantifier(astNode, random.choice, self._cons + self._vowels)
            else:
                s = astNode.value

            return s

        for i in range(int(astNode.quantifier.getValue()) if astNode.quantifier is not None else 1):
            for child in astNode.children:
                s += self._walkAST(child, input)

        return s

    def _applyQuantifier(self, astNode, func, *args):
        ##############################################
        # TODO: Handle +,?,* quantifiers as well
        ##############################################

        if astNode.quantifier is None:
            return str(func(*args))

        s = ''
        for i in range(int(astNode.quantifier.getValue())):
            s += str(func(*args))
        return s


def main():
    try:
        #p = Pattern('{a}')
        #p = Pattern('{{a}}')
        #p = Pattern('{{{a}}}')
        #p = Pattern('{a}{b}')
        #p = Pattern('{{a}{b}}')
        #p = Pattern('{{a}{b}{c}}')
        #p = Pattern('{{a}{b}}{{c}{d}}')
        #p = Pattern('{{a}{b}}{{c}{d}}{e}')
        #p = Pattern('{{{a}{b}}{{c}{d}}}{e}')
        #p = Pattern('a{cons}b')
        #p = Pattern('ab{cons}{vowel}')
        #p = Pattern('ab{{cons}{vowel}}')
        #p = Pattern('ab{{{cons}{vowel}}{cons}}')
        #p = Pattern('{{{a}{b}}{{c}{d}{e}{{f}{g}}{h}}}{i}')
        #p = Pattern('0{{{vowel}{cons}}}1')
        #p = Pattern('{{{{a}{+}}{*}}{?}}{1}')
        #p = Pattern('{vowel}{cons}{digit}')
        #p = Pattern('{}')
        #p = Pattern('{}{}')
        #p = Pattern('{{}{}}{}{}{}{{}{}{}{{}{}{{}}}}')

        # Unbalanced
        #p = Pattern('{')
        #p = Pattern('{{}')
        #p = Pattern('{{}}{')
        #p = Pattern('{{{')
        #p = Pattern('{{}{}}{}{}{{{}}')

        # Quantifiers
        #p = Pattern('{{a}{1}{b}{2}}{3}{c}{4}')
        #p = Pattern('{cons}{vowel}{cons}{vowel}{cons}{vowel}{cons}')
        #p = Pattern('{cons}{vowel}{cons}{cons}{vowel}{cons}{vowel}-{digit}{3}')
        #p = Pattern('{{{{digit}{digit}}{1}{vowel}{1}}{2}}{3}')
        #p = Pattern('{{digit}{1}{digit}{2}}{3}')
        #p = Pattern('{{vowel}{3}{cons}{2}}')
        #p = Pattern('{{a}{1}{b}{+}{c}{*}}{?}}')
        #p = Pattern('{a}{*}{{{b}{+}}{*}}{?}')

        # Range quantifiers
        #p = Pattern('{digit}{1:}')
        #p = Pattern('{digit}{1:2}')
        #p = Pattern('{digit}{1:2:}')
        #p = Pattern('{digit}{1:2:3}')
        p = Pattern('{{vowel}{cons}{{vowel}{cons}}{1:3}}{1:3}')
        p1 = Pattern('{{cons}{vowel}{{cons}{vowel}}{1:3}}{1:3}')
        p2 = Pattern('{vowel}{cons}{vowel}{vowel}{cons}{vowel}{cons}')
        p3 = Pattern('{vowel}{cons} {cons}{vowel}{cons} {vowel}{cons} {vowel}{cons}{vowel}{vowel}{cons}{vowel}{cons}')
        p4 = Pattern('{vowel}{cons}{vowel}')
        p5 = Pattern('{cons}{vowel}{cons}')
        p6 = Pattern('{cons}{vowel}{2}')
        p7 = Pattern('{vowel}{cons}{2}')
        
        # Unbound quantifiers
        #p = Pattern('{2}{a}')
        #p = Pattern('{?}{a}')

        # Misc 

        #p = Pattern('a{cons}_{digit}{2}')
        #p = Pattern('a{cons}_{digit}{2:4}')
        #p = Pattern('a{cons}_{vowel}{cons}-{digit}{2}')
        #p = Pattern('a{cons}_{vowel}{cons}-{digit}{1:3}')
        #p = Pattern('{{{vowel}{2}{cons}{2}}{2}}{2}')
        #p = Pattern('{{vowel}{2}{cons}{2}}{2}')
        #p = Pattern('{{vowel}{digit}{2}}{2}')
        #p = Pattern('az{alpha}{1:3}{vowel}++')

        # Meta pattern
        #p = Pattern('\{vowel\}\{cons\}')

        # Escaped characters
        #p = Pattern('\{\{\t\}\}\\\\-\n')

        d = Pattern('б')
        pat = Pattern('{cons}')
        pat += Pattern('{vowel}')
        pat += Pattern('{digit} ')
        pat += Pattern('{alpha}{1:3} ')
        pat += d + Pattern('{vowel}') + d
        
        for i in range(20):
            print(next(pat.generate()))
            #logger.info('Generated string: {0}'.format(p.generate().next()))
            #print('{0}'.format(next(p.generate())))
            #print('{0}'.format(next(p1.generate())))
            #print('{0}'.format(next(p2.generate())))
            #print('{0}'.format(next(p3.generate())))
            #print('{0}'.format(next(p4.generate())))
            #print('{0}'.format(next(p5.generate())))
            #print('{0}'.format(next(p6.generate())))
            #print('{0}'.format(next(p7.generate())))
    except PGenParsingException as ex:
        logger.error(ex)


if __name__ == '__main__':
    main()



