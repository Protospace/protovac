#!/home/tanner/protovac/env/bin/python

import os, logging
DEBUG = os.environ.get('DEBUG')
logging.basicConfig(
    filename='protovax.log',
    format='[%(asctime)s] %(levelname)s %(module)s/%(funcName)s - %(message)s',
    level=logging.DEBUG if DEBUG else logging.INFO)

logging.info('')
logging.info('Boot up')

os.system('stty -ixon')

import curses
import requests
import pytz
import re
import os
import time
import json
import textwrap
from datetime import datetime

try:
    import secrets
    wa_api_key = secrets.wa_api_key
except:
    wa_api_key = None

try:
    import secrets
    character_ai_token = secrets.character_ai_token
except:
    character_ai_token = None

KEY_ESCAPE = 27
KEY_ENTER = 10
KEY_SPACE = 32

TIMEZONE_CALGARY = pytz.timezone('America/Edmonton')

location = os.path.dirname(os.path.realpath(__file__))

with open(location + '/info.txt') as f:
    PROTO_INFO = f.read()

for num, line in enumerate(PROTO_INFO.split('\n')):
    try:
        line.encode('ascii')
    except UnicodeEncodeError:
        print('non-ascii found in line:', num+1)
        raise

with open(location + '/lastquestion.txt') as f:
    LAST_QUESTION = f.read()


def format_date(datestr):
    if not datestr: return 'None'

    d = datetime.strptime(datestr, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.UTC)
    d = d.astimezone(TIMEZONE_CALGARY)
    return d.strftime('%a %b %-d, %Y  %-I:%M %p')

def sign_send(to_send):
    try:
        logging.info('Sending to sign: %s', to_send)
        data = dict(sign=to_send, on_behalf_of='protovac')
        r = requests.post('https://api.my.protospace.ca/stats/sign/', data=data, timeout=5)
        r.raise_for_status()
        return 'Success!'
    except BaseException as e:
        logging.exception(e)
        return 'Error'

def fetch_stats():
    try:
        logging.info('Fetching status...')
        r = requests.get('https://api.my.protospace.ca/stats/', timeout=5)
        r.raise_for_status()
        return r.json()
    except BaseException as e:
        logging.exception(e)
        return 'Error'

def fetch_classes():
    try:
        logging.info('Fetching classes...')
        r = requests.get('https://api.my.protospace.ca/sessions/', timeout=5)
        r.raise_for_status()
        return r.json()
    except BaseException as e:
        logging.exception(e)
        return 'Error'

def fetch_protocoin():
    try:
        logging.info('Fetching protocoin...')
        r = requests.get('https://api.my.protospace.ca/protocoin/transactions/', timeout=5)
        r.raise_for_status()
        return r.json()
    except BaseException as e:
        logging.exception(e)
        return 'Error'

def message_protovac(message):
    try:
        logging.info('Sending to Protovac: %s', message)

        cookies = secrets.character_ai_cookies

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://beta.character.ai/chat?char=u77cm99PcKBRaczQcJEKLqD99JrT0wxK-RAOKHgFEYo',
            'Authorization': 'Token ' + character_ai_token,
            'Origin': 'https://beta.character.ai',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }

        json_data = {
            'history_external_id': 'Mfdn894zdyDsWvQ3XVZurjW_CPE5SNmEsjPTUNR_nC8',
            'character_external_id': 'u77cm99PcKBRaczQcJEKLqD99JrT0wxK-RAOKHgFEYo',
            'text': message,
            'tgt': 'internal_id:61666:c5e98052-6704-4725-838a-7432ab01fa5b',
            'ranking_method': 'random',
            'faux_chat': False,
            'staging': False,
            'model_server_address': None,
            'override_prefix': None,
            'override_rank': None,
            'rank_candidates': None,
            'filter_candidates': None,
            'enable_tti': None,
            'initial_timeout': None,
            'insert_beginning': None,
            'translate_candidates': None,
            'stream_every_n_steps': 16,
            'chunks_to_pad': 1,
            'is_proactive': False,
        }

        r = requests.post(
            'https://beta.character.ai/chat/streaming/',
            cookies=cookies,
            headers=headers,
            json=json_data,
            timeout=20,
        )
        r.raise_for_status()
        return json.loads(r.text.split('\n')[-2])['replies'][0]['text']
    except BaseException as e:
        logging.exception(e)
        return 'Error'


