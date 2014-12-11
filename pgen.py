#!/usr/bin/env python

import logging
import random
import time

logger = logging.getLogger('pgen')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(funcName)s: %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

class PGenParsingException(Exception):
	pass

class TreeNode:
	"""AST for patterns"""

	Pattern		  = 0
	PatternList	  = 1
	PatternID	  = 2
	Repeat		  = 3
	StringLiteral = 4

	def __init__(self, typeid=None, value=None, children=None, boundTo=None):
		self.typeid = typeid
		self.value = value
		self.children = children
		# If the node's typeid id `Repeat`,
		# then it shoulb be bound to some AST
		self.boundTo = boundTo
		logger.info('Node {0} created; children: {1}'.format(self, children))

	def __str__(self):
		return '<typeid: {0}; value: {1}; bound to: {2}; id: {3}>'.format(self.typeid, self.value, self.boundTo, hex(id(self)))
	
	def addChild(self, child):
		logger.info('Adding child [{0}] with children {1} to parent [{2}]'.format(child, child.children, self))
		if self.children is None:
			self.children = []
		self.children.append(child)
		logger.info('Added child [{0}] with children {1} to parent [{2}]'.format(child, child.children, self))


def printAST(astNode, indent=0):
	if indent == 0:
		logger.info('`' + str(astNode))
	else:
		logger.info('|' + ' ' * indent + '`---' + str(astNode))

	if not astNode.children:
		return

	for child in astNode.children:
		printAST(child, indent + 4)
	
########################################################################
# List of pattern ASTs
########################################################################
ast = []


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
		logger.info('Added pattern ID "{0}" to PLT'.format(patternId))
		self._set.add(patternId)


