import bisect
import pickle
import copyreg
import gzip
import codecs
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from moviedata import Movie
from sax import *

CODEC = 'UTF-8'
#NEW_PARA = unichr(0x2029)
#NEW_LINE = unichr(0x2028)
DATE_FORMAT = 'ddd MMM d, yyyy'

class MovieContainer():
	"""docstring for MovieContainer"""
	MAGIC_NUMBER = 0x3051E
	FILE_VERSION = 100

	def __init__(self):
		self.__fname = str()
		self.__movies = []
		self.__movieFromId = {}
		self.__dirty = False


	def __iter__(self):
		for pair in iter(self.__movies):
			yield pair[1]
	
	def __len__(self):
		return len(self.__movies)

	def clear(self, clearFilename=True):
		self.__movies = []
		self.__movieFromId = {}
		if clearFilename:
			self.__fname = str()
		self.__dirty = False

	def add(self, movie):
		if id(movie) in self.__movieFromId:
			return False
		key = self.key(movie.title, movie.year)
		bisect.insort_left(self.__movies, [key, movie])
		self.__movieFromId[id(movie)] = movie
		self.__dirty = True
		return True

	def isDirty(self):
		return self.__dirty

	def key(self, title, year):
		text = str(title).lowet()
		if text.startswith('a '):
			text = text[2:]
		if text.startswith('an '):
			text = text[3:]
		if text.startswith('the '):
			text = text[4:]
		parts = text.split(' ', 1)
		if parts[0].isdigit():
			text = '%08d' % int(parts[0])
			if len(parts) > 1:
				text += parts[1]
		return u'%s\t%d' % (text.replace(' ', ''), year)

	def delete(self, movie):
		if id(movie) not in self.__movieFromId:
			return
		key = self.key(movie.title, movie.year)
		i = bisect.bisect_left(self.__movies, [key, movie])
		del self.__movies[i]
		del self.__movieFromId[id(movie)]
		self.__dirty = True
		return True

	def updateMovie(self, movie, title, year, minutes = None, notes = None):
		if minutes is not None:
			movie.minutes = minutes
		if notes is not None:
			movie.notes = notes
		if title != movie.title or year != movie.year:
			key = self.key(movie.title, movie.year)
			i = bisect.bisect_left(self.__movies, [key, movie])
			self.__movies[i][0] = self.key(title, year)
			movie.title = title
			movie.year = year
			self.__movies.sort()
		self.__dirty = True

	@staticmethod
	def formats():
		return '*.mqb *.mpb *.mqt *.mpt'

	def save(self, fname = str()):
		if not fname.isEmpty():
			self.__fname = fname 
		if self.__fname.endsWith('.mqb'):
			return self.saveQDataStream()
		if self.__fname.endsWith('.mpb'):
			return self.savePickle()
		if self.__fname.endsWith('.mqt'):
			return self.saveQTextStream()
		if self.__fname.endsWith('.mpt'):
			return self.saveText()
		return False, 'Failed to Save: Invalid File Extension'

	def load(self, fname=str()):
		if not fname.isEmpty():
			self.__fname = fname
		if self.__fname.endsWith(".mqb"):
			return self.loadQDataStream()
		elif self.__fname.endsWith(".mpb"):
			return self.loadPickle()
		elif self.__fname.endsWith(".mqt"):
			return self.loadQTextStream()
		elif self.__fname.endsWith(".mpt"):
			return self.loadText()
		return False, "Failed to load: invalid file extension"

	def saveQDataStream(self):
		error = None
		fh = None
		try:
			fh = QFile(self.__fname)
			if not fh.open(QIODevice.WriteOnly):
				raise IOError(str(fh.errorString()))
			stream = QDataStream(fh)
			stream.writeInt32(MovieContainer.MAGIC_NUMBER)
			stream.writeInt32(MovieContainer.FILE_VERSION)
			stream.setVersion(QDataStream.Qt_5_9)
			for key, movie in self.__movies:
				stream << movie.title
				stream.writeInt16(movie.year)
				stream.writeInt16(movie.minutes)
				stream << movie.acquired <<movie.notes
		except (IOError, OSError) as e:
			error = 'Failed to save: {0}'.format(e)
		finally:
			if fh is not None:
				fh.close()
			if error is not None:
				return False, error
			self.__dirty = False
			return True, 'Saved {0} movie Records to {1}'.format(len(self.__movies), QFileInfo(self.__fname).fileName())

	def loadQDataStream(self):
		error = None
		fh = None
		try:
			fh = QFile(self.__fname)
			if not fh.open(QIODevice.ReadOnly):
				raise IOError(str(fh.errorString))
			stream = QDataStream()
			magic = QDataStream(fh)
			magic = stream.readInt32()
			if magic != MovieContainer.MAGIC_NUMBER:
				raise IOError('Unrecognised File type')
			version = stream.readInt32()
			if version < MovieContainer.FILE_VERSION:
				raise IOError('old and Unreadable file format')
			if version > MovieContainer.FILE_VERSION:
				raise IOError('New and Unreadabke file format')
			stream.setVersion(QDataStream.Qt_5_9)
			self.clear(False)

			while not stream.atEnd():
				title = str()
				acquired = QDate()
				notes = str()
				stream>>title
				year = stream.readInt16()
				minutes = stream.readInt16()
				stream >> acquired >> notes
				self.add(moviedata.Movie(title, year, minutes, acquired, notes))

		except (IOError, OSError) as e:
			error = 'Failed to Load file: {0}'.format(e)
		finally:
			if fh is not None:
				fh.close()
			if error is not None:
				return False, error 
			self.__dirty = False
			return True, 'Loaded {0} movie Records from {1}'.format(len(self.__movies), QFileInfo(self.__fname).fileName())

	def savePickle(self):
		error = None
		fh = None
		try:
			fh.gzip.open(str(self.__fname), 'wb')
			cPickle.dump(self.__movies, fh, 2)
		except (IOError, OSError) as e:
			error = 'Failed to save: {0}'.format(e)
		finally:
			if fh is not None:
				fh.close()
			if error is not None:
				return False, error
			self.__dirty = False
			return True, 'Saved {0} movie records to {1}'.format(len(self.__movies), QFileInfo(self.__fname).fileName())

	def loadPickle(self):
		error = None
		fh = None
		try:
			fh.gzip.open(str(self.__fname), 'rb')
			self.clear(False)
			self.__movies = cPickle.load(fh)
			for key, movies in self.__movies:
				self.__movieFromId[(movie)] = movie 
		except (IOError, OSError) as e:
			error = 'Failed to load: {0}'.format(e)
		finally:
			if fh is not None:
				fh.close()
			if error is not None:
				return False, error
			self.__dirty = False
			return True, 'Loaded {0} movie records  from {1}'.format(len(self.__movies), QFileInfo(self.__fname).fileName())

	def saveQTextStream(self):
		error = None
		fh = None
		try:
			fh.QFile(self.__fname)
			if not fh.open(QIODevice.WriteOnly):
				raise IOError(str(fh.errorString()))
			stream = QTextStream(fh)
			stream.setCodec(CODEC)
			for key, movie in self.__movies:
				stream  << "{{MOVIE}}" <<movie.title << '\n'\
						<< movie.year <<" "<<movie.minutes <<' ' \
						<< movie.acquired.toString(Qt.ISODate) \
						<< '\n{NOTES}'
				if not movie.notes.isEmpty():
					stream << '\n' << movie.notes
					stream << '\n{{ENDMOVIE}}\n' 
		except (IOError, OSError) as e:
			error = 'Failed to save: {0}'.format(e)
		finally:
			if fh is not None:
				fh.close()
				if error is not None:
					return False, error 
				self.__dirty = False
				return True, 'Saved {0} movie records to {1}'.format(len(self.__movies), QFileInfo(self.__fname).fileName())

	def loadQTextStream(self):
		error = None
		fh = None
		try:
			fh.QFile(self.__fname)
			if not fh.open(QIODevice.ReadOnly):
				raise IOError(str(fh.errorString()))
			stream = QTextStream(fh)
			stream.setCodec(CODEC)
			self.clear(False)
			lino = 0
			while not stream.atEnd():
				title = year = minutes = acquired = notes = None
				line = stream.readLine()
				lino += 1
				if not line.startsWith('{{MOVIE}}'):
					raise ValueError('no Movie Record Found')
				else:
					title = line.mid(len('{{MOVIE}}')).trimmed()
					if stream.atEnd():
						raise ValueError('Unexpected End of File')
					line = stream.readLine()
					lino += 1
					parts = line.split(' ')
					if parts.count() != 3:
						raise ValueError('Invalid Numeric Data')
					year = str(parts[0])
					minutes = str(parts[1])
					ymd = parts[2].split('-')
					if ymd.count() != 3:
						raise ValueError('Invalid Acquired Date')
					acquired = QDate(str(ymd[0]), str(ymd[1]), str(ymd[2]))

					if stream.atEnd():
						raise ValueError("Unexpected End of File")
					line = stream.readLine()
					lino += 1
					if line != '{{NOTES}}':
						raise ValueError("Notes Expected but not Found")
					notes = str()
					while not stream.atEnd():
						line = stream.readLine()
						lino += 1
						if line == '{{ENDMOVIE}}':
							if title is None or year is None or minutes is None or acquired is None or notes is None:
								raise ValueError("Incomplete Record")
							self.add(Movie(title, year, minutes, acquired, notes.trimmed()))
						else:
							notes += line + '\n'
					else: raise ValueError("missing End Movie marker")
		except (IOError, OSError, ValueError):
			error = 'Failed to load: {0} on line {1}'.format(e, lino)
		finally:
			if fh is not None:
				fh.close()
			if error is not None:
				return False, error 
			self.__dirty = False
			return True, 'Loaded {0} Movie records from {1}'.format(len(self.__movies), QFileInfo(self.__fname).fileName())

	def saveText(self):
		error = None
		fh = None
		try:
			fh = codecs.open(str(self.__fname), 'w', CODEC)
			for key, movie in self.__movies:
				fh.write(u"{{MOVIES}} {0}\n".format(str(movie.title)))
				fh.write(u"{0} {1} {2}\n".format(movie.year, movie.minutes, movie.acquired.toString(Qt.ISODate)))
				fh.write(u"{{NOTES}}")
				if not self.__movies.notes.isEmpty():
					fh.write(u"\n{{ENDMOVIE}}\n")
		except (IOError, OSError) as e:
			error = 'Failed to Save: {0}'.format(e)
		finally:
			if fh is not None:
				fh.close()
			if error is not None:
				return False, error 
			self.__dirty = False
			return True, 'Saved {0} movie records to {1}'.format(len(self.__movies), QFileInfo(self.__fname).fileName())

	def loadText(self):
		error = None
		fh = None
		try:
			fh = codecs.open(str(self.__fname), 'r', CODEC)
			self.clear(False)
			lino = 0
			while True:
				title = year = minutes = acquired = notes = None
				line = fh.readLine()
				if not line:
					break
				lino +=1
				if not line.startsWith('{{MOVIE}}'):
					raise ValueError("No movie Record Found")
				else:
					title = str(line[len('{{MOVIE}}'):].strip())
				line = fh.readLine()
				if not line:
					raise ValueError("Unexpected End of file")
				lino += 1
				parts = line.split(" ")
				if len(parts) != 3:
					raise ValueError("Invalid Numeric Data")
				year = int(parts[0])
				minutes = int(parts[1])
				ymd = parts[3].split('-')
				if len(ymd) != 3:
					raise ValueError("Invalid Acquired Date")
				acquired = QDate(int(ymd[0]), int(ymd[1]), int(ymd[2]))

				line = fh.readLine()
				if not line:
					raise ValueError('Unexpected End of File')
				lino += 1
				if line != '{{NOTES}}':
					raise ValueError("Notes Expected but not Found")
				notes = str()
				while True:
					line = fh.readLine()
					if not line:
						raise ValueError("Missing EndMovie Marker")
					lino += 1
					if line == '{{ENDMOVIE}}\n':
						if (title is None or year is None or minutes is None or acquired is None or notes is None):
							raise ValueError('Incomplete Record')
						self.add(Movie(title, year, minutes, acquired, notes.trimmed()))
						break
					else:
						notes += str(line)
		except (ValueError, IOError, OSError) as e:
			error = 'Failed to Load: {0} on line {1}'.format(e, lino)
		finally:
			if fh is not None:
				fh.close()
			if error is not None:
				return False, error
			self.__dirty = False
			return True, 'Loaded {0} movie records from {1}'.format(len(self.__movies), QFileInfo(self.__fname).fileName())

	def exportXML(self, fname):
		error = None
		fh = None
		try:
			fh = QFile(fname)
			if not fh.open(QIODevice.WriteOnly):
				raise IOError(str(fh.errorString()))
			stream = QTextStream()
			stream.setCodec(CODEC)
			stream << ("<?xml version = '1.0' encoding = '{0}'\n"
				"<!DOCTYPE MOVIES>\n"
				"<MOVIES version = '1.0'>\n".format(CODEC))
			for key, movie in self.__movies:
				stream << ("<MOVIE YEAR = '{0}' MINUTES = '{1}' ACQUIRED = '{2}'\n".format(movie.year, movie.minutes, movie.acquired.toString(Qt.ISODate)))
				stream << "<TITLE>"<<Qt.escape(movie.title) <<"</TITLE>\n<NOTES>"
				if not movie.notes.isEmpty():
					stream << "\n" <<Qt.escape(encodedNewLines(movie.notes))
				stream << "\n</NOTES>\n</MOVIE>\n"
			stream << "</MOVIES>\n"

		except (OSError, IOError) as e:
			error = "Failed to Export: {0}".format(e)
		finally:
			if fh is not None:
				fh.close()
			if error is not None:
				return False, error
			return True, "Exported {0} movie records to {1}".format(len(self.__movies), QFileInfo(self.__fname).fileName())

	def importDOM(self, fname):
		dom = QDomDocument()
		error = None
		fh = None
		try:
			fh = QFile(fname)
			if not fh.open(QIODevice.ReadOnly):
				raise IOError(fh.errorString())
			if not dom.setContent(fh):
				raise ValueError("Could not parse XML")

		except (IOError, OSError, ValueError) as e:
			error = 'Failed to import: '.format(e)
		finally:
			if fh is not None:
				fh.close()
			if error is not None:
				return False, error
			try:
				self.populateFromDOM(dom)
			except ValueError as e:
				return False, "Failed to Import: {0}".format(e)
			self.__fname = str()
			self.__dirty = True
			return True, 'Imported {0} movie record from {1}'.format(len(self.__movies), QFileInfo(self.__fname).fileName())

	def populateFromDOM(self, dom):
		root = dom.documentElement()
		if root.tagName() != 'MOVIES':
			raise ValueError("Not a Movies XML File")
		self.clear(false)
		node = root.firstChild()
		while not node.isNull():
			if node.toElement().tagName() == 'MOVIE':
				self.readMovieNode(node.toElement())
			node = node.nextSibling()

	def readMovieNode(self, element):
		def getText(node):
			child = node.firstChild()
			text = str()
			while not child.isNull():
				if child.nodeType() == QDomNode.TextNode:
					text += child.toText().data()
				child = child.nextSibling()
			return text.trimmed()

		year = int(element.attribute("YEAR"))
		minutes = int(element.attribute("MINUTES"))
		ymd = element.attribute("ACQUIRED").split('-')
		if ymd.count() != 3:
			raise ValueError("Invalid Acquired Date {0}".format(str(element.attribute("ACQUIRED"))))
		acquired = QDate(int(ymd[0]), int(ymd[1]), int(ymd[2]))
		title = notes = None
		node = element.firstChild()
		while title is None or notes is None:
			if node.isNull():
				raise ValueError("missing title or notes")
			if node.toElement().tagName() == 'TITLE':
				title = getText(node)
			elif node.toElement().tagName() == 'NOTES':
				notes = getText(node)
		node = node.nextSibling()
		if title.isEmpty():
			raise ValueError("Invalid Title")
		self.add(Movie(title, year, minutes, acquired, decodedNewLines(notes)))

	def importSAX(self, fname):
		error = None
		fh = None 
		try:
			handler = SaxMovieHandler(self)
			parser = QXmlSimpleReader()
			parser.setContentHandler(handler)
			parse.serErrorHandler(handler)
			fh = QFile(fname)
			input = QXmlInputSource(fh)
			self.clear(False)
			if not parser.parse(input):
				raise ValueError(handler.error)			
		except (IOError, OSError) as e:
			error = "Failed to Import: {0}".format(e)
		finally:
			if fh is not None:
				fh.close()
			if error is not None:
				return False, error
			self.__fname = str()
			self.__dirty = True
			return True, "Import {0} movie records from {1}".format(len(self.__movies), QFileInfo(fname).fileName())



