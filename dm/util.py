from PyQt5.QtCore import Qt

basic_keytab = {
  Qt.Key_Exclam: '!',
  Qt.Key_QuoteDbl: '"',
  Qt.Key_NumberSign: '#',
  Qt.Key_Dollar: '$',
  Qt.Key_Percent: '%',
  Qt.Key_Ampersand: '&',
  Qt.Key_Apostrophe: '\'',
  Qt.Key_ParenLeft: '(',
  Qt.Key_ParenRight: ')',
  Qt.Key_Asterisk: '*',
  Qt.Key_Plus: '+',
  Qt.Key_Comma: ',',
  Qt.Key_Minus: '-',
  Qt.Key_Period: '.',
  Qt.Key_Slash: '/',
  Qt.Key_0: '0',
  Qt.Key_1: '1',
  Qt.Key_2: '2',
  Qt.Key_3: '3',
  Qt.Key_4: '4',
  Qt.Key_5: '5',
  Qt.Key_6: '6',
  Qt.Key_7: '7',
  Qt.Key_8: '8',
  Qt.Key_9: '9',
  Qt.Key_Colon: ':',
  Qt.Key_Semicolon: ';',
  Qt.Key_Less: '<',
  Qt.Key_Equal: '=',
  Qt.Key_Greater: '>',
  Qt.Key_Question: '?',
  Qt.Key_At: '@',
  Qt.Key_A: 'a',
  Qt.Key_B: 'b',
  Qt.Key_C: 'c',
  Qt.Key_D: 'd',
  Qt.Key_E: 'e',
  Qt.Key_F: 'f',
  Qt.Key_G: 'g',
  Qt.Key_H: 'h',
  Qt.Key_I: 'i',
  Qt.Key_J: 'j',
  Qt.Key_K: 'k',
  Qt.Key_L: 'l',
  Qt.Key_M: 'm',
  Qt.Key_N: 'n',
  Qt.Key_O: 'o',
  Qt.Key_P: 'p',
  Qt.Key_Q: 'q',
  Qt.Key_R: 'r',
  Qt.Key_S: 's',
  Qt.Key_T: 't',
  Qt.Key_U: 'u',
  Qt.Key_V: 'v',
  Qt.Key_W: 'w',
  Qt.Key_X: 'x',
  Qt.Key_Y: 'y',
  Qt.Key_Z: 'z',
}

keytab = {
  Qt.Key_Escape: 'escape',
  Qt.Key_Tab: 'tab',
  Qt.Key_Backtab: 'backtab',
  Qt.Key_Backspace: 'backspace',
  Qt.Key_Return: 'enter',
  Qt.Key_Enter: 'enter',
  Qt.Key_Insert: 'insert',
  Qt.Key_Delete: 'delete',
  Qt.Key_Pause: 'pause',
  Qt.Key_Print: 'print',
  Qt.Key_Clear: 'clear',
  Qt.Key_Home: 'home',
  Qt.Key_End: 'end',
  Qt.Key_Left: 'left',
  Qt.Key_Up: 'up',
  Qt.Key_Right: 'right',
  Qt.Key_Down: 'down',
  Qt.Key_PageUp: 'pageup',
  Qt.Key_PageDown: 'pagedown',
  Qt.Key_CapsLock: 'capslock',
  Qt.Key_NumLock: 'numlock',
  Qt.Key_ScrollLock: 'scrolllock',
  Qt.Key_F1: 'f1',
  Qt.Key_F2: 'f2',
  Qt.Key_F3: 'f3',
  Qt.Key_F4: 'f4',
  Qt.Key_F5: 'f5',
  Qt.Key_F6: 'f6',
  Qt.Key_F7: 'f7',
  Qt.Key_F8: 'f8',
  Qt.Key_F9: 'f9',
  Qt.Key_F10: 'f10',
  Qt.Key_F11: 'f11',
  Qt.Key_F12: 'f12',
  Qt.Key_F13: 'f13',
  Qt.Key_F14: 'f14',
  Qt.Key_F15: 'f15',
  Qt.Key_F16: 'f16',
  Qt.Key_F17: 'f17',
  Qt.Key_F18: 'f18',
  Qt.Key_F19: 'f19',
  Qt.Key_F20: 'f20',
  Qt.Key_F21: 'f21',
  Qt.Key_F22: 'f22',
  Qt.Key_F23: 'f23',
  Qt.Key_F24: 'f24',
  Qt.Key_F25: 'f25',
  Qt.Key_F26: 'f26',
  Qt.Key_F27: 'f27',
  Qt.Key_F28: 'f28',
  Qt.Key_F29: 'f29',
  Qt.Key_F30: 'f30',
  Qt.Key_F31: 'f31',
  Qt.Key_F32: 'f32',
  Qt.Key_F33: 'f33',
  Qt.Key_F34: 'f34',
  Qt.Key_F35: 'f35',
  Qt.Key_Menu: 'menu',
  Qt.Key_Help: 'help',
  Qt.Key_Space: 'space',
}

def key_string(e):
    global basic_keytab, keytab
    if e.key() in basic_keytab:
        cmd = basic_keytab[e.key()]
        shift_modifier = False
        if e.modifiers() & Qt.ShiftModifier == Qt.ShiftModifier:
            cmd = cmd.upper()
    elif e.key() in keytab:
        shift_modifier = True
        cmd = '<' + keytab[e.key()] + '>'
    else:
        return None

    if shift_modifier and (e.modifiers() & Qt.ShiftModifier == Qt.ShiftModifier):
        cmd = 'S-' + cmd
    if e.modifiers() & Qt.AltModifier == Qt.AltModifier:
        cmd = 'M-' + cmd
    if e.modifiers() & Qt.ControlModifier == Qt.ControlModifier:
        cmd = 'C-' + cmd

    return cmd
