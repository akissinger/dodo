global_keymap = {
  'Q':       lambda a: a.quit(),
  'Z Z':     lambda a: a.quit(),
  '`':       lambda a: a.sync_mail(quiet=False),
  'l':       lambda a: a.next_panel(),
  'h':       lambda a: a.previous_panel(),
  'x':       lambda a: a.close_panel(),
  'X':       lambda a: [a.close_panel(i) for i in range(a.num_panels()-1, -1, -1)],
  'c':       lambda a: a.compose(),
  'I':       lambda a: a.search('tag:inbox'),
  'U':       lambda a: a.search('tag:unread'),
  'F':       lambda a: a.search('tag:flagged'),
  '/':       lambda a: a.command_bar.open('search'),
  't':       lambda a: a.command_bar.open('tag'),
}

search_keymap = {
  'j':       lambda p: p.next_thread(),
  'k':       lambda p: p.previous_thread(),
  '<down>':  lambda p: p.next_thread(),
  '<up>':    lambda p: p.previous_thread(),
  'g g':     lambda p: p.first_thread(),
  'G':       lambda p: p.last_thread(),
  'C-d':     lambda p: [p.next_thread() for i in range(20)],
  'C-u':     lambda p: [p.previous_thread() for i in range(20)],
  '<enter>': lambda p: p.open_current_thread(),
  'a':       lambda p: p.tag_thread('-inbox -unread'),
  'u':       lambda p: p.toggle_thread_tag('unread'),
  'f':       lambda p: p.toggle_thread_tag('flagged'),
}

thread_keymap = {
  'J':       lambda p: p.next_message(),
  'K':       lambda p: p.previous_message(),
  'g g':     lambda p: p.scroll_message(pos='top'),
  'G':       lambda p: p.scroll_message(pos='bottom'),
  'j':       lambda p: p.scroll_message(lines=1),
  'k':       lambda p: p.scroll_message(lines=-1),
  'C-d':     lambda p: p.scroll_message(lines=10),
  'C-u':     lambda p: p.scroll_message(lines=-10),
  '<space>': lambda p: p.scroll_message(pages=1),
  '-':       lambda p: p.scroll_message(pages=-1),
  'u':       lambda p: p.toggle_message_tag('unread'),
  'f':       lambda p: p.toggle_message_tag('flagged'),
  'H':       lambda p: p.toggle_html(),
  'r':       lambda p: p.reply(to_all=True),
  'R':       lambda p: p.reply(to_all=False),
}

compose_keymap = {
  '<enter>': lambda p: p.edit(),
  'S':       lambda p: p.send(),
}

command_bar_keymap = {
  '<enter>':  lambda b: b.accept(),
  '<escape>': lambda b: b.close(),
  '<down>':   lambda b: b.history_next(),
  '<up>':     lambda b: b.history_previous(),
  'C-n':      lambda b: b.history_next(),
  'C-p':      lambda b: b.history_previous(),
}
