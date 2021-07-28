from PyQt5.QtWidgets import QWidget
import subprocess
import json

class ThreadView(QWidget):
    def __init__(self, app, thread_id, parent=None):
        super().__init__(parent)
        self.app = app
        self.thread_id = thread_id
        self.refresh()

    def refresh(self):
        r = subprocess.run(['notmuch', 'show', '--format=json', self.thread_id],
                stdout=subprocess.PIPE)
        self.json_str = r.stdout.decode('utf-8')
        self.d = json.loads(self.json_str)

        # store a flattened version of the thread
        self.thread = []
        self.dft(self.d)
        self.thread.sort(key=lambda m: m['timestamp'])
        print('thread of size: %d' % len(self.thread))

    def dft(self, d):
        if isinstance(d, list):
            for x in d: self.dft(x)
        else:
            self.thread.append(d)
