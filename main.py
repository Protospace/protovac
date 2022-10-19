#!/home/pi/protovac/env/bin/python

import os, logging
DEBUG = os.environ.get('DEBUG')
logging.basicConfig(
    filename='protovax.log',
    format='[%(asctime)s] %(levelname)s %(module)s/%(funcName)s - %(message)s',
    level=logging.DEBUG if DEBUG else logging.INFO)

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

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
import random
from PIL import Image, ImageEnhance, ImageFont, ImageDraw
from datetime import datetime, timezone, timedelta

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
        return r.json()['results']
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

QUOTES = [
    'THEY MADE ME WEAR THIS',
    'ASK ME ABOUT TOAST',
    'ASK ME ABOUT BIKESHEDDING',
    'ASK ME ABOUT VETTING',
    'ASK ME ABOUT MAGNETS',
    'ASK ME ABOUT SPACE',
    'ASK ME ABOUT COUNTING',
    'EXPERT WITNESS',
    'AS SEEN ON TV',
    'CONTAINS MEAT',
    'PROTOCOIN ECONOMIST',
    'EXPERT ON ALIENS',
    'EXPERT ON WARP DRIVES',
    'CHIEF OF STARFLEET OPERATIONS',
    'ALIEN DOCTOR',
    'NASA ASTROLOGIST',
    'PINBALL WIZARD',
    'JEDI KNIGHT',
    'GHOSTBUSTER',
    'DOUBLE AGENT',
    'POKEMON TRAINER',
    'POKEMON GYM LEADER',
    'ASSISTANT TO THE REGIONAL MANAGER',
    'BOUNTY HUNTER',
    'I\'M NOT A DOCTOR',
    'SPACE PIRATE',
    'BATTERIES NOT INCLUDED',
    'QUANTUM MECHANIC',
    'PROTO SPACEX PILOT',
    'EARTHBENDER',
    'AIRBENDER',
    'WATERBENDER',
    'FIREBENDER',
    '01001000 01101001',
    'CURRENT EBAY BID: $8.51',
    'MADE YOU LOOK!',
    '(OR SIMILAR PRODUCT)',
    'BATTERY MAY EXPLODE OR LEAK',
    'CONNECT GROUND WIRE TO AVOID SHOCK',
    'COOK THROROUGHLY',
    'CURRENT AT TIME OF PRINTING',
    'DO NOT BLEACH',
    'DO NOT LEAVE UNATTENDED',
    'DO NOT REMOVE TAG UNDER PENALTY OF FEDERAL LAW',
    'DROP IN ANY MAILBOX',
    'EDITED FOR TELEVISION',
    'FOR A LIMITED TIME ONLY',
    'FOR INDOOR OR OUTDOOR USE ONLY',
    'KEEP AWAY FROM FIRE OR FLAMES',
    'KEEP AWAY FROM SUNLIGHT',
    'MADE FROM 100% RECYCLED ELECTRONS',
    'LIFEGUARD ON DUTY',
    'NOT DISHWASHER SAFE',
    'NOT TO BE COMBINED WITH OTHER RADIOISOTOPES',
    'NOT TO BE USED AS A PERSONAL FLOTATION DEVICE',
    'PEEL FROM PAPER BACKING BEFORE EATING',
    'STORE IN A COOL, DRY PLACE',
    'VOID WHERE PROHIBITED',
]
random.shuffle(QUOTES)

quote_count = 0
assigned_quotes = {}

def print_nametag(name, guest=False):
    global quote_count
    quote = ''

    if guest:
        quote_size = 120
        quote = 'GUEST'
        logging.info('Printing guest nametag for: %s', name)
    else:
        quote_size = 80
        name_lookup = name.lower()[:4]
        if name_lookup in assigned_quotes:
            quote = assigned_quotes[name_lookup]
        else:
            quote = QUOTES[quote_count % len(QUOTES)]
            quote_count += 1
            assigned_quotes[name_lookup] = quote
        logging.info('Printing member nametag for: %s, quote: %s', name, quote)

    name_size = 305

    im = Image.open(location + '/label.png')
    width, height = im.size
    draw = ImageDraw.Draw(im)

    w = 9999
    while w > 1084:
        name_size -= 5
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', name_size)
        w, h = draw.textsize(name, font=font)

    x, y = (width - w) / 2, ((height - h) / 2) - 20
    draw.text((x, y), name, font=font, fill='black')

    w = 9999
    while w > 1200:
        quote_size -= 5
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', quote_size)
        w, h = draw.textsize(quote, font=font)

    x, y = (width - w) / 2, height - h - 30
    draw.text((x, y), quote, font=font, fill='black')

    im.save('tmp.png')
    os.system('lp -d dymo tmp.png > /dev/null 2>&1')