if wa_api_key:
    import wolframalpha
    wa_client = wolframalpha.Client(wa_api_key)

def think_send(query):
    result = ''
    try:
        res = wa_client.query(query, timeout=10)
    except BaseException as e:
        logging.error('Error hitting W|A API: {} - {}\n'.format(e.__class__.__name__, e))
        return 'Network error'

    if 'didyoumeans' in res:
        try:
            guess = res['didyoumeans']['didyoumean']['#text']
        except TypeError:
            guess = res['didyoumeans']['didyoumean'][0]['#text']
        next_result = think_send(guess)
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
                    plaintext += '\n' + think_send(plaintext + '.0')
                if 'base' in query.lower() and '_' in plaintext:
                    plaintext = '(Base conversion) "' + plaintext + '"'
                if '(irreducible)' in plaintext and '/' in plaintext:
                    result = think_send(query + '.0')
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
    elif len(result) == 0:
        result = 'Error'

    result = result.replace('Wolfram|Alpha', 'Protovac')
    result = result.replace('Stephen Wolfram', 'Tanner') # lol
    result = result.replace('and his team', '')

    for word in ['according to', 'asked', 'although', 'approximately']:
        idx = result.lower().find('('+word)
        if idx > 0:
            result = result[:idx-1]

    if result == 'Error':
        result = 'INSUFFICIENT DATA FOR A MEANINGFUL ANSWER.'

    return result

skip_input = False
current_screen = 'home'
prev_screen = current_screen

stdscr = curses.initscr()
curses.noecho()
curses.cbreak()
stdscr.keypad(True)
curses.curs_set(0)

highlight_keys = False
highlight_debounce = time.time()
sign_to_send = ''
messages = ['']*15
message_to_send = ''
think_to_send = ''
think_result = ''
stats = {}
classes = {}
classes_start = 0
protocoin = {}
protocoin_line = 0
text_line = 0

logging.info('Starting main loop...')


last_key = time.time()
def ratelimit_key():
    global last_key

    if think_to_send or sign_to_send or message_to_send or time.time() > last_key + 1:
        last_key = time.time()
        return False
    else:
        return True


