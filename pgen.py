#!/usr/bin/env python3

import time
import random
import string
import logging
import argparse

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

    def __init__(self, patternStr, patternId=''):
        self._vowels = ['e','y','u','i','o','a']
        self._cons = [l for l in string.ascii_lowercase if l not in self._vowels]
        
        #self._vowels = ['у','е','ё','ы','э','а','о','я','и','ю']
        #self._cons = ['й','ц','к','н','г','ш','щ','з','х','ъ','ф','в','п','р','л','д','ж','ч','с','м','т','ь','б']
        self._quant = ['?','+','*','@']

        self._root = AstNode(typeid=AstNode.Pattern)
        self._nodeStack = []
        self.patternStr = patternStr
        self.patternId = patternId 
        self._pos = 0

    def __add__(self, other):
        return Pattern(self.patternStr + other.patternStr)

    def __iadd__(self, other):
        self.patternStr += other.patternStr
        return self

    def _parseString(self):
        """This method corresponds to the Expr production rule"""
        self.patternStr += '\x00' * 2
        self._curChar = self.patternStr[self._pos]

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
        elif self._curChar == '\'':
            self._parseStringLiteral(node)
        elif str.isdigit(self._curChar) or self._curChar in self._quant:
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
            """Parse {number:number} quantifier"""
            
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
            """Parse ?, +, *, @ quantifiers"""
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

    def _parseStringLiteral(self, astNode):
        """
        Parse 'string literal' inside {pattern}.
        String literals are only allowed inside curly-brace patterns.
        """
        logger.debug('Parsing string literal')
        self._consumeChar(keep=False)
        literal = ''
        while True:
            while self._curChar != '\'' and self._curChar != '\x00':
                literal += self._curChar
                self._consumeChar(keep=False)

            if self._curChar == '\x00':
                raise PGenParsingException('Missing closing `\'` in string literal')

            if self._peek(lookahead=-1) != '\\':
                self._consumeChar(keep=False)
                astNode.typeid = AstNode.StringLiteral
                astNode.value = literal
                return

            # Remove back-slash from string literal, append escaped `'`, and continue
            literal = literal[:-1] + self._curChar
            self._consumeChar(keep=False)

    def _parsePatternId(self, astNode=None):
        logger.debug('Parsing pattern id')
        patternId = ''
        while str.isalpha(self._curChar):
            patternId += self._curChar
            self._consumeChar(keep=False)

        logger.debug('Pattern ID: "{0}"'.format(patternId))
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
        self._parseString()

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
            if astNode.value == 'v':
                s = self._applyQuantifier(astNode, random.choice, self._vowels)
            elif astNode.value == 'V':
                s = self._applyQuantifier(astNode, random.choice, self._vowels).upper()
            elif astNode.value == 'c':
                s = self._applyQuantifier(astNode, random.choice, self._cons)
            elif astNode.value == 'C':
                s = self._applyQuantifier(astNode, random.choice, self._cons).upper()
            elif astNode.value == 'd':
                s = self._applyQuantifier(astNode, random.choice, range(10))
            elif astNode.value == 'alpha':
                s = self._applyQuantifier(astNode, random.choice, self._cons + self._vowels)
            elif astNode.value == 'Alpha':
                s = self._applyQuantifier(astNode, random.choice, self._cons + self._vowels).upper()
            else:
                s = astNode.value

            return s

        if astNode.quantifier and astNode.quantifier.getValue() in self._quant:
            return self._applyNonNumericQuantifier(astNode)

        for i in range(int(astNode.quantifier.getValue()) if astNode.quantifier is not None else 1):
            for child in astNode.children:
                s += self._walkAST(child, input)

        return s

    def _applyNonNumericQuantifier(self, astNode):
        ################################################
        # TODO: Handle +,?,* quantifiers as well
        # For now this method handles only '@' (any of)
        ################################################

        s = ''
        return self._walkAST(random.choice(astNode.children), s)

    def _applyQuantifier(self, astNode, func, *args):
        if astNode.quantifier is None:
            return str(func(*args))

        s = ''
        if astNode.quantifier.getValue() not in self._quant:
            for i in range(int(astNode.quantifier.getValue())):
                s += str(func(*args))
            return s


def main():
    parser = argparse.ArgumentParser(description='Pattern generator')
    parser.add_argument('-c', '--count', dest='count', default=1, type=int)
    parser.add_argument('-p', '--pattern', dest='pattern', type=str, required=True)
    args = parser.parse_args()

    try:
        for i in range(args.count):
            pattern = Pattern(args.pattern if args.pattern is not None else '{digit}{2:3}')
            print(next(pattern.generate()))
    except PGenParsingException as ex:
        logger.error(ex)


if __name__ == '__main__':
    main()