def print_tool_label(wiki_num):
    im = Image.open(location + '/blank.png')
    w1, h1 = im.size

    logging.info('Printing tool label for ID: %s', wiki_num)

    draw = ImageDraw.Draw(im)

    params = {'id': str(wiki_num), 'size': '4'}
    res = requests.get('https://labels.protospace.ca/', stream=True, params=params, timeout=5)
    res.raise_for_status()

    label = Image.open(res.raw)

    new_size = (1280, 640)
    label = label.resize(new_size, Image.ANTIALIAS)

    w2, h2 = label.size

    x, y = int((w1 - w2) / 2), int((h1 - h2) / 2)

    im.paste(label, (x, y))

    im.save('tmp.png')
    os.system('lp -d dymo tmp.png > /dev/null 2>&1')


def print_sheet_label(name, contact):
    def get_date():
        d = datetime.now(tz=timezone.utc)
        d = d.astimezone(TIMEZONE_CALGARY)
        return d.strftime('%b %-d, %Y')

    def get_expiry_date():
        d = datetime.now(tz=timezone.utc) + timedelta(days=90)
        d = d.astimezone(TIMEZONE_CALGARY)
        return d.strftime('%b %-d, %Y')

    name_size = 85
    contact_size = 65
    date_size = 65

    im = Image.open(location + '/label.png')

    draw = ImageDraw.Draw(im)

    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', name_size)
    draw.text((20, 300), name, font=font, fill='black')

    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', contact_size)
    draw.text((20, 425), contact, font=font, fill='black')

    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', date_size)
    date_line = 'Printed: ' + get_date()
    draw.text((20, 590), date_line, font=font, fill='black')
    date_line = 'EXPIRES: ' + get_expiry_date()
    draw.text((20, 680), date_line, font=font, fill='black')

    im.save('tmp.png')
    os.system('lp -d dymo tmp.png > /dev/null 2>&1')


def message_protovac(message):
    try:
        logging.info('Message to Protovac: %s', message)

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
            timeout=30,
        )
        r.raise_for_status()
        reply = json.loads(r.text.split('\n')[-2])['replies'][0]['text'].replace('\n\n', ' ')

        logging.info('Message reply: %s', reply)

        return reply
    except BaseException as e:
        logging.exception(e)
        return 'THERE HAS BEEN AN ERROR IN MY PROCESSING ROUTINE. CAN YOU REPHRASE?'

def print_messages(messages):
    try:
        with open('/dev/usb/lp0', 'w') as f:
            for m in messages:
                f.write('  ' + m + '\n')
            f.write('\n')
    except BaseException as e:
        logging.exception(e)

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
nametag_member = ''
nametag_guest = ''
label_tool = ''
label_material_name = ''
label_material_contact = ''

logging.info('Starting main loop...')


