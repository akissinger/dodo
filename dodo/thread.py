from PyQt5.QtWidgets import QWidget
import subprocess
import json

# recursively search a message body for content of a particular type and return the first
# occurance
def find_content(m, ty):
    content = []

    def dfs(x):
        global content, ty
        if isinstance(x, list):
            for y in x: dfs(y)
        elif isinstance(x, dict) and 'content-type' in x and 'content' in x:
            if x['content-type'] == ty:
                content.append(x['content'])
            elif isinstance(x['content'], list):
                for y in x['content']: dfs(y)

    dfs(m)
    return content


class ThreadView(QWidget):
    def __init__(self, app, thread_id, parent=None):
        super().__init__(parent)
        self.app = app
        self.thread_id = thread_id
        self.refresh()

    def refresh(self):
        r = subprocess.run(['notmuch', 'show', '--format=json', '--include-html', self.thread_id],
                stdout=subprocess.PIPE)
        self.json_str = r.stdout.decode('utf-8')
        self.d = json.loads(self.json_str)

        # store a flattened version of the thread
        self.thread = []
        self.dft(self.d)
        self.thread.sort(key=lambda m: m['timestamp'])
        print('thread of size: %d' % len(self.thread))

        for m in self.thread:
            c = find_content(m['body'], 'text/html')
            if not c: c = find_content(m['body'], 'text/plain')

    def dft(self, d):
        if isinstance(d, list):
            for x in d: self.dft(x)
        else:
            self.thread.append(d)