while True:
    if current_screen != 'debug':
        c = 0

    if current_screen == 'home':
        stdscr.addstr(0, 1, ' _______  _______      ___    _________    ___   ____   ____  _        ______ ')
        stdscr.addstr(1, 1, '|_   __ \|_   __ \   .\'   `. |  _   _  | .\'   `.|_  _| |_  _|/ \     .\' ___  |')
        stdscr.addstr(2, 1, '  | |__) | | |__) | /  .-.  \|_/ | | \_|/  .-.  \ \ \   / / / _ \   / .\'   \_|')
        stdscr.addstr(3, 1, '  |  ___/  |  __ /  | |   | |    | |    | |   | |  \ \ / / / ___ \  | |       ')
        stdscr.addstr(4, 1, ' _| |_    _| |  \ \_\  `-\'  /   _| |_   \  `-\'  /   \ \' /_/ /   \ \_\ `.___.\'\\')
        stdscr.addstr(5, 1, '|_____|  |____| |___|`.___.\'   |_____|   `.___.\'     \_/|____| |____|`.____ .\'')
        stdscr.addstr(6, 1, '')
        stdscr.addstr(7, 1, '                                         UNIVERSAL COMPUTER')
        stdscr.addstr(8, 1, '')
        menupos = 5
        stdscr.addstr(7, menupos+4, '[I]', curses.A_REVERSE if highlight_keys else 0)
        stdscr.addstr(7, menupos+8, 'Info')
        stdscr.addstr(9, menupos+4, '[S]', curses.A_REVERSE if highlight_keys else 0)
        stdscr.addstr(9, menupos+8, 'Stats')
        stdscr.addstr(11, menupos+4, '[N]', curses.A_REVERSE if highlight_keys else 0)
        stdscr.addstr(11, menupos+8, 'Sign')
        stdscr.addstr(13, menupos+4, '[C]', curses.A_REVERSE if highlight_keys else 0)
        stdscr.addstr(13, menupos+8, 'Classes')
        stdscr.addstr(15, menupos+4, '[P]', curses.A_REVERSE if highlight_keys else 0)
        stdscr.addstr(15, menupos+8, 'Protocoin')
        if character_ai_token:
            stdscr.addstr(17, menupos+4, '[M]', curses.A_REVERSE if highlight_keys else 0)
            stdscr.addstr(17, menupos+8, 'Message')
        if wa_api_key:
            stdscr.addstr(19, menupos+4, '[T]', curses.A_REVERSE if highlight_keys else 0)
            stdscr.addstr(19, menupos+8, 'Think')
        stdscr.addstr(21, menupos+4, '[A]', curses.A_REVERSE if highlight_keys else 0)
        stdscr.addstr(21, menupos+8, 'About')
        stdscr.addstr(23, 1, '               Copyright (c) 1985 Bikeshed Computer Systems Ltd.')

        stars = (8, 34)
        stdscr.addstr(stars[0]+0 , stars[1], "                           .  *       - )-    ")
        stdscr.addstr(stars[0]+1 , stars[1], "       .      *       o       .       *       ")
        stdscr.addstr(stars[0]+2 , stars[1], "                  |                           ")
        stdscr.addstr(stars[0]+3 , stars[1], "           .     -O-                          ")
        stdscr.addstr(stars[0]+4 , stars[1], ".                 |        *      .     -0-   ")
        stdscr.addstr(stars[0]+5 , stars[1], "       *  o     .    '       *      .        o")
        stdscr.addstr(stars[0]+6 , stars[1], "              .         .        |      *     ")
        stdscr.addstr(stars[0]+7 , stars[1], "   *             *              -O-          .")
        stdscr.addstr(stars[0]+8 , stars[1], "         .             *         |     ,      ")
        stdscr.addstr(stars[0]+9 , stars[1], "                .           o                 ")
        stdscr.addstr(stars[0]+10, stars[1], "        .---.                                 ")
        stdscr.addstr(stars[0]+11, stars[1], "  =   _/__[0]\_     .  *            o       ' ")
        stdscr.addstr(stars[0]+12, stars[1], " = = (_________)             .                ")
        stdscr.addstr(stars[0]+13, stars[1], "                 .                        *   ")
        stdscr.addstr(stars[0]+14, stars[1], "       *               - ) -       *          ")


        stdscr.clrtoeol()
        stdscr.refresh()
    elif current_screen == 'debug':
        stdscr.addstr(0, 1, 'PROTOVAC UNIVERSAL COMPUTER')
        stdscr.addstr(2, 1, 'Debug Mode')
        stdscr.addstr(3, 1, '==========')
        stdscr.addstr(5, 1, str.format('Character pressed = {0}', c))
        stdscr.clrtoeol()

        stdscr.addstr(23, 1, '[B] Back', curses.A_REVERSE if highlight_keys else 0)
        stdscr.clrtoeol()
        stdscr.refresh()
    elif current_screen == 'stats':
        stdscr.addstr(0, 1, 'PROTOVAC UNIVERSAL COMPUTER')
        stdscr.addstr(2, 1, 'Protospace Stats')
        stdscr.addstr(3, 1, '================')
        if stats == 'Error':
            stdscr.addstr(5, 1, 'Error. Go back and try again.')
        elif stats:
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

        stdscr.addstr(23, 1, '[B] Back', curses.A_REVERSE if highlight_keys else 0)
        stdscr.clrtoeol()
        stdscr.refresh()

        if not stats:
            stats = fetch_stats()
            stdscr.erase()
            skip_input = True
    elif current_screen == 'classes':
        stdscr.addstr(0, 1, 'PROTOVAC UNIVERSAL COMPUTER')
        stdscr.addstr(2, 1, 'Protospace Classes')
        stdscr.addstr(3, 1, '==================              Instructor    Cost     Students')
        if classes == 'Error':
            stdscr.addstr(5, 1, 'Error. Go back and try again.')
        elif classes:
            classes_in_view = classes['results'][classes_start:6+classes_start]
            lines = []

            for session in classes_in_view:
                lines.append(session['course_data']['name'])
                lines.append('{:<30}  {:<12}  {:<7}  {:<7}'.format(
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

        stdscr.addstr(23, 1, '[B] Back  [J] Down  [K] Up', curses.A_REVERSE if highlight_keys else 0)
        stdscr.clrtoeol()
        stdscr.refresh()

        if not classes:
            classes = fetch_classes()
            stdscr.erase()
            skip_input = True
    elif current_screen == 'asimov':
        stdscr.addstr(0, 1, 'PROTOVAC UNIVERSAL COMPUTER')
        lines = LAST_QUESTION.split('\n')

        offset = 2
        for num, line in enumerate(lines[text_line:text_line+20]):
            stdscr.addstr(num + offset, 1, line)

        stdscr.addstr(23, 1, '[B] Back  [J] Down  [K] Up', curses.A_REVERSE if highlight_keys else 0)
        stdscr.addstr(23, 67, 'Page {:>2} / {:>2}'.format((text_line // 19)+1, (len(lines) // 19)+1))
        stdscr.clrtoeol()
        stdscr.refresh()
    elif current_screen == 'info':
        stdscr.addstr(0, 1, 'PROTOVAC UNIVERSAL COMPUTER')
        lines = PROTO_INFO.split('\n')

        offset = 2
        for num, line in enumerate(lines[text_line:text_line+20]):
            stdscr.addstr(num + offset, 1, line)

        stdscr.addstr(23, 1, '[B] Back  [J] Down  [K] Up', curses.A_REVERSE if highlight_keys else 0)
        stdscr.addstr(23, 67, 'Page {:>2} / {:>2}'.format((text_line // 19)+1, (len(lines) // 19)+1))
        stdscr.clrtoeol()
        stdscr.refresh()
    elif current_screen == 'protocoin':
        stdscr.addstr(0, 1, 'PROTOVAC UNIVERSAL COMPUTER')
        stdscr.addstr(2, 1, 'Protocoin')
        stdscr.addstr(3, 1, '=========')
        if protocoin == 'Error':
            stdscr.addstr(5, 1, 'Error. Go back and try again.')
        elif protocoin:
            txs = protocoin['transactions']
            lines = []

            lines.append('Protocoin is used to buy things from Protospace\'s vending machines.')
            lines.append('')
            lines.append('Total in circulation: {}'.format(protocoin['total_protocoin']))
            lines.append('')
            lines.append('Transactions:')
            lines.append('')
            lines.append('ID     Date        Method       Amount  Category')

            for tx in txs:
                lines.append('{}  {}  {:<11}  {:<6}  {:<11}'.format(
                    tx['id'],
                    tx['date'],
                    tx['account_type'],
                    tx['protocoin'],
                    'Transfer' if tx['category'] == 'Other' else tx['category'],
                ))

            offset = 5
            for num, line in enumerate(lines[protocoin_line:protocoin_line+17]):
                stdscr.addstr(num + offset, 1, line)
        else:
            stdscr.addstr(5, 1, 'Loading...')

        stdscr.addstr(23, 1, '[B] Back  [J] Down  [K] Up', curses.A_REVERSE if highlight_keys else 0)
        stdscr.clrtoeol()
        stdscr.refresh()

        if not protocoin:
            protocoin = fetch_protocoin()
            stdscr.erase()
            skip_input = True
    elif current_screen == 'sign':
        stdscr.addstr(0, 1, 'PROTOVAC UNIVERSAL COMPUTER')
        stdscr.addstr(2, 1, 'Protospace Sign')
        stdscr.addstr(3, 1, '===============')
        stdscr.addstr(5, 1, 'Send a message to the sign in the welcome room and classroom.')
        stdscr.addstr(6, 1, 'After sending, turn your head right and wait 5 seconds.')

        if sign_to_send:
            stdscr.addstr(8, 4, sign_to_send)
            stdscr.clrtoeol()
            stdscr.addstr(23, 1, '[RETURN] Send  [ESC] Cancel')
        else:
            stdscr.addstr(8, 4, '[E] Edit message', curses.A_REVERSE if highlight_keys else 0)
            stdscr.addstr(23, 1, '[B] Back', curses.A_REVERSE if highlight_keys else 0)

        stdscr.clrtoeol()
        stdscr.refresh()
    elif current_screen == 'message':
        stdscr.addstr(0, 1, 'PROTOVAC UNIVERSAL COMPUTER')
        stdscr.addstr(2, 1, 'Message Protovac')
        stdscr.addstr(3, 1, '===============')
        stdscr.addstr(5, 1, 'Send a message to Protovac, the universal computer.')

        offset = 7
        for num, line in enumerate(messages[-13:]):
            stdscr.addstr(num + offset, 1, line)

        if message_to_send:
            stdscr.addstr(21, 21, message_to_send)
            stdscr.clrtoeol()
            stdscr.addstr(23, 1, '[RETURN] Send  [ESC] Cancel')
        else:
            stdscr.addstr(21, 21, '[E] Edit message', curses.A_REVERSE if highlight_keys else 0)
            stdscr.addstr(23, 1, '[B] Back', curses.A_REVERSE if highlight_keys else 0)

        stdscr.clrtoeol()
        stdscr.refresh()
    elif current_screen == 'think':
        stdscr.erase()
        stdscr.addstr(0, 1, 'PROTOVAC UNIVERSAL COMPUTER')
        stdscr.addstr(2, 1, 'Think')
        stdscr.addstr(3, 1, '=====')
        stdscr.addstr(5, 1, 'Give Protovac something to think about.')

        if think_to_send:
            stdscr.addstr(7, 4, think_to_send)
            stdscr.clrtoeol()
            stdscr.addstr(23, 1, '[RETURN] Send  [ESC] Cancel')
        else:
            stdscr.addstr(7, 4, '[E] Edit prompt', curses.A_REVERSE if highlight_keys else 0)
            stdscr.addstr(23, 1, '[B] Back', curses.A_REVERSE if highlight_keys else 0)

        if think_result:
            for _ in range(100):
                try:
                    stdscr.addstr(9, 4, think_result)
                    break
                except:
                    think_result = think_result[:-5]
            stdscr.addstr(22, 1, '')
            stdscr.clrtoeol()
            stdscr.addstr(23, 1, '[B] Back', curses.A_REVERSE if highlight_keys else 0)
            stdscr.clrtoeol()

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
        stdscr.addstr(0, 1, 'PROTOVAC UNIVERSAL COMPUTER')
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

        stdscr.addstr(23, 1, '[B] Back', curses.A_REVERSE if highlight_keys else 0)
        stdscr.refresh()

    stdscr.move(23, 79)

    if highlight_keys:
        time.sleep(0.5)
        highlight_keys = False
        continue

    if skip_input:
        skip_input = False
    else:
        curses.flushinp()
        if ratelimit_key(): continue
        try:
            c = stdscr.getch()
        except KeyboardInterrupt:
            pass
            #break

    try:
        button = chr(c).lower()
    except:
        button = None

    def try_highlight():
        global c, highlight_debounce, highlight_keys
        if c and time.time() - highlight_debounce > 0.6:
            highlight_debounce = time.time()
            highlight_keys = True
            curses.beep()

    if current_screen == 'home':
        if button == 's':
            current_screen = 'stats'
        elif button == 'i':
            current_screen = 'info'
        elif button == '0':
            current_screen = 'asimov'
        elif button == 'n':
            current_screen = 'sign'
        elif button == 'c':
            current_screen = 'classes'
        elif button == 'm':
            current_screen = 'message'
            messages = ['']*15
        elif button == 't' and wa_api_key:
            current_screen = 'think'
        elif button == 'd':
            current_screen = 'debug'
        elif button == 'a':
            current_screen = 'about'
        elif button == 'p':
            current_screen = 'protocoin'
        else:
            try_highlight()
    elif current_screen == 'debug':
        if button == 'b' or c == KEY_ESCAPE:
            current_screen = 'home'
        if button == 'x':
            break
        else:
            try_highlight()
    elif current_screen == 'stats':
        if button == 'b' or c == KEY_ESCAPE:
            current_screen = 'home'
            stats = {}
        else:
            try_highlight()
    elif current_screen == 'about':
        if button == 'b' or c == KEY_ESCAPE:
            current_screen = 'home'
        else:
            try_highlight()
    elif current_screen == 'classes':
        if button == 'b' or c == KEY_ESCAPE:
            current_screen = 'home'
            classes = {}
            classes_start = 0
        elif button == 'j' or c == curses.KEY_DOWN or c == KEY_SPACE:
            classes_start += 1
            stdscr.erase()
        elif button == 'k' or c == curses.KEY_UP:
            if classes_start > 0:
                classes_start -= 1
                stdscr.erase()
        else:
            try_highlight()
    elif current_screen == 'asimov':
        if button == 'b' or c == KEY_ESCAPE:
            current_screen = 'home'
            protocoin = {}
            text_line = 0
        elif button == 'j' or c == curses.KEY_DOWN or c == KEY_SPACE:
            if text_line+19 < len(lines):
                text_line += 19
                stdscr.erase()
        elif button == 'k' or c == curses.KEY_UP:
            if text_line > 0:
                text_line -= 19
                stdscr.erase()
        else:
            try_highlight()
    elif current_screen == 'info':
        if button == 'b' or c == KEY_ESCAPE:
            current_screen = 'home'
            protocoin = {}
            text_line = 0
        elif button == 'j' or c == curses.KEY_DOWN or c == KEY_SPACE:
            if text_line+19 < len(lines):
                text_line += 19
                stdscr.erase()
        elif button == 'k' or c == curses.KEY_UP:
            if text_line > 0:
                text_line -= 19
                stdscr.erase()
        else:
            try_highlight()
    elif current_screen == 'protocoin':
        if button == 'b' or c == KEY_ESCAPE:
            current_screen = 'home'
            protocoin = {}
            protocoin_line = 0
        elif button == 'j' or c == curses.KEY_DOWN or c == KEY_SPACE:
            protocoin_line += 1
            stdscr.erase()
        elif button == 'k' or c == curses.KEY_UP:
            if protocoin_line > 0:
                protocoin_line -= 1
                stdscr.erase()
        else:
            try_highlight()
    elif current_screen == 'sign':
        if sign_to_send:
            if c == curses.KEY_BACKSPACE:
                sign_to_send = sign_to_send[:-2] + '_'
            elif c == KEY_ESCAPE:
                sign_to_send = ''
                stdscr.erase()
            elif c == KEY_ENTER:
                if len(sign_to_send) > 1:
                    stdscr.addstr(15, 4, 'Sending...')
                    stdscr.refresh()
                    sign_send(sign_to_send[:-1])
                    stdscr.erase()
                    sign_to_send = ''
            else:
                if c < 127 and c > 31:
                    sign_to_send = sign_to_send[:-1] + chr(c) + '_'
        elif button == 'b' or c == KEY_ESCAPE:
            current_screen = 'home'
        elif button == 'e':
            sign_to_send = '_'
        else:
            try_highlight()
    elif current_screen == 'message':
        if message_to_send:
            if c == curses.KEY_BACKSPACE:
                message_to_send = message_to_send[:-2] + '_'
            elif c == KEY_ESCAPE:
                message_to_send = ''
                stdscr.erase()
            elif c == KEY_ENTER:
                if len(message_to_send) > 1:
                    stdscr.addstr(22, 21, 'Sending...')
                    stdscr.refresh()
                    message_to_send = message_to_send[:-1]

                    lines = textwrap.wrap(
                        message_to_send,
                        width=80,
                        initial_indent=' '*20,
                        subsequent_indent=' '*20,
                    )
                    messages.append('')
                    messages.extend(lines)

                    reply = message_protovac(message_to_send)

                    lines = textwrap.wrap(
                        reply,
                        width=60,
                    )
                    messages.append('')
                    messages.extend(lines)

                    stdscr.erase()
                    message_to_send = ''
            else:
                if c < 127 and c > 31:
                    message_to_send = message_to_send[:-1] + chr(c) + '_'
        elif button == 'b' or c == KEY_ESCAPE:
            current_screen = 'home'
        elif button == 'e':
            message_to_send = '_'
        else:
            try_highlight()
    elif current_screen == 'think':
        if think_to_send:
            if c == curses.KEY_BACKSPACE:
                think_to_send = think_to_send[:-2] + '_'
            elif c == KEY_ESCAPE:
                think_to_send = ''
                stdscr.erase()
            elif c == KEY_ENTER:
                if len(think_to_send) > 1:
                    stdscr.addstr(9, 4, 'Thinking...')
                    stdscr.clrtoeol()
                    stdscr.refresh()

                    query = think_to_send[:-1]
                    logging.info('Thinking about: %s', query)
                    think_result = think_send(query)
                    logging.info('Think result: %s', think_result)

                    stdscr.erase()
                    think_to_send = ''
            else:
                if c < 127 and c > 31:
                    think_to_send = think_to_send[:-1] + chr(c) + '_'
        elif button == 'b' or c == KEY_ESCAPE:
            current_screen = 'home'
            think_result = ''
        elif button == 'e':
            think_to_send = '_'
        else:
            try_highlight()

    if current_screen != prev_screen:
        prev_screen = current_screen
        logging.info('Switching to screen: %s', current_screen)
        stdscr.erase()


curses.nocbreak()
stdscr.keypad(False)
curses.echo()
curses.endwin()
logging.info('Exiting.')
