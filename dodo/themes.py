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

# Catppuccin pallette
# https://github.com/catppuccin/catppuccin
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

catppuccin_macchiato = {
  'bg': cat_macchiato_p['base'],
  'fg': cat_macchiato_p['text'],
  'fg_bright': cat_macchiato_p['lavender'],
  'fg_dim': cat_macchiato_p['subtext0'],
  'fg_good': cat_macchiato_p['green'],
  'fg_bad': cat_macchiato_p['red'],
  'bg_alt': cat_macchiato_p['surface1'],
  'bg_button': cat_macchiato_p['overlay1'],
  'fg_button': cat_macchiato_p['crust'],
  'fg_link': cat_macchiato_p['blue'],
  'bg_highlight': cat_macchiato_p['peach'],
  'fg_highlight': cat_macchiato_p['crust'],
  'fg_subject': cat_macchiato_p['text'],
  'fg_subject_unread': cat_macchiato_p['sapphire'],
  'fg_subject_flagged': cat_macchiato_p['yellow'],
  'fg_from': cat_macchiato_p['lavender'],
  'fg_date': cat_macchiato_p['mauve'],
  'fg_tags': cat_macchiato_p['teal'],
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