last_key = time.time()
def ratelimit_key():
    global last_key

    if think_to_send or sign_to_send or message_to_send or nametag_member or nametag_guest or label_tool or label_material_name or label_material_contact or time.time() > last_key + 1:
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
        menupos = 2
        stdscr.addstr(7, menupos+4, '[I]', curses.A_REVERSE if highlight_keys else 0)
        stdscr.addstr(7, menupos+8, 'Info')
        stdscr.addstr(7, menupos+4+15, '[N]', curses.A_REVERSE if highlight_keys else 0)
        stdscr.addstr(7, menupos+8+15, 'Nametag')
        stdscr.addstr(9, menupos+4, '[S]', curses.A_REVERSE if highlight_keys else 0)
        stdscr.addstr(9, menupos+8, 'Stats')
        stdscr.addstr(9, menupos+4+15, '[L]', curses.A_REVERSE if highlight_keys else 0)
        stdscr.addstr(9, menupos+8+15, 'Label')
        stdscr.addstr(11, menupos+4, '[G]', curses.A_REVERSE if highlight_keys else 0)
        stdscr.addstr(11, menupos+8, 'Sign')
        stdscr.addstr(13, menupos+4, '[C]', curses.A_REVERSE if highlight_keys else 0)
        stdscr.addstr(13, menupos+8, 'Classes')
        stdscr.addstr(15, menupos+4, '[P]', curses.A_REVERSE if highlight_keys else 0)
        stdscr.addstr(15, menupos+8, 'Protocoin')
        if character_ai_token:
            stdscr.addstr(17, menupos+4, '[M]', curses.A_REVERSE if highlight_keys else 0)
            stdscr.addstr(17, menupos+8, 'Message')
            stdscr.addstr(17, 1, 'NEW')
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
            classes_sorted = sorted(classes, key=lambda x: x['datetime'])
            classes_in_view = classes_sorted[classes_start:6+classes_start]
            lines = []

            for session in classes_in_view:
                past = datetime.now(tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ') > session['datetime']
                lines.append(('[PAST] ' if past else '') + session['course_data']['name'])
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

    elif current_screen == 'nametag':
        stdscr.addstr(0, 1, 'PROTOVAC UNIVERSAL COMPUTER')
        stdscr.addstr(2, 1, 'Print a Nametag')
        stdscr.addstr(3, 1, '===============')
        stdscr.addstr(5, 1, 'Choose between member or guest.')

        if nametag_member:
            stdscr.addstr(8, 4, 'Enter your name: ' + nametag_member)
            stdscr.clrtoeol()
            stdscr.addstr(10, 4, '')
            stdscr.clrtoeol()
            stdscr.addstr(23, 1, '[RETURN] Print  [ESC] Cancel')
        elif nametag_guest:
            stdscr.addstr(8, 4, '')
            stdscr.clrtoeol()
            stdscr.addstr(10, 4, 'Enter your name: ' + nametag_guest)
            stdscr.clrtoeol()
            stdscr.addstr(23, 1, '[RETURN] Print  [ESC] Cancel')
        else:
            stdscr.addstr(8, 4, '[M] Member nametag', curses.A_REVERSE if highlight_keys else 0)
            stdscr.addstr(10, 4, '[G] Guest nametag', curses.A_REVERSE if highlight_keys else 0)
            stdscr.addstr(23, 1, '[B] Back', curses.A_REVERSE if highlight_keys else 0)

        stdscr.clrtoeol()
        stdscr.refresh()

    elif current_screen == 'label':
        stdscr.addstr(0, 1, 'PROTOVAC UNIVERSAL COMPUTER')
        stdscr.addstr(2, 1, 'Print a Label')
        stdscr.addstr(3, 1, '===============')
        stdscr.addstr(5, 1, 'Choose the type of label.')

        if label_tool:
            stdscr.addstr(8, 4, 'Enter Wiki-ID tool number: ' + label_tool)
            stdscr.clrtoeol()
            stdscr.addstr(10, 4, '')
            stdscr.clrtoeol()
            stdscr.addstr(23, 1, '[RETURN] Print  [ESC] Cancel')
        elif label_material_contact:
            stdscr.addstr(8, 4, '')
            stdscr.clrtoeol()
            stdscr.addstr(10, 4, 'Enter your contact info: ' + label_material_contact)
            stdscr.clrtoeol()
            stdscr.addstr(23, 1, '[RETURN] Next  [ESC] Cancel')
        elif label_material_name:
            stdscr.addstr(8, 4, '')
            stdscr.clrtoeol()
            stdscr.addstr(10, 4, 'Enter your name: ' + label_material_name)
            stdscr.clrtoeol()
            stdscr.addstr(23, 1, '[RETURN] Next  [ESC] Cancel')
        else:
            stdscr.addstr(8, 4, '[T] Tool label', curses.A_REVERSE if highlight_keys else 0)
            stdscr.addstr(10, 4, '[S] Sheet material', curses.A_REVERSE if highlight_keys else 0)
            stdscr.addstr(23, 1, '[B] Back', curses.A_REVERSE if highlight_keys else 0)

        stdscr.clrtoeol()
        stdscr.refresh()

    elif current_screen == 'message':
        stdscr.addstr(0, 1, 'PROTOVAC UNIVERSAL COMPUTER')
        stdscr.addstr(2, 1, 'Talk to Protovac')
        stdscr.addstr(3, 1, '================')
        stdscr.addstr(5, 1, 'Send a message to Protovac, who is flying through space.')

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
        elif button == 'n':
            current_screen = 'nametag'
        elif button == 'l':
            current_screen = 'label'
        elif button == '0':
            current_screen = 'asimov'
        elif button == 'g':
            current_screen = 'sign'
        elif button == 'c':
            current_screen = 'classes'
        elif button == 'm':
            current_screen = 'message'
            messages = ['']*15
        elif button == 't' and wa_api_key:
            current_screen = 'think'
        elif c == 68:
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
        if c == 88:
            break
        if c == 83:
            curses.nocbreak()
            stdscr.keypad(False)
            curses.echo()
            curses.endwin()
            logging.info('Spawning shell.')
            os.system('/bin/bash')
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
            if classes_start+6 < len(classes):
                classes_start += 6
                stdscr.erase()
        elif button == 'k' or c == curses.KEY_UP:
            if classes_start > 0:
                classes_start -= 6
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

    elif current_screen == 'nametag':
        if nametag_member:
            if c == curses.KEY_BACKSPACE:
                nametag_member = nametag_member[:-2] + '_'
            elif c == KEY_ESCAPE:
                nametag_member = ''
                stdscr.erase()
            elif c == KEY_ENTER:
                if len(nametag_member) > 1:
                    stdscr.addstr(15, 4, 'Printing...')
                    stdscr.refresh()
                    print_nametag(nametag_member[:-1], guest=False)
                    stdscr.erase()
                    nametag_member = ''
                    current_screen = 'home'
            else:
                if c < 127 and c > 31:
                    nametag_member = nametag_member[:-1] + chr(c) + '_'
        elif nametag_guest:
            if c == curses.KEY_BACKSPACE:
                nametag_guest = nametag_guest[:-2] + '_'
            elif c == KEY_ESCAPE:
                nametag_guest = ''
                stdscr.erase()
            elif c == KEY_ENTER:
                if len(nametag_guest) > 1:
                    stdscr.addstr(15, 4, 'Printing...')
                    stdscr.refresh()
                    print_nametag(nametag_guest[:-1], guest=True)
                    stdscr.erase()
                    nametag_guest = ''
                    current_screen = 'home'
            else:
                if c < 127 and c > 31:
                    nametag_guest = nametag_guest[:-1] + chr(c) + '_'
        elif button == 'b' or c == KEY_ESCAPE:
            current_screen = 'home'
        elif button == 'm':
            nametag_member = '_'
        elif button == 'g':
            nametag_guest = '_'
        else:
            try_highlight()

    elif current_screen == 'label':
        if label_tool:
            if c == curses.KEY_BACKSPACE:
                label_tool = label_tool[:-2] + '_'
            elif c == KEY_ESCAPE:
                label_tool = ''
                stdscr.erase()
            elif c == KEY_ENTER:
                if len(label_tool) > 1:
                    stdscr.addstr(15, 4, 'Printing...')
                    stdscr.refresh()
                    try:
                        print_tool_label(label_tool[:-1])
                    except BaseException as e:
                        logging.exception(e)
                        stdscr.addstr(15, 4, 'Error.')
                        stdscr.clrtoeol()
                        stdscr.refresh()
                        time.sleep(2)
                    stdscr.erase()
                    label_tool = ''
            else:
                if c <= 57 and c >= 48:
                    label_tool = label_tool[:-1] + chr(c) + '_'
        elif label_material_contact:
            if c == curses.KEY_BACKSPACE:
                label_material_contact = label_material_contact[:-2] + '_'
            elif c == KEY_ESCAPE:
                label_material_contact = ''
                stdscr.erase()
            elif c == KEY_ENTER:
                if len(label_material_contact) > 1:
                    stdscr.addstr(15, 4, 'Printing...')
                    stdscr.refresh()
                    print_sheet_label(label_material_name[:-1], label_material_contact[:-1])
                    stdscr.erase()
                    label_material_name = ''
                    label_material_contact = ''
            else:
                if c < 127 and c > 31:
                    label_material_contact = label_material_contact[:-1] + chr(c) + '_'
        elif label_material_name:
            if c == curses.KEY_BACKSPACE:
                label_material_name = label_material_name[:-2] + '_'
            elif c == KEY_ESCAPE:
                label_material_name = ''
                stdscr.erase()
            elif c == KEY_ENTER:
                if len(label_material_name) > 1:
                    label_material_contact = '_'
            else:
                if c < 127 and c > 31:
                    label_material_name = label_material_name[:-1] + chr(c) + '_'
        elif button == 'b' or c == KEY_ESCAPE:
            current_screen = 'home'
        elif button == 't':
            label_tool = '_'
        elif button == 's':
            label_material_name = '_'
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
                    print_messages(lines)
                    messages.append('')
                    messages.extend(lines)

                    reply = message_protovac(message_to_send)

                    lines = textwrap.wrap(
                        reply,
                        width=60,
                    )
                    print_messages(lines)
                    messages.append('')
                    messages.extend(lines)

                    stdscr.erase()
                    message_to_send = '_'
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
