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

from __future__ import annotations
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import QApplication


# palettes used in theme definitions
nord_p = {
  'polar0':  '#2e3440',
  'polar1':  '#3b4252',
  'polar2':  '#434c5e',
  'polar3':  '#4c566a',
  'snow0':   '#d8dee9',
  'snow1':   '#e5e9f0',
  'snow2':   '#eceff4',
  'frost0':  '#8fbcbb',
  'frost1':  '#88c0d0',
  'frost2':  '#81a1c1',
  'frost3':  '#5e81ac',
  'aurora0': '#bf616a',
  'aurora1': '#d08770',
  'aurora2': '#ebcb8b',
  'aurora3': '#a3be8c',
  'aurora4': '#b48ead',
}

solarized_p = {
  'base03':    '#002b36',
  'base02':    '#073642',
  'base01':    '#586e75',
  'base00':    '#657b83',
  'base0':     '#839496',
  'base1':     '#93a1a1',
  'base2':     '#eee8d5',
  'base3':     '#fdf6e3',
  'yellow':    '#b58900',
  'orange':    '#cb4b16',
  'red':       '#dc322f',
  'magenta':   '#d33682',
  'violet':    '#6c71c4',
  'blue':      '#268bd2',
  'cyan':      '#2aa198',
  'green':     '#859900',
}

cat_macchiato_p = {
  'rosewater':  '#f4dbd6',
  'flamingo':   '#f0c6c6',
  'pink':       '#f5bde6',
  'mauve':      '#c6a0f6',
  'red':        '#ed8796',
  'maroon':     '#ee99a0',
  'peach':      '#f5a97f',
  'yellow':     '#eed49f',
  'green':      '#a6da95',
  'teal':       '#8bd5ca',
  'sky':        '#91d7e3',
  'sapphire':   '#7dc4e4',
  'blue':       '#8aadf4',
  'lavender':   '#b7bdf8',
  'text':       '#cad3f5',
  'subtext1':   '#b8c0e0',
  'subtext0':   '#a5adcb',
  'overlay2':   '#939ab7',
  'overlay1':   '#8087a2',
  'overlay0':   '#6e738d',
  'surface2':   '#5b6078',
  'surface1':   '#494d64',
  'surface0':   '#363a4f',
  'base':       '#24273a',
  'mantle':     '#1e2030',
  'crust':      '#181926',
}

gruvbox_p = {
  'dark0_hard':     '#1d2021',
  'dark0':          '#282828',
  'dark0_soft':     '#32302f',
  'dark1':          '#3c3836',
  'dark2':          '#504945',
  'dark3':          '#665c54',
  'dark4':          '#7c6f64',

  'gray_245':       '#928374',
  'gray_244':       '#928374',

  'light0_hard':    '#f9f5d7',
  'light0':         '#fbf1c7',
  'light0_soft':    '#f2e5bc',
  'light1':         '#ebdbb2',
  'light2':         '#d5c4a1',
  'light3':         '#bdae93',
  'light4':         '#a89984',

  'bright_red':     '#fb4934',
  'bright_green':   '#b8bb26',
  'bright_yellow':  '#fabd2f',
  'bright_blue':    '#83a598',
  'bright_purple':  '#d3869b',
  'bright_aqua':    '#8ec07c',
  'bright_orange':  '#fe8019',

  'neutral_red':    '#cc241d',
  'neutral_green':  '#98971a',
  'neutral_yellow': '#d79921',
  'neutral_blue':   '#458588',
  'neutral_purple': '#b16286',
  'neutral_aqua':   '#689d6a',
  'neutral_orange': '#d65d0e',

  'faded_red':      '#9d0006',
  'faded_green':    '#79740e',
  'faded_yellow':   '#b57614',
  'faded_blue':     '#076678',
  'faded_purple':   '#8f3f71',
  'faded_aqua':     '#427b58',
  'faded_orange':   '#af3a03',
}

