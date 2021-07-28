global_keymap = {
  'q': lambda a: a.quit(),
}

search_keymap = {
  'j':   lambda s: s.next_thread(),
  'k':   lambda s: s.previous_thread(),
  'g g': lambda s: s.first_thread(),
  'G':   lambda s: s.last_thread(),
  'C-d': lambda s: [s.next_thread() for i in range(20)],
  'C-u': lambda s: [s.previous_thread() for i in range(20)],
}
