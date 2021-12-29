global_keymap = {
  'Q':       lambda a: a.quit(),
  'Z Z':     lambda a: a.quit(),
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
  '<space>': lambda p: p.scroll_message(20),
  'j':       lambda p: p.scroll_message(1),
  'k':       lambda p: p.scroll_message(-1),
  'C-d':     lambda p: p.scroll_message(20),
  'C-u':     lambda p: p.scroll_message(-20),
  'u':       lambda p: p.toggle_message_tag('unread'),
  'f':       lambda p: p.toggle_message_tag('flagged'),
  'H':       lambda p: p.toggle_html(),
  'r':       lambda p: p.reply(),
}

compose_keymap = {
  '<enter>': lambda p: p.edit(),
  'S':       lambda p: p.send(),
}

command_bar_keymap = {
  '<enter>':  lambda b: b.accept(),
  '<escape>': lambda b: b.close(),
}
