from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtXml import *

from moviedata import *

class SaxMovieHandler(QXmlDefaultHandler):
	"""docstring for SaxMovieHandler"""
	def __init__(self, movies):
		super(SaxMovieHandler, self).__init__()
		self.movies = movies
		self.text = str()
		self.error = None

	def clear(self):
		self.year = None
		self.minutes = None
		self.acquired = None
		self.notes = None
		self.title = None

	def startElement(self, namespaceURI, localName, qName, attributes):
		if qName == "MOVIE":
			self.clear()
			self.year = int(attributes.value("YEAR"))
			self.minutes = int(attributes.value("MINUTES"))
			ymd = attributes.value("ACQUIRED")
			if ymd.count() != 3:
				raise ValueError("Invalid acquired Date: {0}".format(str(attributes.value("ACQUIRED"))))
			self.acquired = QDate(int(ymd[0]), int(ymd[1]), int(ymd[2]))
		elif qName in ("TITLE", 'NOTES'):
			self.text = str()
		return True

	def characters(self, text):
		self.text += text 
		return True

	def endElement(self, namespaceURI, localName, qName):
		if qName == 'MOVIE':
			if self.year is None or self.minutes is None or self.acquired is None \
			or self.title is None or self.notes is None or self.title.isEmpty():
				raise ValueError("Incomplete movie Record")
			self.movies.add(Movie(self.title, self.year, self.minutes, self.acquired, decodedNewLines(self.notes)))
			self.clear()
		elif qName == "TITLE":
			self.title = self.text.trimmed()
		elif qName == "NOTES":
			self.notes = self.text.trimmed()
		return True

	def fatalError(self, exception):
		self.error = "Parse Error at line {0} column {1}: {2}".format(exception.lineNumber(), exception.columnNumber(), exception.message())
		return False


