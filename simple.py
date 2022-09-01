#!/home/tanner/protovac/env/bin/python

import time
import curses

stdscr = curses.initscr()
curses.noecho()
curses.cbreak()
stdscr.keypad(True)

stdscr.addstr(5, 5, 'Hello world!')
stdscr.refresh()

stdscr.getch()

curses.nocbreak()
stdscr.keypad(False)
curses.echo()
curses.endwin()