catppuccin_macchiato = {
  'bg': cat_macchiato_p['base'],
  'fg': cat_macchiato_p['text'],
  'fg_bright': cat_macchiato_p['lavender'],
  'fg_dim': cat_macchiato_p['overlay1'],
  'fg_good': cat_macchiato_p['green'],
  'fg_bad': cat_macchiato_p['red'],
  'bg_alt': cat_macchiato_p['crust'],
  'bg_button': cat_macchiato_p['surface0'],
  'fg_button': cat_macchiato_p['rosewater'],
  'fg_link': cat_macchiato_p['blue'],
  'bg_highlight': cat_macchiato_p['blue'],
  'fg_highlight': cat_macchiato_p['crust'],
  'fg_subject': cat_macchiato_p['text'],
  'fg_subject_unread': cat_macchiato_p['mauve'],
  'fg_subject_flagged': cat_macchiato_p['yellow'],
  'fg_from': cat_macchiato_p['blue'],
  'fg_date': cat_macchiato_p['flamingo'],
  'fg_tags': cat_macchiato_p['peach'],
}
"""Theme based on the `Catppuchin`_ palette (macchiatto version).

.. _Catppuchin: https://github.com/catppuccin/catppuccin
"""

solarized_dark = {
  'bg': solarized_p['base02'],
  'fg': solarized_p['base1'],
  'fg_bright': solarized_p['violet'],
  'fg_dim': solarized_p['base01'],
  'fg_good': solarized_p['green'],
  'fg_bad': solarized_p['red'],
  'bg_alt': solarized_p['base03'],
  'bg_button': solarized_p['base03'],
  'fg_button': solarized_p['base01'],
  'fg_link': solarized_p['violet'],
  'bg_highlight': solarized_p['base2'],
  'fg_highlight': solarized_p['base01'],
  'fg_subject': solarized_p['base0'],
  'fg_subject_unread': solarized_p['base2'],
  'fg_subject_flagged': solarized_p['violet'],
  'fg_from': solarized_p['blue'],
  'fg_date': solarized_p['cyan'],
  'fg_tags': solarized_p['violet'],
}
"""Theme based on the `Solarized`_ palette (dark background).

.. _Solarized: https://ethanschoonover.com/solarized/
"""

solarized_light = {
  'bg': solarized_p['base3'],
  'fg': solarized_p['base01'],
  'fg_bright': solarized_p['violet'],
  'fg_dim': solarized_p['base1'],
  'fg_good': solarized_p['green'],
  'fg_bad': solarized_p['red'],
  'bg_alt': solarized_p['base3'],
  'bg_button': solarized_p['base3'],
  'fg_button': solarized_p['base1'],
  'fg_link': solarized_p['violet'],
  'bg_highlight': solarized_p['base02'],
  'fg_highlight': solarized_p['base1'],
  'fg_subject': solarized_p['base0'],
  'fg_subject_unread': solarized_p['base02'],
  'fg_subject_flagged': solarized_p['violet'],
  'fg_from': solarized_p['blue'],
  'fg_date': solarized_p['cyan'],
  'fg_tags': solarized_p['violet'],
}
"""Theme based on the `Solarized`_ palette (light background).

.. _Solarized: https://ethanschoonover.com/solarized/
"""

nord = {
  'bg': nord_p['polar0'],
  'fg': nord_p['snow0'],
  'fg_bright': nord_p['aurora4'],
  'fg_dim': nord_p['polar3'],
  'fg_good': nord_p['aurora3'],
  'fg_bad': nord_p['aurora0'],
  'bg_alt': nord_p['polar1'],
  'bg_button': nord_p['polar3'],
  'fg_button': nord_p['snow2'],
  'fg_link': nord_p['frost2'],
  'bg_highlight': nord_p['aurora3'],
  'fg_highlight': nord_p['polar0'],
  'fg_subject': nord_p['snow0'],
  'fg_subject_unread': nord_p['aurora4'],
  'fg_subject_flagged': nord_p['aurora2'],
  'fg_from': nord_p['frost3'],
  'fg_date': nord_p['polar3'],
  'fg_tags': nord_p['frost2'],
}
"""Theme based on the `Nord`_ palette

.. _Nord: https://www.nordtheme.com/
"""

