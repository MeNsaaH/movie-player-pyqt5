from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import container


class ClassName(container.MovieContainer):
	"""docstring for ClassName"""
	def __init__(self):
		pass
		
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
			error = 'Failed to save: {0}'.format([e])
		finally:
			if fh is not None:
				fh.close()
			if error is not None:
				return False, error
			self.__dirty = False
			return True, 'Saved {0} movie Records to {1}'.format([len(self.__movies), QFileInfo(self.__fname).fileName()])

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
			error = 'Failed to Load file: {0}'.format([e])
		finally:
			if fh is not None:
				fh.close()
			if error is not None:
				return False, error 
			self.__dirty = False
			return True, 'Loaded {0} movie Records from {1}'.format([len(self.__movies), QFileInfo(self.__fname).fileName()])


