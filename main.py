#!/home/tanner/protovac/env/bin/python

import curses
import requests
import pytz
import re
from datetime import datetime

try:
    import secrets
    wa_api_key = secrets.wa_api_key
except:
    wa_api_key = None

ENTER_KEY = 10
BACKSPACE_KEY = 263
ESCAPE_KEY = 27

TIMEZONE_CALGARY = pytz.timezone('America/Edmonton')

def format_date(datestr):
    d = datetime.strptime(datestr, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.UTC)
    d = d.astimezone(TIMEZONE_CALGARY)
    return d.strftime('%a %b %-d, %Y  %-I:%M %p')

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

def fetch_classes():
    try:
        r = requests.get('https://api.my.protospace.ca/sessions/', timeout=5)
        r.raise_for_status()
        return r.json()
    except:
        return 'Error.'

if wa_api_key:
    import wolframalpha
    wa_client = wolframalpha.Client(wa_api_key)

def think_send(query):
    result = ''
    try:
        res = wa_client.query(query, timeout=20)
    except BaseException as e:
        logging.error('Error hitting W|A API: {} - {}\n'.format(e.__class__.__name__, e))
        return 'Network error'

    if 'didyoumeans' in res:
        try:
            guess = res['didyoumeans']['didyoumean']['#text']
        except TypeError:
            guess = res['didyoumeans']['didyoumean'][0]['#text']
        next_result, img_url = wa(guess)
        result += 'Confused, using \'' + guess + '\'\n' + next_result
    elif 'pod' in res:
        pods = res['pod'] if isinstance(res['pod'], list) else [res['pod']]
        for pod in pods:
            title = pod['@title']
            subpods = pod['subpod'] if isinstance(pod['subpod'], list) else [pod['subpod']]
            plaintexts = []

            for subpod in subpods:
                if subpod['plaintext']:
                    plaintexts.append(subpod['plaintext'])

            plaintext = '; '.join(plaintexts)

            if any([x in title.lower() for x in ['input', 'conversion', 'corresponding', 'comparison', 'interpretation']]):
                pass
            elif 'definition' in title.lower():
                if plaintext[0] == '1':
                    definition = plaintext.split('\n')[0].split(' | ', 1)[1]
                else:
                    definition = plaintext
                result += 'Definition: ' + definition + '\n'
            elif 'result' in title.lower():
                if re.match(r'^\d+/\d+$', plaintext):
                    plaintext += '\n' + wa(plaintext + '.0')[0]
                if 'base' in query.lower() and '_' in plaintext:
                    plaintext = '(Base conversion) "' + plaintext + '"'
                if '(irreducible)' in plaintext and '/' in plaintext:
                    result, _ = wa(query + '.0')
                    break
                else:
                    result += 'Result: ' + plaintext + '\n'
                    break
            elif plaintext:
                result += title + ': ' + plaintext + '\n'
                break
    else:
        result = 'Error'

    result = result.strip()

    if len(result) > 500:
        result = result[:500] + '... truncated.'
    elif len(result) == 0 and not img_url:
        result = 'Error'

    result = result.replace('Stephen Wolfram', 'Tanner') # lol
    result = result.replace('and his team', '')

    if '(according to' in result:
        result = result.split('(according to')[0]

    return result

skip_input = False
current_screen = 'home'
prev_screen = current_screen

c = 0

# highlighting:
#wattron(menu_win, A_REVERSE)
#mvwaddstr(menu_win, y, x, choices[i])
#wattroff(menu_win, A_REVERSE)

stdscr = curses.initscr()
curses.noecho()
curses.cbreak()
stdscr.keypad(True)
curses.curs_set(0)

sign_to_send = ''
think_to_send = ''
think_result = ''
stats = {}
classes = {}
classes_start = 0

