#!/usr/bin/env python

import logging

logger = logging.getLogger('pgen')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(funcName)s: %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

class PGenParsingException(Exception):
	pass

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

	_plt = PatternLookupTable()

	def __init__(self, string):
		self._list = []
		self._string = string + '\x00'
		self._pos = 0
		self._curChar = self._string[self._pos]
		logger.info('Parsing pattern "{0}"'.format(self._string))
		self._parseString()
		logger.info(self._list)

	def _parseString(self):
		
		if self._curChar == '\x00':
			logger.info('Saw NULL character. Parsing is done!')
			return

		if self._curChar == '\\':
			self._parseEscapedChar()
		elif self._curChar == '{':
			self._parsePattern()
		else:
			self._consumeChar()

		self._parseString()

	def _consumeChar(self, join=False, keep=True):
		"""
		If join is True, then consume the current character and the following one,
		and join them together (e.g., the character sequence '\\', 'n'
		becomes '\\n' in the list).
		If keep is False, then consume the character but don't store it
		"""

		logger.info('Consuming character "{0}" (join={1}, keep={2}'.format(self._curChar, join, keep))

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


	def _parsePattern(self):
		logger.info('parsing {} pattern')
		self._consumeChar(keep=False) # Comsume '{'

		if self._curChar == '{':
			self._parsePattern()
			return
		elif self._curChar =='\'':
			self._parseStringLiteral()
		else:
			self._parsePatternId()

		if self._curChar != '}':
			raise PGenParsingException('Expected a closing "}}", but found "{0}" instead'.format(self._curChar))

		self._consumeChar(keep=False) # Consume '}'


	def _parseStringLiteral(self):
		pass

	def _parsePatternId(self):
		patternId = ''
		while str.isalpha(self._curChar):
			patternId += self._curChar
			self._consumeChar(keep=False)

		logger.info('Pattern ID: "{0}"'.format(patternId))
		Pattern._plt.add(patternId)

def main():
	try:
		p = Pattern('abc{{vowel}{cons}}')
	except PGenParsingException as ex:
		logging.error(ex)


if __name__ == '__main__':
	main()
