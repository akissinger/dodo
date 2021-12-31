#     Dodo - A graphical, hackable email client based on notmuch
#     Copyright (C) 2021 - Aleks Kissinger
#
# This file is part of Dodo
#
# Dodo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Dodo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Dodo. If not, see <https://www.gnu.org/licenses/>.

global_keymap = {
  '?':       ('show help', lambda a: a.show_help()),
  'Q':       ('quit', lambda a: a.quit()),
  'Z Z':     ('quit', lambda a: a.quit()),
  '`':       ('sync mail', lambda a: a.sync_mail(quiet=False)),
  'l':       ('next panel', lambda a: a.next_panel()),
  'h':       ('previous panel', lambda a: a.previous_panel()),
  'x':       ('close panel', lambda a: a.close_panel()),
  'X':       ('close all', lambda a: [a.close_panel(i) for i in reversed(range(a.num_panels()))]),
  'c':       ('compose', lambda a: a.compose()),
  'I':       ('show inbox', lambda a: a.search('tag:inbox')),
  'U':       ('show unread', lambda a: a.search('tag:unread')),
  'F':       ('show flagged', lambda a: a.search('tag:flagged')),
  '/':       ('search', lambda a: a.command_bar.open('search')),
  't':       ('tag', lambda a: a.command_bar.open('tag')),
}

search_keymap = {
  'j':       ('next thread', lambda p: p.next_thread()),
  'k':       ('previous thread', lambda p: p.previous_thread()),
  '<down>':  ('next thread', lambda p: p.next_thread()),
  '<up>':    ('previous thread', lambda p: p.previous_thread()),
  'g g':     ('first thread', lambda p: p.first_thread()),
  'G':       ('last thread', lambda p: p.last_thread()),
  'C-d':     ('down 20', lambda p: [p.next_thread() for i in range(20)]),
  'C-u':     ('up 20', lambda p: [p.previous_thread() for i in range(20)]),
  '<enter>': ('open thread', lambda p: p.open_current_thread()),
  'a':       ('tag -inbox -unread', lambda p: p.tag_thread('-inbox -unread')),
  'u':       ('toggle unread', lambda p: p.toggle_thread_tag('unread')),
  'f':       ('toggle flagged', lambda p: p.toggle_thread_tag('flagged')),
}

thread_keymap = {
  'J':       ('next message', lambda p: p.next_message()),
  'K':       ('previous message', lambda p: p.previous_message()),
  'g g':     ('top of message', lambda p: p.scroll_message(pos='top')),
  'G':       ('bottom of message', lambda p: p.scroll_message(pos='bottom')),
  'j':       ('scroll down', lambda p: p.scroll_message(lines=1)),
  'k':       ('scroll up', lambda p: p.scroll_message(lines=-1)),
  'C-d':     ('scroll down more', lambda p: p.scroll_message(lines=10)),
  'C-u':     ('scroll up more', lambda p: p.scroll_message(lines=-10)),
  '<space>': ('page down', lambda p: p.scroll_message(pages=1)),
  '-':       ('page up', lambda p: p.scroll_message(pages=-1)),
  'u':       ('toggle unread', lambda p: p.toggle_message_tag('unread')),
  'f':       ('toggle flagged', lambda p: p.toggle_message_tag('flagged')),
  'H':       ('toggle HTML', lambda p: p.toggle_html()),
  'r':       ('reply to all', lambda p: p.reply(to_all=True)),
  'R':       ('reply', lambda p: p.reply(to_all=False)),
  'A':       ('show attachments in file browser', lambda p: p.open_attachments()),
}

compose_keymap = {
  '<enter>': ('edit message', lambda p: p.edit()),
  'S':       ('send', lambda p: p.send()),
  'a':       ('attach file', lambda p: p.attach_file()),
}

command_bar_keymap = {
  '<enter>':  ('accept', lambda b: b.accept()),
  '<escape>': ('close', lambda b: b.close()),
  '<down>':   ('history next', lambda b: b.history_next()),
  '<up>':     ('history previous', lambda b: b.history_previous()),
  'C-n':      ('history next', lambda b: b.history_next()),
  'C-p':      ('history previous', lambda b: b.history_previous()),
}