gruvbox_light = {
  'bg': gruvbox_p['light0'],
  'fg': gruvbox_p['dark1'],
  'fg_bright': gruvbox_p['dark0'],
  'fg_dim': gruvbox_p['dark2'],
  'fg_good': gruvbox_p['neutral_green'],
  'fg_bad': gruvbox_p['neutral_red'],
  'bg_alt': gruvbox_p['light1'],
  'bg_button': gruvbox_p['light1'],
  'fg_button': gruvbox_p['dark2'],
  'fg_link': gruvbox_p['neutral_purple'],
  'bg_highlight': gruvbox_p['light0'],
  'fg_highlight': gruvbox_p['neutral_yellow'],
  'fg_subject': gruvbox_p['dark3'],
  'fg_subject_unread': gruvbox_p['neutral_green'],
  'fg_subject_flagged': gruvbox_p['neutral_orange'],
  'fg_from': gruvbox_p['neutral_blue'],
  'fg_date': gruvbox_p['neutral_aqua'],
  'fg_tags': gruvbox_p['neutral_purple'],
}
"""Theme based on the `Gruvbox`_ palette (light background)

.. _Gruvbox: https://github.com/morhetz/gruvbox
"""

gruvbox_light_hard = gruvbox_light.copy()
"""Theme based on the `Gruvbox`_ palette (light background, hard contrast)

.. _Gruvbox: https://github.com/morhetz/gruvbox
"""

gruvbox_light_soft = gruvbox_light.copy()
"""Theme based on the `Gruvbox`_ palette (light background, soft contrast)

.. _Gruvbox: https://github.com/morhetz/gruvbox
"""

gruvbox_light_hard['bg'] = gruvbox_p['light0_hard']
gruvbox_light_soft['bg'] = gruvbox_p['light0_soft']

gruvbox_dark = gruvbox_light.copy()
"""Theme based on the `Gruvbox`_ palette (dark background)

.. _Gruvbox: https://github.com/morhetz/gruvbox
"""
gruvbox_dark.update({
  'bg': gruvbox_p['dark0'],
  'fg': gruvbox_p['light1'],
  'fg_bright': gruvbox_p['light0'],
  'fg_dim': gruvbox_p['light4'],
  'bg_alt': gruvbox_p['dark1'],
  'bg_button': gruvbox_p['dark1'],
  'fg_button': gruvbox_p['light2'],
  'bg_highlight': gruvbox_p['dark0'],
  'fg_subject': gruvbox_p['light3'],
})

gruvbox_dark_hard = gruvbox_dark.copy()
"""Theme based on the `Gruvbox`_ palette (dark background, hard contrast)

.. _Gruvbox: https://github.com/morhetz/gruvbox
"""

gruvbox_dark_soft = gruvbox_dark.copy()
"""Theme based on the `Gruvbox`_ palette (dark background, soft contrast)

.. _Gruvbox: https://github.com/morhetz/gruvbox
"""

gruvbox_dark_hard['bg'] = gruvbox_p['dark0_hard']
gruvbox_dark_soft['bg'] = gruvbox_p['dark0_soft']


def apply_theme(theme: dict) -> None:
    """"Apply the given theme to GUI components

    This is called when :class:`~dodo.app.Dodo` is initialised."""

    # Force the style to be the same on all OSs:
    QApplication.setStyle("Fusion")
    # Now use a palette to switch to theme colors:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(theme['bg']))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(theme['fg']))
    palette.setColor(QPalette.ColorRole.Base, QColor(theme['bg']))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(theme['bg_alt']))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(theme['fg']))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(theme['fg']))
    palette.setColor(QPalette.ColorRole.Text, QColor(theme['fg']))
    palette.setColor(QPalette.ColorRole.Button, QColor(theme['bg_button']))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(theme['fg_button']))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(theme['fg_bright']))
    palette.setColor(QPalette.ColorRole.Link, QColor(theme['fg_link']))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(theme['bg_highlight']))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(theme['fg_highlight']))
    QApplication.setPalette(palette)