class Pattern:
	"""
	Grammar:
		P -> { L }
		L -> PL
			 id
	"""

	_plt = PatternLookupTable()

	def __init__(self, string):
		self._list = []
		self._string = string + '\x00'
		self._pos = 0
		self._braceCount = 0
		self._curChar = self._string[self._pos]
		self._prevASTNode = None
		logger.info('Parsing pattern "{0}"'.format(self._string))
		self._parseString()
		logger.info(self._list)
		logger.info('Brace count: {0}'.format(self._braceCount))

	def _parseString(self):
		while self._curChar != '\x00':
			if self._curChar == '{':
				root = self._parsePattern()
				ast.append(root)
				self._list.append(root)
			elif self._curChar == '\\':
				self._parseEscapedChar()
			else:
				self._consumeChar()

		logger.info('Saw NULL character. Parsing is done!')
		if self._braceCount < 0:
			raise PGenParsingException('Unbalanced braces in the pattern')


	def _parsePattern(self):
		"""P production rule"""
		self._consumeChar(keep=False)
		astNode = TreeNode(typeid=TreeNode.Pattern)
		self._parsePatternList(parent=astNode)
		self._prevASTNode = astNode
		self._consumeChar(expect='}', keep=False)
		return astNode

	def _parsePatternList(self, parent):
		"""L production rule"""
		if str.isalpha(self._curChar):
			parent.addChild(self._parsePatternId())
		elif str.isdigit(self._curChar):
			parent.addChild(self._parseRepeat(isdigit=True))
		elif self._curChar in ['+','?','*']:
			parent.addChild(self._parseRepeat(isdigit=False))
		elif self._curChar == '{':
			astNodeRoot = self._parsePattern()
			self._parsePatternList(astNodeRoot)
			parent.addChild(astNodeRoot)
			
	def _parseRepeat(self, isdigit=True):
		repeat = ''
		if isdigit:
			while str.isdigit(self._curChar):
				repeat += self._curChar 
				self._consumeChar(keep=False)
		else:
			repeat = self._curChar
			self._consumeChar(keep=False)

		logger.info('Repeat: "{0}"; bound to pattern: {1}'.format(repeat, self._prevASTNode))
		printAST(self._prevASTNode)
		return TreeNode(typeid=TreeNode.Repeat, value=repeat, boundTo=self._prevASTNode) 

	def _parseStringLiteral(self):
		"""Not implemented yet"""
		pass

	def _parsePatternId(self):
		logger.info('Parsing pattern id')
		patternId = ''
		while str.isalpha(self._curChar):
			patternId += self._curChar
			self._consumeChar(keep=False)

		logger.info('Pattern ID: "{0}"'.format(patternId))
		Pattern._plt.add(patternId)
		return TreeNode(typeid=TreeNode.PatternID, value=patternId)

	def _consumeChar(self, expect=None, join=False, keep=True):
		"""
		If join is True, then consume the current character and the following one,
		and join them together (e.g., the character sequence '\\', 'n'
		becomes '\\n' in the list).
		If keep is False, then consume the character but don't store it
		"""

		if self._curChar == '{':
			self._braceCount += 1
		elif self._curChar == '}':
			self._braceCount -= 1
			
		logger.info('Consuming character "{0}" (expect={1}, join={2}, keep={3})'.format(self._curChar, expect, join, keep))

		if expect:
			# Assert that the current character is the one we're expecting
			if self._curChar != expect:
				raise PGenParsingException('Expected "{0}", but found "{1}" instead'.format(expect, self._curChar))
				
		if keep:
			self._list.append(self._curChar)

		self._pos += 1
		self._curChar = self._string[self._pos]

		if join:
			logger.info('Consuming character "{0}" and joining it with "{1}"'.format(self._curChar, self._string[self._pos - 1]))
			if keep:
				self._list[-1] += self._curChar
			self._pos += 1
			self._curChar = self._string[self._pos]

		logger.info('Current character is "{0}"'.format(self._curChar))

	def _parseEscapedChar(self):
		nextChar = self._string[self._pos + 1]
		if nextChar not in ['n', 't', '\\']:
			raise PGenParsingException('Unknown escape character "{0}{1}"'.format(self._curChar, nextChar))

		self._consumeChar(join=True)

	def generate(self):
		"""Traverse the list and AST and generate the string"""
		while True:
			s = ''
			for elem in self._list:
				s += self._generateFromAST(elem) if isinstance(elem, TreeNode) else elem
			yield s

	def _generateFromAST(self, astNode):
		s = self._walkAST(astNode, '')
		return s

	def _walkAST(self, astNode, input, repeat=None):
		s = input 
		if not astNode.children:
			if astNode.value == 'vowel':
				return random.choice(['e','y','u','i','o','a'])
			elif astNode.value == 'cons':
				return random.choice(['q','w','r','t','p','s','d','f','g','h','j','k','l','z','x','c','v','b','n','m'])
			elif astNode.value == 'digit':
				return str(random.choice(xrange(10)))
			elif astNode.typeid == TreeNode.Repeat:
				if repeat is None and (int(astNode.value) - 1) > 0:
					s += self._walkAST(astNode.boundTo, input, int(astNode.value) - 1)
				elif repeat > 1:
					s += self._walkAST(astNode.boundTo, input, repeat - 1)

				return s
					
		for child in astNode.children:
			s += self._walkAST(child, input, repeat)
		
		return s

def main():
	try:
		#p = Pattern('{a}')
		#p = Pattern('{{a}}')
		#p = Pattern('{{{a}}}')
		#p = Pattern('{{a}{b}}')
		#p = Pattern('a{{cons}}b')
		#p = Pattern('{{{a}{b}}{{c}{d}{e}{{f}{g}}{h}}}{i}')
		#p = Pattern('0{{{vowel}{cons}}}1')
		#p = Pattern('{{{{a}{+}}{*}}{?}}{1}')
		#p = Pattern('{vowel}{cons}{digit}')
		#p = Pattern('{cons}{vowel}{cons}{vowel}{cons}')
		#p = Pattern('{cons}{vowel}{cons}{vowel}{cons}{vowel}{cons}')
		#p = Pattern('{cons}{vowel}{cons}{cons}{vowel}{cons}')
		#p = Pattern('{{{{digit}{digit}}{1}{vowel}{1}}{2}}{3}')
		#p = Pattern('{{digit}{1}{digit}{2}}{3}')
		p = Pattern('{{vowel}{3}{cons}{2}}')
		for node in ast:
			printAST(node)

		for i in xrange(1):
			logger.info('Generated string: {0}'.format(p.generate().next()))
			#time.sleep(5)
	except PGenParsingException as ex:
		logger.error(ex)


if __name__ == '__main__':
	main()
