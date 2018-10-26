
import sys
import platform
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import qrc_resources
from container import MovieContainer
import editMovieDialog as edlg

__version__ = '1.0.0'

class MainWindow(QMainWindow):
	"""docstring for MainWindow"""
	def __init__(self, parent=None):
		super(MainWindow, self).__init__(parent)
		
		self.movies = MovieContainer()
		self.table = QTableWidget()
		self.setCentralWidget(self.table)
		
		#Status bar below
		self.sizeLabel = QLabel()
		self.sizeLabel.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)

		status = self.statusBar()
		status.setSizeGripEnabled(False)
		status.addPermanentWidget(self.sizeLabel)
		status.showMessage('Ready', 5000)

		#file Menu Options
		fileNewAction = self.createAction('&New...', self.fileNew, QKeySequence.New, 'filenew', 'Create a new movie data File' )
		fileQuitAction = self.createAction('&Quit...', self.close, 'Ctrl + Q', 'filequit', 'Close the Application' )
		fileOpenAction = self.createAction('&Open...', self.fileOpen, QKeySequence.Open, 'fileopen', 'open an existing movie data file')
		fileSaveAction = self.createAction('&Save...', self.fileSave, QKeySequence.Save, 'filesave', 'save movie data')
		fileSaveAsAction = self.createAction('Save &As...', self.fileSaveAs, QKeySequence.SaveAs, 'filesaveas', 'save Movie data file using a new name')
		fileImportDOMAction = self.createAction('&Import from XML (DOM)...', self.fileImportDOM, tip='Import the movie data from an XML file')
		fileImportSAXAction = self.createAction('I&mport from XML (SAX)...', self.fileImportSAX, tip='Import the movie data from an XML file')
		fileExportXmlAction = self.createAction('E&xport as XML...', self.fileExportXml, tip="Export the movie data to an XML file")
		
		#Edit Menu options
		editAddAction = self.createAction('&Add...', self.editAdd, 'Ctrl + A', 'editadd', 'Add data about a movie')
		editEditAction = self.createAction('&Edit...', self.editEdit, 'Ctrl + E', 'editedit', "Edit the current movie's data")
		editRemoveAction = self.createAction('&Remove...', self.editRemove, 'Del', 'editdelete', "Remove a movie's data")
		#help Menu Options
		helpAboutAction = self.createAction('&About the Application', self.helpAbout)
		helpHelpAction = self.createAction('&Help', self.helpHelp, QKeySequence.HelpContents)

		#add Menus to menu bar
		#fileMenu
		self.fileMenu = self.menuBar().addMenu('&File')
		self.fileMenuActions = (fileNewAction, fileOpenAction, fileSaveAction, fileSaveAsAction, fileImportSAXAction, fileImportDOMAction, fileExportXmlAction, None, fileQuitAction)
		self.fileMenu.aboutToShow.connect(self.updateFileMenu)

		#edit Menu
		editMenu = self.menuBar().addMenu('&Edit')
		self.addActions(editMenu, (editAddAction, editEditAction, editRemoveAction))
		#help Menu
		helpMenu = self.menuBar().addMenu('&Help')
		self.addActions(helpMenu, (helpAboutAction, helpHelpAction))

		#Tool bars
		#File Tool Bars
		fileToolBar = self.addToolBar('File')
		fileToolBar.setObjectName('FileToolBar')
		self.addActions(fileToolBar, (fileNewAction, fileOpenAction, fileSaveAction, fileSaveAsAction))

		#Edit Tool Bars
		editToolBar = self.addToolBar('Edit')
		editToolBar.setObjectName('EditToolBar')
		self.addActions(editToolBar, (editAddAction, editEditAction, editRemoveAction))

		self.table.itemDoubleClicked.connect(self.editEdit)

		#QShortcut(QKeySequence('Return'), self.width, self.editEdit)

		settings = QSettings()
		if settings.value('recentFiles') is not None:
			self.recentFiles = settings.value('recentFiles')
			self.restoreGeometry(settings.value('Geometry'))
			self.restoreState(settings.value('MainWindow/State'))
		else:
			self.recentFiles = list()
		self.setMinimumSize(600, 600)
		self.setWindowTitle('My Movies')
		QTimer.singleShot(0, self.loadInitialFile)


	def createAction(self, text, slot=None, shortcut=None, icon=None, tip=None, checkable=False, signal='triggered'):
		action = QAction(text, self)
		if icon is not None:
			action.setIcon(QIcon(':/%s.png' % icon))
		if shortcut is not None:
			action.setShortcut(shortcut)
		if tip is not None:
			action.setToolTip(tip)
			action.setStatusTip(tip)
		if slot is not None:
			action.triggered.connect(slot)
		if checkable:
			action.setCheckable(True)
		return action


	def addActions(self, target, actions):
		for action in actions:
			if action is None:
				target.addSeparator()
			else:
				target.addAction(action)


	def loadInitialFile(self):
		settings = QSettings()
		if settings.value('LastFile'):
			fname = str(settings.value('LastFile'))
			if fname and QFile.exists(fname):
				ok, msg = self.movies.load(fname)
				self.statusBar().showMessage(msg, 5000)
			self.updateTable()


	def closeEvent(self, event):
		if self.okToContinue():
			settings = QSettings()
			filename = QVariant(str(self.movies.fileName())) if self.movies.fileName() is not  None else QVariant()
			settings.setValue('LastFile', filename)
			#recentFiles = QVariant(self.recentFiles) if self.recentFiles else QVariant()
			#settings.setValue('recentFiles', recentFiles)
			settings.setValue('Geometry', QVariant(self.saveGeometry()))
			settings.setValue('MainWindow/State', QVariant(self.saveState()))
		else:
			event.ignore()


	def okToContinue(self):
		if self.movies.isDirty():
			reply = QMessageBox.question(self, 'My Movies - Unsaved Changes',
					'Save Unsaved Changes?', QMessageBox.Save|QMessageBox.Discard|QMessageBox.Cancel)
			if reply == QMessageBox.Cancel:
				return False
			elif reply == QMessageBox.Yes:
				self.fileSave()
		return True


	def updateTable(self, current=None):
		self.table.clear()
		self.table.setRowCount(len(self.movies))
		self.table.setColumnCount(5)
		self.table.setHorizontalHeaderLabels(['Title', 'Year', 'Mins', 'Acquired', 'Notes'])
		self.table.setAlternatingRowColors(True)
		self.table.setEditTriggers(QTableWidget.NoEditTriggers)
		self.table.setSelectionBehavior(QTableWidget.SelectRows)
		self.table.setSelectionMode(QTableWidget.SingleSelection)
		selected = None 

		for row, movie in enumerate(self.movies):
			item = QTableWidget(movie.title)
			if current is not None and current == id(movie):
				selected = item 
			item.setData(Qt.UserRole, QVariant(long(id(movie))))
			self.table.setItem(row, 0, item)
			year = movie.year
			if year != movie.UNKNOWNYEAR:
				item = QTableWidgetItem('%d' % year)
				item.setTextAlignment(Qt.AlignCenter)
				self.table.setItem(row, 1, item)
			minutes = movie.minutes 
			if minutes != movie.UNKNOWNMINUTES:
				item = QTableWidgetItem('%d' % minutes)
				item.setTextAlignment(Qt.AlignRight|Qt.AlignVCenter)
				self.table.setItem(row, 2, item)
			item = QTableWidgetItem(movie.acquired.toString(moviedata.DATEFORMAT))
			item.setTextAlignment(Qt.AlignRight|Qt.AlignVCenter)
			self.table.setItem(row, 3, item)
			notes = movie.notes
			if notes.length > 40:
				notes = notes[:-1] + '...'
			self.table.setItem(row, 4, QTableWidgetItem(notes))
		self.table.resizeColumnToContents(10)
		if selected is not None:
			selected.setSelected(True)
			self.table.setCurrentItem(selected)
			self.table.scrollToItem(selected)


	def updateFileMenu(self):
		pass


	def fileNew(self):
		if not self.okToContinue():
			return
		self.movies.clear()
		self.statusBar().clearMessage()
		self.updateTable()

	
	def fileOpen(self):
		if not self.okToContinue():
			return
		path = (QFileInfo(self.movies.filename()).path() if not self.movies.filename().isEmpty() else '.')
		fname, _ = QFileDialog.getOpenFileName(self, 'My Movies - Load Movie Data', path, 'Movie Data Files ({0})'.format(self.movies.format()))
		if fname:
			ok, msg = self.movies.load(fname)
			self.statusBar().showMessage(msg, 5000)
			self.updateTable()	

	
	def fileSave(self):
		if self.movies.filename().isEmpty():
			return self.fileSaveAs()
		else:
			ok, msg = self.movies.save()
			self.statusBar().showMessage(msg, 5000)
			return ok

	
	def fileSaveAs(self):
		fname = self.movies.filename() if self.movies.filename() else '.'
		fname,_ = QFileDialog.getSaveFileName(self, 'My Movies - Save Movie Data', fname, 'My Movie Data Files ({0})'.format(self.movies.format()))
		if fname:
			if not fname.contains('.'):
				fname += '.mqp'
			ok, msg = self.movies.save(fname)
			self.statusBar().showMessage(msg, 5000)
			return ok
		return False
		

	def fileExportXml(self):
		fname = self.movies.filename()
		if fname.isEmpty():
			fname = '.'
		else:
			i = fname.lastIndexOf('.')
			if i > 0:
				fname = fname.left(i)
				fname += '.xml'
		fname,_ = QFileDialog.getSaveFileName(self, 'My Movies - Export Movie Data', fname, 'My Movies XML Files (*.xml)')
		if fname:
			if not fname.contains('.'):
				fname += '.xml'
			ok, msg = self.movies.exportXml(fname)
			self.statusBar().showMessage(msg, 5000)


	def fileImportDOM(self):
		self.fileImport('dom')


	def fileImportSAX(self):
		self.fileImport('sax')


	def fileImport(self, format):
		if not self.okToContinue():
			return
		path = (QFileInfo(self.movies.filename()).path() if not self.movies.filename().isEmpty() else '.')
		fname, _ = QFileDialog.getOpenFileName(self, 'My Movies - Import Movie Data', path, 'Movie Data Files (*.xml)')
		if not fname.isEmpty():
			if format.lower() == 'dom':
				ok, msg = self.movies.importDOM(fname)
			else:
				ok, msg = self.movies.importSAX(fname)
			self.statusBar().showMessage(msg, 5000)
			self.updateTable


	def editEdit(self):
		movie = self.currentMovie()
		if movie is not None:
			form = edlg.AddEditMovieDlg(self.movies, movie, self)
			if form.exec_():
				self.updateTable(id(movie))

	
	def editAdd(self):
		form = edlg.AddEditMovieDlg(self.movies, None, self)

		if form.exec_():
			self.updateTable(id(form.movie))


	def editRemove(self):
		movie = self.currentMovie()
		if movie is not None:
			year = (' {0}'.format(movie.year) if movie.year != movie.UNKNOWNYEAR else '')

			if (QMessageBox.question(self, 'My Movies - Delete Movie', "Delete Movie '{0}' {1}".format(movie.title, year), QMessageBox.Yes|QMessageBox.No) ==  QMessageBox.Yes):
				self.movies.delete(movie)
				self.updateTable()


	def currentMovie(self):
		row = self.table.currentRow()
		if row > -1:
			item = self.table.item(row, 0)
			id = item.data(Qt.UserRole).toLongLong()[0]
			return self.movies.movieFromId(id)
		return None

	def helpAbout(self):
		pass

	def helpHelp(self):
		pass


if __name__ == '__main__':
	app = QApplication(sys.argv)
	app.setOrganizationName('Qtrac Ltd')
	app.setOrganizationDomain('qtrac.eu')
	app.setApplicationName('My Movies')
	app.setWindowIcon(QIcon(':/icon.png'))
	form = MainWindow()
	form.show()
	app.exec_()