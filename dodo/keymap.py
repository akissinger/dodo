global_keymap = {
  'q': lambda a: a.quit(),
}

search_keymap = {
  'j':  lambda s: s.next_thread(),
  'k':  lambda s: s.previous_thread(),
  'g g': lambda s: print('got gg'),
  'g g g': lambda s: print('got ggg'),
}
