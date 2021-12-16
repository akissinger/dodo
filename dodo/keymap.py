global_keymap = {
  'q': lambda a: a.quit(),
  'l': lambda a: a.next_panel(),
  'h': lambda a: a.previous_panel(),
  'x': lambda a: a.close_panel(),
  'X': lambda a: [a.close_panel(i) for i in range(a.num_panels())],
}

search_keymap = {
  'j':       lambda s: s.next_thread(),
  'k':       lambda s: s.previous_thread(),
  'g g':     lambda s: s.first_thread(),
  'G':       lambda s: s.last_thread(),
  'C-d':     lambda s: [s.next_thread() for i in range(20)],
  'C-u':     lambda s: [s.previous_thread() for i in range(20)],
  '<enter>': lambda s: s.open_current_thread(),
}

thread_keymap = {}
