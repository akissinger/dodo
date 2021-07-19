from PyQt5.QtWidgets import QApplication, QTreeView
from PyQt5.QtCore import QAbstractItemModel, QModelIndex, Qt
import dm

app = QApplication([])
dm.style.apply_style(app)
model = dm.search.SearchModel('tag:inbox')
# model = dm.search.SearchModel('*')
view = QTreeView()
view.resize(1024,768)
view.setModel(model)
view.resizeColumnToContents(0)
view.setColumnWidth(1, 150)
view.setColumnWidth(2, 600)

view.show()
app.exec()

