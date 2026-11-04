# Free camera for Neopets: The Darkest Faerie (USA, SCUS-97367) running in PCSX2.
# See README.md. Controls are in controls.ini. Changes live memory only, never the disc.
import configparser
import ctypes
import math
import os
import socket
import struct
import sys
import time
from ctypes import wintypes

SERIAL = 'SCUS-97367'
GAME_OBJECT = 0x35C7B0       # +4 points to the camera record
SELECTED_HERO = 0x35C7D4     # the hero's motion record is named at +0x16C; its position is at +0x50
INPUT_ENABLE = 0x35C984      # bit 0 off: the hero ignores the pad
MODE, MODE_EMPTY, MODE_FOLLOW = 0x50, 2, 0
HERE = os.path.dirname(os.path.abspath(__file__))
CONTROLS = os.path.join(HERE, 'controls.ini')

user32 = ctypes.windll.user32
user32.GetForegroundWindow.restype = wintypes.HWND

KEYS = {c: ord(c) for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'}
KEYS.update({'F%d' % i: 0x6F + i for i in range(1, 13)})
KEYS.update({'NUM%d' % i: 0x60 + i for i in range(10)})
KEYS.update(UP=0x26, DOWN=0x28, LEFT=0x25, RIGHT=0x27, SPACE=0x20, TAB=0x09, ENTER=0x0D, BACKSPACE=0x08,
            SHIFT=0x10, CTRL=0x11, ALT=0x12, HOME=0x24, END=0x23, PAGEUP=0x21, PAGEDOWN=0x22, INSERT=0x2D,
            DELETE=0x2E, COMMA=0xBC, PERIOD=0xBE, SLASH=0xBF, SEMICOLON=0xBA, QUOTE=0xDE, MINUS=0xBD,
            EQUALS=0xBB, MOUSE_LEFT=0x01, MOUSE_RIGHT=0x02, MOUSE_MIDDLE=0x04)
BUTTONS = dict(DPAD_UP=0x0001, DPAD_DOWN=0x0002, DPAD_LEFT=0x0004, DPAD_RIGHT=0x0008, START=0x0010, BACK=0x0020,
               L3=0x0040, R3=0x0080, LB=0x0100, RB=0x0200, A=0x1000, B=0x2000, X=0x4000, Y=0x8000)
TRIGGERS = ('LT', 'RT')
ACTIONS = ('toggle', 'teleport', 'forward', 'back', 'left', 'right', 'up', 'down', 'turn_left', 'turn_right',
           'look_up', 'look_down', 'slower', 'faster')


class Stop(Exception):
    pass


def fail(message):
    raise Stop(message)


def parse(section, names, valid, where):
    """Reads 'Y, NUM8' or 'L3+R3' into a list of alternatives, each a list of inputs held together."""
    out = {}
    for name in names:
        alts = []
        for alt in section.get(name, '').split(','):
            parts = [t.strip().upper() for t in alt.split('+') if t.strip()]
            for t in parts:
                if t not in valid:
                    fail(f'{where}: "{t}" for "{name}" is not a name I know. The README lists the names.')
            if parts:
                alts.append(parts)
        out[name] = alts
    return out


def load_controls():
    if not os.path.exists(CONTROLS):
        fail(f'controls.ini is missing. It should be next to freecam.py: {CONTROLS}')
    ini = configparser.ConfigParser(inline_comment_prefixes=('#',), interpolation=None)
    try:
        ini.read(CONTROLS, encoding='utf-8')
        s = ini['settings']
        settings = dict(
            pine_slot=s.getint('pine_slot', 28011), move_speed=s.getfloat('move_speed', 0.5),
            turn_speed=s.getfloat('turn_speed', 0.03), look_speed=s.getfloat('look_speed', 0.02),
            stick_speed=s.getfloat('stick_speed', 0.04), mouse_speed=s.getfloat('mouse_speed', 0.003),
            freeze_player=s.getboolean('freeze_player', True), invert_stick_x=s.getboolean('invert_stick_x', False),
            invert_stick_y=s.getboolean('invert_stick_y', False), invert_mouse_y=s.getboolean('invert_mouse_y', False))
        keyboard = parse(ini['keyboard'], ACTIONS + ('mouse_look',), KEYS, 'controls.ini, keyboard section')
        controller = parse(ini['controller'], ACTIONS, set(BUTTONS) | set(TRIGGERS), 'controls.ini, controller section')
        sticks = {k: ini['controller'].get(k, '').strip().lower() for k in ('move_stick', 'look_stick')}
    except (configparser.Error, KeyError, ValueError) as e:
        fail(f'controls.ini has a mistake in it: {e}')
    for k, v in sticks.items():
        if v not in ('left', 'right', 'none', ''):
            fail(f'controls.ini, controller section: {k} must be left, right or none, not "{v}".')
    return settings, keyboard, controller, sticks


class Pine:
    """The small part of PCSX2's PINE protocol this needs."""

    def __init__(self, slot):
        self.s = socket.create_connection(('127.0.0.1', slot), timeout=5)
        self.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    def call(self, op, args=b''):
        self.s.sendall(struct.pack('<IB', 5 + len(args), op) + args)
        head = self.recv(5)
        size, result = struct.unpack('<IB', head)
        body = self.recv(size - 5)
        if result:
            raise ConnectionError('PCSX2 refused the request')
        return body

    def recv(self, n):
        b = b''
        while len(b) < n:
            c = self.s.recv(n - len(b))
            if not c:
                raise ConnectionError('PCSX2 closed the connection')
            b += c
        return b

    def read32(self, a):
        return struct.unpack('<I', self.call(0x02, struct.pack('<I', a)))[0]

    def write32(self, a, v):
        self.call(0x06, struct.pack('<II', a, v & 0xFFFFFFFF))

    def read_f32(self, a):
        return struct.unpack('<f', self.call(0x02, struct.pack('<I', a)))[0]

    def write_f32(self, a, v):
        self.call(0x06, struct.pack('<If', a, v))

    def game_id(self):
        return self.call(0x0C)[4:].rstrip(b'\0').decode('latin-1')


class XState(ctypes.Structure):
    _fields_ = [('packet', wintypes.DWORD), ('buttons', wintypes.WORD), ('lt', ctypes.c_ubyte), ('rt', ctypes.c_ubyte),
                ('lx', ctypes.c_short), ('ly', ctypes.c_short), ('rx', ctypes.c_short), ('ry', ctypes.c_short)]


XINPUT = None
for name in ('xinput1_4', 'xinput1_3', 'xinput9_1_0'):
    try:
        XINPUT = ctypes.WinDLL(name)
        break
    except OSError:
        pass


def pad():
    """The first connected controller's state, or None."""
    if not XINPUT:
        return None
    for i in range(4):
        s = XState()
        if XINPUT.XInputGetState(i, ctypes.byref(s)) == 0:
            return s
    return None


def axis(v, dead=7000):
    if abs(v) < dead:
        return 0.0
    return (abs(v) - dead) / (32767 - dead) * (1 if v > 0 else -1)


def key_down(k):
    return bool(user32.GetAsyncKeyState(KEYS[k]) & 0x8000)


def in_game_window():
    buf = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(user32.GetForegroundWindow(), buf, 256)
    return 'Neopets' in buf.value or 'PCSX2' in buf.value


def cursor():
    pt = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def norm(v):
    n = math.sqrt(sum(a * a for a in v)) or 1.0
    return [a / n for a in v]


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def stick(g, which):
    if not g or which not in ('left', 'right'):
        return 0.0, 0.0
    return (axis(g.lx), axis(g.ly)) if which == 'left' else (axis(g.rx), axis(g.ry))


def controller_state(g, bindings):
    """Each action's value from 0 to 1. A button used in a held combination doesn't also count alone."""
    def held(t):
        if t == 'LT':
            return g.lt > 30
        if t == 'RT':
            return g.rt > 30
        return bool(g.buttons & BUTTONS[t])
    active = [set(alt) for alts in bindings.values() for alt in alts if all(held(t) for t in alt)]
    out = {}
    for action, alts in bindings.items():
        value = 0.0
        for alt in alts:
            s = set(alt)
            if s in active and not any(s < other for other in active):
                if len(alt) == 1 and alt[0] in TRIGGERS:
                    value = max(value, (g.lt if alt[0] == 'LT' else g.rt) / 255)
                else:
                    value = 1.0
        out[action] = value
    return out


def connect(slot):
    print(f'Waiting for PCSX2 on port {slot}. Start the game, with PINE turned on (see README.md).', flush=True)
    while True:
        try:
            p = Pine(slot)
            game = p.game_id()
            if game:
                if game.replace('-', '').upper() != SERIAL.replace('-', ''):
                    fail(f'The running game is "{game}". This only works with the USA disc, {SERIAL}.')
                return p
        except OSError:
            pass
        time.sleep(1)


def run():
    cfg, keyboard, controller, sticks = load_controls()
    p = connect(cfg['pine_slot'])
    state = dict(on=False, last_mouse=None)
    speed, pos, yaw, pitch, pin = cfg['move_speed'], [0, 0, 0], 0.0, 0.0, None
    was = dict(toggle=False, teleport=False)

    def camera():
        return p.read32(GAME_OBJECT + 4)

    def motion():
        return p.read32(p.read32(SELECTED_HERO) + 0x16C)

    def hero_input(enabled):
        if cfg['freeze_player']:
            w = p.read32(INPUT_ENABLE)
            p.write32(INPUT_ENABLE, w | 1 if enabled else w & ~1)

    print('Ready. Click into the game window and turn the freecam on:', flush=True)
    print('  keyboard:', ' or '.join('+'.join(a) for a in keyboard['toggle']) or '(not set)', flush=True)
    print('  controller:', ' or '.join('+'.join(a) for a in controller['toggle']) or '(not set)',
          '' if pad() else '(no controller found yet)', flush=True)

    try:
        while True:
            time.sleep(1 / 60)
            if not in_game_window():
                state['last_mouse'] = None
                continue
            g = pad()
            pads = controller_state(g, controller) if g else {a: 0.0 for a in ACTIONS}

            def value(action):
                keys = any(all(key_down(k) for k in alt) for alt in keyboard[action])
                return max(1.0 if keys else 0.0, pads[action])

            toggle, teleport = value('toggle') > 0, value('teleport') > 0
            cam = camera()
            if toggle and not was['toggle'] and cam:
                state['on'] = not state['on']
                if state['on']:
                    pos = [p.read_f32(cam + 0x30 + 4 * i) for i in range(3)]
                    f = [p.read_f32(cam + 0x20 + 4 * i) for i in range(3)]
                    yaw, pitch = math.atan2(f[0], f[2]), math.asin(max(-1, min(1, f[1])))
                    p.write32(cam + MODE, MODE_EMPTY)
                    hero_input(False)
                    m = motion()
                    pin = [p.read_f32(m + 0x50), p.read_f32(m + 0x58)]
                else:
                    p.write32(cam + MODE, MODE_FOLLOW)
                    hero_input(True)
                print('Freecam', 'on' if state['on'] else 'off', flush=True)
            was['toggle'] = toggle
            if not state['on']:
                was['teleport'] = teleport
                continue
            if p.read32(cam + MODE) != MODE_EMPTY:      # a world load or scene took the camera back
                state['on'] = False
                hero_input(True)
                print('Freecam off: the game took the camera back.', flush=True)
                continue

            m = motion()
            if teleport and not was['teleport']:
                for i in range(3):
                    p.write_f32(m + 0x50 + 4 * i, pos[i])
                pin = [pos[0], pos[2]]
                print('Player moved to', [round(a, 1) for a in pos], flush=True)
            was['teleport'] = teleport
            if cfg['freeze_player']:
                # Hold the player in place across the ground; they can still fall.
                if p.read32(INPUT_ENABLE) & 1:
                    hero_input(False)
                p.write_f32(m + 0x50, pin[0])
                p.write_f32(m + 0x58, pin[1])

            speed = max(0.02, speed * (1 - 0.03 * value('slower')))
            speed = min(20.0, speed * (1 + 0.03 * value('faster')))
            yaw += (value('turn_left') - value('turn_right')) * cfg['turn_speed']
            pitch += (value('look_up') - value('look_down')) * cfg['look_speed']
            lx, ly = stick(g, sticks['look_stick'])
            yaw -= lx * cfg['stick_speed'] * (-1 if cfg['invert_stick_x'] else 1)
            pitch += ly * cfg['stick_speed'] * 0.75 * (-1 if cfg['invert_stick_y'] else 1)
            if any(all(key_down(k) for k in alt) for alt in keyboard['mouse_look']):
                c = cursor()
                if state['last_mouse']:
                    yaw -= (c[0] - state['last_mouse'][0]) * cfg['mouse_speed']
                    pitch -= (c[1] - state['last_mouse'][1]) * cfg['mouse_speed'] * (-1 if cfg['invert_mouse_y'] else 1)
                state['last_mouse'] = c
            else:
                state['last_mouse'] = None
            pitch = max(-1.5, min(1.5, pitch))

            f = [math.cos(pitch) * math.sin(yaw), math.sin(pitch), math.cos(pitch) * math.cos(yaw)]
            side = norm(cross([0, 1, 0], f))    # the game's first row, which points to screen left
            up = cross(f, side)
            mx, my = stick(g, sticks['move_stick'])
            mv = value('forward') - value('back') + my
            st = value('right') - value('left') + mx
            ud = value('up') - value('down')
            for i in range(3):
                pos[i] += speed * (mv * f[i] - st * side[i] + (ud if i == 1 else 0))
            for off, row in ((0x00, side), (0x10, up), (0x20, f), (0x30, pos)):
                for i in range(3):
                    p.write_f32(cam + off + 4 * i, row[i])
    except KeyboardInterrupt:
        if state['on']:
            p.write32(camera() + MODE, MODE_FOLLOW)
            hero_input(True)
        print('Stopped. The camera is back to normal.', flush=True)
    except (OSError, ConnectionError):
        print('The game closed, so the freecam stopped.', flush=True)


if __name__ == '__main__':
    try:
        run()
    except Stop as e:
        print('Problem:', e, flush=True)
        sys.exit(1)