while True:
    if current_screen == 'home':
        stdscr.addstr(1, 1, ' _______  _______      ___    _________    ___   ____   ____  _        ______ ')
        stdscr.addstr(2, 1, '|_   __ \|_   __ \   .\'   `. |  _   _  | .\'   `.|_  _| |_  _|/ \     .\' ___  |')
        stdscr.addstr(3, 1, '  | |__) | | |__) | /  .-.  \|_/ | | \_|/  .-.  \ \ \   / / / _ \   / .\'   \_|')
        stdscr.addstr(4, 1, '  |  ___/  |  __ /  | |   | |    | |    | |   | |  \ \ / / / ___ \  | |       ')
        stdscr.addstr(5, 1, ' _| |_    _| |  \ \_\  `-\'  /   _| |_   \  `-\'  /   \ \' /_/ /   \ \_\ `.___.\'\\')
        stdscr.addstr(6, 1, '|_____|  |____| |___|`.___.\'   |_____|   `.___.\'     \_/|____| |____|`.____ .\'')

        stdscr.addstr(9, 4, '[T] Stats')
        stdscr.addstr(11, 4, '[S] Sign')
        stdscr.addstr(13, 4, '[C] Classes')
        if wa_api_key:
            stdscr.addstr(15, 4, '[K] Think')
        stdscr.addstr(17, 4, '[A] About')

        stdscr.addstr(23, 1, '             Copyright (c) 1985 Bikeshed Computer Systems Corp.')
        stdscr.clrtoeol()
        stdscr.refresh()
    elif current_screen == 'debug':
        stdscr.addstr(0, 1, 'PROTOVAC')
        stdscr.addstr(2, 1, 'Debug Mode')
        stdscr.addstr(3, 1, '==========')
        stdscr.addstr(5, 1, str.format('Character pressed = {0}', c))
        stdscr.clrtoeol()

        stdscr.addstr(23, 1, '[B] Back')
        stdscr.clrtoeol()
        stdscr.refresh()
    elif current_screen == 'stats':
        stdscr.addstr(0, 1, 'PROTOVAC')
        stdscr.addstr(2, 1, 'Protospace Stats')
        stdscr.addstr(3, 1, '================')
        if stats:
            stdscr.addstr(5 , 1, 'Next meeting: {}'.format(format_date(stats['next_meeting'])))
            stdscr.addstr(7 , 1, 'Next clean:   {}'.format(format_date(stats['next_clean'])))
            stdscr.addstr(9, 1, 'Next class:   {}'.format(stats['next_class']['name']))
            stdscr.addstr(10, 1, '              {}'.format(format_date(stats['next_class']['datetime'])))
            stdscr.addstr(12, 1, 'Last class:   {}'.format(stats['prev_class']['name']))
            stdscr.addstr(13, 1, '              {}'.format(format_date(stats['prev_class']['datetime'])))

            stdscr.addstr(15, 1, 'Member count: {}   Green: {}   Paused / expired: {}'.format(
                stats['member_count'],
                stats['green_count'],
                stats['paused_count'],
            ))
            stdscr.addstr(17, 1, 'Card scans:   {}'.format(stats['card_scans']))
        else:
            stdscr.addstr(5, 1, 'Loading...')

        stdscr.addstr(23, 1, '[B] Back')
        stdscr.clrtoeol()
        stdscr.refresh()

        if not stats:
            stats = fetch_stats()
            stdscr.erase()
            skip_input = True
    elif current_screen == 'classes':
        stdscr.addstr(0, 1, 'PROTOVAC')
        stdscr.addstr(2, 1, 'Protospace Classes')
        stdscr.addstr(3, 1, '==================')
        if classes:
            classes_in_view = classes['results'][classes_start:6+classes_start]
            lines = []
            for session in classes_in_view:
                lines.append(session['course_data']['name'])
                lines.append('{}  Instructor: {}  Cost: {}  Students: {}'.format(
                    format_date(session['datetime']),
                    'Protospace' if session['course_data']['id'] in [413, 317, 273] else session['instructor_name'],
                    'Free' if session['cost'] == '0.00' else '$' + session['cost'],
                    str(session['student_count']) + (' / ' + str(session['max_students']) if session['max_students'] else ''),
                ))
                lines.append('')

            offset = 5
            for num, line in enumerate(lines):
                stdscr.addstr(num + offset, 1, line)
        else:
            stdscr.addstr(5, 1, 'Loading...')

        stdscr.addstr(23, 1, '[B] Back  [J] Down  [K] Up')
        stdscr.clrtoeol()
        stdscr.refresh()

        if not classes:
            classes = fetch_classes()
            stdscr.erase()
            skip_input = True
    elif current_screen == 'sign':
        stdscr.addstr(0, 1, 'PROTOVAC')
        stdscr.addstr(2, 1, 'Protospace Sign')
        stdscr.addstr(3, 1, '===============')
        stdscr.addstr(5, 1, 'Send a message to the sign in the welcome room and classroom.')
        stdscr.addstr(6, 1, 'After sending, turn your head right and wait.')

        if sign_to_send:
            stdscr.addstr(8, 4, sign_to_send)
            stdscr.clrtoeol()
            stdscr.addstr(23, 1, '[ENTER] Send  [ESC] Cancel')
        else:
            stdscr.addstr(8, 4, '[E] Edit message')
            stdscr.addstr(23, 1, '[B] Back')

        stdscr.clrtoeol()
        stdscr.refresh()
    elif current_screen == 'think':
        stdscr.erase()
        stdscr.addstr(0, 1, 'PROTOVAC')
        stdscr.addstr(2, 1, 'Think')
        stdscr.addstr(3, 1, '=====')
        stdscr.addstr(5, 1, 'Give Protovac something to think about.')

        if think_to_send:
            stdscr.addstr(7, 4, think_to_send)
            stdscr.clrtoeol()
            stdscr.addstr(23, 1, '[ENTER] Send  [ESC] Cancel')
        else:
            stdscr.addstr(7, 4, '[E] Edit prompt')
            stdscr.addstr(23, 1, '[B] Back')

        if think_result:
            stdscr.addstr(9, 4, think_result)

        if not think_result and not think_to_send:
            stdscr.addstr(9, 1, 'Examples:')
            stdscr.addstr(11, 4, '42 + 69')
            stdscr.addstr(12, 4, '55 kg to lbs')
            stdscr.addstr(13, 4, 'density of lead')
            stdscr.addstr(14, 4, 'if x = 4, what is 3x + 50?')
            stdscr.addstr(15, 4, 'force m=150g, a=50cm/s^2')
            stdscr.addstr(16, 4, 'boiling point of benzene at 550 torr')
            stdscr.addstr(17, 4, 'goats with highest milk yield')
            stdscr.addstr(18, 4, 'how long did the Aztec empire last?')

        stdscr.refresh()
    elif current_screen == 'about':
        stdscr.addstr(0, 1, 'PROTOVAC')
        stdscr.addstr(2, 1, 'About')
        stdscr.addstr(3, 1, '=====')
        stdscr.addstr(5, 1, 'Protovac is a universal mainframe computer accessible by terminal.')
        stdscr.addstr(7, 1, 'License')
        stdscr.addstr(8, 1, '-------')
        stdscr.addstr(10, 1, 'This program is free and open-source software licensed under the MIT License.')
        stdscr.addstr(11, 1, 'Please see the LICENSE file for details. This means you have the right to')
        stdscr.addstr(12, 1, 'study, change, and distribute the software and source code to anyone and for')
        stdscr.addstr(13, 1, 'any purpose.')
        stdscr.addstr(15, 1, 'Source code: github.com/Protospace/protovac')
        stdscr.addstr(17, 1, 'Acknowledgements')
        stdscr.addstr(18, 1, '----------------')
        stdscr.addstr(20, 1, 'Thanks to Peter for lending the Morrow MTD-60 terminal and Jamie for the Pi.')

        stdscr.addstr(23, 1, '[B] Back')

    stdscr.move(23, 79)

    if skip_input:
        skip_input = False
    else:
        try:
            c = stdscr.getch()
        except KeyboardInterrupt:
            break

    if c == curses.KEY_UP:
        pass
    elif c == curses.KEY_DOWN:
        pass
    elif c == 10:   # ENTER is pressed
        pass

    button = chr(c).lower()

    if current_screen == 'home':
        if button == 't':
            current_screen = 'stats'
        elif button == 's':
            current_screen = 'sign'
        elif button == 'c':
            current_screen = 'classes'
        elif button == 'k' and wa_api_key:
            current_screen = 'think'
        elif button == 'd':
            current_screen = 'debug'
        elif button == 'a':
            current_screen = 'about'
    elif current_screen == 'debug':
        if button == 'b':
            current_screen = 'home'
    elif current_screen == 'stats':
        if button == 'b':
            current_screen = 'home'
            stats = {}
    elif current_screen == 'about':
        if button == 'b':
            current_screen = 'home'
    elif current_screen == 'classes':
        if button == 'b':
            current_screen = 'home'
            classes = {}
            classes_start = 0
        elif button == 'j':
            classes_start += 1
            stdscr.erase()
        elif button == 'k':
            if classes_start > 0:
                classes_start -= 1
                stdscr.erase()
    elif current_screen == 'sign':
        if sign_to_send:
            if c == BACKSPACE_KEY:
                sign_to_send = sign_to_send[:-2] + '_'
            elif c == ESCAPE_KEY:
                sign_to_send = ''
                stdscr.erase()
            elif c == ENTER_KEY:
                if len(sign_to_send) > 1:
                    stdscr.addstr(15, 4, 'Sending...')
                    stdscr.refresh()
                    sign_send(sign_to_send[:-1])
                    stdscr.erase()
                    sign_to_send = ''
            else:
                if c < 127 and c > 31:
                    sign_to_send = sign_to_send[:-1] + chr(c) + '_'
        elif button == 'b':
            current_screen = 'home'
        elif button == 'e':
            sign_to_send = '_'
    elif current_screen == 'think':
        if think_to_send:
            if c == BACKSPACE_KEY:
                think_to_send = think_to_send[:-2] + '_'
            elif c == ESCAPE_KEY:
                think_to_send = ''
                stdscr.erase()
            elif c == ENTER_KEY:
                if len(think_to_send) > 1:
                    stdscr.addstr(9, 4, 'Thinking...')
                    stdscr.clrtoeol()
                    stdscr.refresh()
                    think_result = think_send(think_to_send[:-1])
                    stdscr.erase()
                    think_to_send = ''
            else:
                if c < 127 and c > 31:
                    think_to_send = think_to_send[:-1] + chr(c) + '_'
        elif button == 'b':
            current_screen = 'home'
            think_result = ''
        elif button == 'e':
            think_to_send = '_'

    if current_screen != prev_screen:
        prev_screen = current_screen
        stdscr.erase()


curses.nocbreak()
stdscr.keypad(False)
curses.echo()
curses.endwin()
