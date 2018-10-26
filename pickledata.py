import pickle
import copyreg
import gzip

from container import MovieContainer

class PickleData(MovieContainer):
	"""docstring for PickleData"""
	def __init__(self):
		super(PickleData, self).__init__()
		self.__fname = fname
		copyreg.pickle(QDate, self._pickleQDate)
	
	def _pickleQDate(self, date):
		return QDate, (date.year(), date.month(), date.day())

	def savePickle(self):
		error = None
		fh = None
		try:
			fh.gzip.open(str(self.__fname), 'wb')
			cPickle.dump(self.__movies, fh, 2)
		except (IOError, OSError) as e:
			error = 'Failed to save: {0}'.format([e])
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
			error = 'Failed to load: {0}'.format([e])
		finally:
			if fh is not None:
				fh.close()
			if error is not None:
				return False, error
			self.__dirty = False
			return True, 'Loaded {0} movie records  from {1}'.format([len(self.__movies)], QFileInfo(self.__fname).fileName())