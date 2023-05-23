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
  'Q':       ('quit', lambda a: a.prompt_quit()),
  '`':       ('sync mail', lambda a: a.sync_mail(quiet=False)),
  'l':       ('next panel', lambda a: a.next_panel()),
  'h':       ('previous panel', lambda a: a.previous_panel()),
  'x':       ('close panel', lambda a: a.close_panel()),
  'X':       ('close all', lambda a: [a.close_panel(i) for i in reversed(range(a.num_panels()))]),
  'c':       ('compose', lambda a: a.open_compose()),
  'I':       ('show inbox', lambda a: a.open_search('tag:inbox')),
  'U':       ('show unread', lambda a: a.open_search('tag:inbox and tag:unread')),
  'F':       ('show flagged', lambda a: a.open_search('tag:flagged')),
  'T':       ('show tags', lambda a: a.open_tags()),
  '/':       ('search', lambda a: a.search_bar()),
  't t':     ('tag', lambda a: a.tag_bar()),
  't m':     ('tag marked', lambda a: a.tag_bar(mode='tag marked')),
}
"""The global keymap

A dictionary from key strings to pairs consisting of a short docstring and a function
taking :class:`~dodo.app.Dodo` as input. This commands can be superseded by the various
local keymaps.
"""

search_keymap = {
  'j':       ('next thread', lambda p: p.next_thread()),
  'k':       ('previous thread', lambda p: p.previous_thread()),
  '<down>':  ('next thread', lambda p: p.next_thread()),
  '<up>':    ('previous thread', lambda p: p.previous_thread()),
  '<tab>':   ('next unread', lambda p: p.next_thread(unread=True)),
  'S-<tab>': ('previous unread', lambda p: p.previous_thread(unread=True)),
  'g g':     ('first thread', lambda p: p.first_thread()),
  'G':       ('last thread', lambda p: p.last_thread()),
  'C-d':     ('down 20', lambda p: [p.next_thread() for i in range(20)]),
  'C-u':     ('up 20', lambda p: [p.previous_thread() for i in range(20)]),
  '<enter>': ('open thread', lambda p: p.open_current_thread()),
  'a':       ('tag -inbox -unread', lambda p: p.tag_thread('-inbox -unread')),
  'u':       ('toggle unread', lambda p: p.toggle_thread_tag('unread')),
  'f':       ('toggle flagged', lambda p: p.toggle_thread_tag('flagged')),
  '<space>': ('toggle marked', lambda p: [p.toggle_thread_tag('marked'), p.next_thread()]),
}
"""The local keymap for search panels

A dictionary from key strings to pairs consisting of a short docstring and a function
taking :class:`~dodo.search.SearchPanel` as input.
"""

tag_keymap = {
  'j':       ('next tag', lambda p: p.next_tag()),
  'k':       ('previous tag', lambda p: p.previous_tag()),
  '<down>':  ('next tag', lambda p: p.next_tag()),
  '<up>':    ('previous tag', lambda p: p.previous_tag()),
  'g g':     ('first tag', lambda p: p.first_tag()),
  'G':       ('last tag', lambda p: p.last_tag()),
  'C-d':     ('down 20', lambda p: [p.next_tag() for i in range(20)]),
  'C-u':     ('up 20', lambda p: [p.previous_tag() for i in range(20)]),
  '<enter>': ('search tag', lambda p: p.search_current_tag()),
}
"""The local keymap for the tag panel

A dictionary from key strings to pairs consisting of a short docstring and a function
taking :class:`~dodo.search.TagPanel` as input.
"""

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
  'C-f':     ('forward', lambda p: p.forward()),
  'A':       ('show attachments in file browser', lambda p: p.open_attachments()),
}
"""The local keymap for thread panels

A dictionary from key strings to pairs consisting of a short docstring and a function
taking :class:`~dodo.thread.ThreadPanel` as input.
"""

compose_keymap = {
  '<enter>': ('edit message', lambda p: p.edit()),
  'S':       ('send', lambda p: p.send()),
  'a':       ('attach file', lambda p: p.attach_file()),
  's':       ('toggle PGP-sign', lambda p: p.toggle_pgp_sign()),
  'w':       ('toggle word wrap', lambda p: p.toggle_wrap()),
  ']':       ('next SMTP account', lambda p: p.next_account()),
  '[':       ('previous SMTP account', lambda p: p.previous_account()),
}
"""The local keymap for compose panels

A dictionary from key strings to pairs consisting of a short docstring and a function
taking :class:`~dodo.compose.ComposePanel` as input.
"""

command_bar_keymap = {
  '<enter>':  ('accept', lambda b: b.accept()),
  '<escape>': ('close', lambda b: b.close_bar()),
  '<down>':   ('history next', lambda b: b.history_next()),
  '<up>':     ('history previous', lambda b: b.history_previous()),
  'C-n':      ('history next', lambda b: b.history_next()),
  'C-p':      ('history previous', lambda b: b.history_previous()),
}
"""The keymap active when the command bar is visible

A dictionary from key strings to pairs consisting of a short docstring and a function
taking :class:`~dodo.compose.CommandBar` as input. Unlike the other keymaps, the
command bar keymap doesn't accept keychords. Also, you should avoid mapping alphanumeric
keys to commands, as this will interfere with typing.
"""
