from unicurses import *
from curses.textpad import Textbox, rectangle
import requests

ENTER_KEY = 10
BACKSPACE_KEY = 263
ESCAPE_KEY = 27

def sign_send(to_send):
    try:
        data = dict(sign=to_send, on_behalf_of='protovac')
        r = requests.post('https://api.my.protospace.ca/stats/sign/', data=data, timeout=5)
        r.raise_for_status()
        return 'Success!'
    except:
        return 'Error.'

def fetch_stats():
    try:
        r = requests.get('https://api.my.protospace.ca/stats/', timeout=5)
        r.raise_for_status()
        return r.json()
    except:
        return 'Error.'

skip_input = False
current_screen = 'home'

highlight = 1
choice = 0
c = 0

# highlighting:
#wattron(menu_win, A_REVERSE)
#mvwaddstr(menu_win, y, x, choices[i])
#wattroff(menu_win, A_REVERSE)

stdscr = initscr()
clear()
noecho()
cbreak()
curs_set(0)

keypad(stdscr, True)

sign_to_send = ''
stats = {}

while True:
    if current_screen == 'home':
        mvaddstr(1, 1, 'PROTOVAC  -  can you smell the phosphorus?')
        mvaddstr(4, 4, '[T] Stats')
        mvaddstr(6, 4, '[S] Sign')
        #mvaddstr(8, 4, '[C] Classes')
        #mvaddstr(10, 4, '[F] Forum')

        mvaddstr(23, 1, '')
        clrtoeol()
        refresh()
    elif current_screen == 'debug':
        mvaddstr(1, 1, 'PROTOVAC')
        mvaddstr(3, 1, 'Debug Mode')
        mvaddstr(4, 1, '==========')
        mvaddstr(6, 1, str.format('Character pressed = {0}', c))
        clrtoeol()

        mvaddstr(23, 1, '[B] Back')
        clrtoeol()
        refresh()
    elif current_screen == 'stats':
        mvaddstr(1, 1, 'PROTOVAC')
        mvaddstr(3, 1, 'Protospace Stats')
        mvaddstr(4, 1, '================')
        if stats:
            mvaddstr(6 , 1, 'Next meeting: {}'.format(stats['next_meeting']))
            mvaddstr(8 , 1, 'Next clean:   {}'.format(stats['next_clean']))
            mvaddstr(10, 1, 'Next class:   {}'.format(stats['next_class']['datetime']))
            mvaddstr(11, 1, '              {}'.format(stats['next_class']['name']))
            mvaddstr(13, 1, 'Last class:   {}'.format(stats['prev_class']['datetime']))
            mvaddstr(14, 1, '              {}'.format(stats['prev_class']['name']))

            mvaddstr(16, 1, 'Member count: {}   Green: {}   Paused / expired: {}'.format(
                stats['member_count'],
                stats['green_count'],
                stats['paused_count'],
            ))
            mvaddstr(18, 1, 'Card scans:   {}'.format(stats['card_scans']))
        else:
            mvaddstr(6, 1, 'Loading...')

        mvaddstr(23, 1, '[B] Back')
        clrtoeol()
        refresh()

        if not stats:
            stats = fetch_stats()
            skip_input = True
    elif current_screen == 'sign':
        mvaddstr(1, 1, 'PROTOVAC')
        mvaddstr(3, 1, 'Protospace Sign')
        mvaddstr(4, 1, '===============')
        mvaddstr(6, 1, 'Send a message to the sign in the welcome room and classroom.')

        if sign_to_send:
            mvaddstr(8, 4, sign_to_send)
            mvaddstr(23, 1, '[ENTER] Send  [ESC] Cancel')
        else:
            mvaddstr(8, 4, '[E] Edit message')
            mvaddstr(23, 1, '[B] Back')

        clrtoeol()
        refresh()

    if skip_input:
        skip_input = False
    else:
        try:
            c = wgetch(stdscr)
        except KeyboardInterrupt:
            refresh()
            endwin()
            break

    if c == KEY_UP:
        pass
    elif c == KEY_DOWN:
        pass
    elif c == 10:   # ENTER is pressed
        pass

    button = chr(c).lower()

    if current_screen == 'home':
        if button == 't':
            current_screen = 'stats'
            clear()
        elif button == 's':
            current_screen = 'sign'
            clear()
        elif button == 'd':
            current_screen = 'debug'
            clear()
    elif current_screen == 'stats':
        if button == 'b':
            current_screen = 'home'
            stats = {}
            clear()
    elif current_screen == 'sign':
        if sign_to_send:
            if c == BACKSPACE_KEY:
                sign_to_send = sign_to_send[:-2] + '_'
            elif c == ESCAPE_KEY:
                sign_to_send = ''
            elif c == ENTER_KEY:
                if len(sign_to_send) > 1:
                    mvaddstr(10, 4, 'Sending...')
                    refresh()
                    sign_send(sign_to_send[:-1])
                    sign_to_send = ''
            else:
                if c < 127 and c > 31:
                    sign_to_send = sign_to_send[:-1] + chr(c) + '_'
            clear()
        elif button == 'b':
            current_screen = 'home'
            clear()
        elif button == 'e':
            sign_to_send = '_'
            clear()

