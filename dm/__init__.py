from PyQt5.QtWidgets import QApplication

from . import search
from . import style

if __name__ == '__main__':
    app = QApplication([])
    app.setApplicationName('Dodo')
    style.apply_style(app)
    view = search.SearchView('tag:inbox')
    view.resize(1024,768)
    view.show()
    app.exec()
