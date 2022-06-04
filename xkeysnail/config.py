# -*- coding: utf-8 -*-
# import {{{
from itertools import product
from functools import reduce
from subprocess import Popen
import re
from xdg import BaseDirectory
import xkeysnail.transform as T
from xkeysnail.transform import *
# }}}

# modmap {{{
define_modmap({
    Key.CAPSLOCK: Key.ESC,
    Key.ESC: Key.GRAVE,
})

define_timeout(0.3)
define_multipurpose_modmap({
    Key.ESC: [Key.ESC, Key.LEFT_CTRL],
    Key.ENTER: [Key.ENTER, Key.RIGHT_CTRL],
    Key.TAB: [Key.TAB, Key.LEFT_META],
    Key.BACKSLASH: [Key.BACKSLASH, Key.RIGHT_META],
})
# }}}

# polybar {{{
modes = ['normal', 'run', 'focus', 'win', 'move', 'resize', 'session', 'volume', 'volume-mute', 'brightness']
mode = 0
polybar_hooks = {v: k for k, v in enumerate(modes)}


def polybar(name, persist=False):
    def func():
        global mode
        if not persist:
            mode = polybar_hooks[name]
        else:
            mode = 0
        Popen(['polybar-msg', 'action', 'keys', 'hook', str(polybar_hooks[name])])
        return {}
    return func


origin_transform_key = T.transform_key


def my_transform_key(key, action, wm_class=None, quiet=False):
    global mode
    origin_transform_key(key, action, wm_class, quiet)
    if T._mode_maps is None and mode != 0:
        Popen(['polybar-msg', 'action', 'keys', 'hook', '0'])


T.transform_key = my_transform_key
# }}}

# repeat {{{


def repeat(mod, keymap):
    new_keymap = keymap.copy()
    for key, orig_command in keymap.items():
        if callable(orig_command):
            def func(orig_command=orig_command):
                orig_command()
                return {}
            command = func
        else:
            command = orig_command
        if not isinstance(command, list):
            command = [command]
        else:
            command = command[:]
        command.append(new_keymap)
        for mod_key in [key.with_modifier(mod.to_left()), key.with_modifier(mod.to_right())]:
            if mod_key in new_keymap:
                continue
            new_keymap[mod_key] = command
    return new_keymap
# }}}

# left_right {{{


def left_right(keymap):
    new_keymap = {}
    for key, command in keymap.items():
        for mods in product(*[[m.to_left(), m.to_right()] for m in key.modifiers]):
            mod_key = Combo(set(mods), key.key)
            if mod_key in new_keymap:
                continue
            new_keymap[mod_key] = command
    return new_keymap
# }}}

# modifiable {{{


def modifiable(mods, keymap):
    new_keymap = keymap.copy()
    for key, command in keymap.items():
        assert isinstance(command, Combo)
        for mod in product(*[[None, mod] for mod in mods]):
            mod = [m for m in mod if m]
            mod_key = reduce(lambda k, m: k.with_modifier(m), mod, key)
            if mod_key in new_keymap:
                continue
            new_keymap[mod_key] = reduce(
                lambda k, m: k.with_modifier(m), mod, command)
    return new_keymap
# }}}

# launch {{{


def launch(command, reset_mode=True):
    def func():
        Popen(command, start_new_session=True)
        if not reset_mode:
            return {}
    return func
# }}}


# keymap {{{
# run mode {{{
run_mode = [polybar('run'), repeat(Modifier.SUPER, {
    # TODO: email, proxy, window manager reload
    K('t'): launch(['exo-open', '--launch', 'TerminalEmulator']),
    K('w'): launch(['exo-open', '--launch', 'WebBrowser']),
    K('e'): launch(['exo-open', '--launch', 'FileManager']),
    K('n'): launch(['mousepad', '-o', 'window']),
    K('r'): launch(['rofi', '-show', 'combi']),
})]
# }}}

# workspaces {{{
with open(BaseDirectory.load_first_config('i3/config')) as f:
    workspaces = re.findall(r'^set \$ws(\d+) "([^"]+)"$', f.read(), re.M)
    workspaces = [(int(k) % 10, v) for k, v in workspaces]
# }}}

define_keymap(None, {
    # special keys {{{
    **modifiable([Modifier.ALT, Modifier.CONTROL, Modifier.SHIFT], {
        K('Super-h'): K('left'),
        K('Super-j'): K('down'),
        K('Super-k'): K('up'),
        K('Super-l'): K('right'),
        K('Super-a'): K('home'),
        K('Super-e'): K('end'),
        K('Super-f'): K('page_down'),
        K('Super-b'): K('page_up'),
        K('Super-i'): K('insert'),
        K('Super-d'): K('delete'),
    }),
    # }}}
    K('Super-q'): launch(['bspc', 'node', '-c']),
    # run mode {{{
    K('Super-r'): run_mode,
    # }}}
    # focus mode {{{
    K('Super-w'): [polybar('focus'), repeat(Modifier.SUPER, {
        K('h'): launch(['i3-msg', 'focus', 'left']),
        K('j'): launch(['i3-msg', 'focus', 'down']),
        K('k'): launch(['i3-msg', 'focus', 'up']),
        K('l'): launch(['i3-msg', 'focus', 'right']),
        K('a'): launch(['i3-msg', 'focus', 'parent']),
        K('d'): launch(['i3-msg', 'focus', 'child']),
        K('f'): launch(['i3-msg', 'focus', 'mode_toggle']),

        **{K(f'KEY_{i}'): launch(['i3-msg', 'workspace', 'number', n]) for i, n in workspaces},

        K('enter'): launch(['i3-msg', 'mode', 'FOCUS']),
    })],
    # }}}
    # window mode {{{
    K('Super-t'): [polybar('win'), repeat(Modifier.SUPER, {
        # K('q'): launch(['i3-msg', 'kill']),
        # K('f'): launch(['i3-msg', 'fullscreen', 'toggle']),
        # K('space'): launch(['i3-msg', 'floating', 'toggle']),
        # K('s'): launch(['i3-msg', 'sticky', 'toggle']),
        # K('j'): launch(['i3-msg', 'layout', 'toggle', 'split']),
        # K('k'): launch(['i3-msg', 'layout', 'tabbed']),
        # K('l'): launch(['i3-msg', 'layout', 'stacking']),
        K('q'): launch(['bspc', 'node', '-k']),
        # screenshoot {{{
        K('p'): launch(['xfce4-screenshooter', '-f']),
        **left_right({
            K('Shift-p'): launch(['xfce4-screenshooter', '-r']),
            K('Alt-p'): launch(['xfce4-screenshooter', '-w']),
        }),
        # }}}
        # volumn {{{
        K('k'): [
            launch(['pactl', 'set-sink-volume', '0', '+0.1'], reset_mode=False),
            polybar('volume', persist=True),
        ],
        K('j'): [
            launch(['pactl', 'set-sink-volume', '0', '-0.1'], reset_mode=False),
            polybar('volume', persist=True),
        ],
        K('m'): [
            launch(['pactl', 'set-sink-mute', '0', 'toggle'], reset_mode=False),
            polybar('volume-mute', persist=True),
        ],
        # }}}
        # brightness {{{
        K('o'): [
            launch(['light', '-A', '5'], reset_mode=False),
            polybar('brightness', persist=True),
        ],
        K('i'): [
            launch(['light', '-U', '5'], reset_mode=False),
            polybar('brightness', persist=True),
        ],
        # }}}
        # music {{{
        K('h'): launch(['playerctl', 'previous']),
        K('l'): launch(['playerctl', 'next']),
        K('space'): launch(['playerctl', 'play-pause']),
        K('a'): launch([
            'zsh', '-c',
            'current_card=$(pactl list short cards | cut -d $\'\\t\' -f 2 | dmenu)\n'
            'if [[ ! -z "$current_card" ]]; then'
            '  profile=$(for card in ${(ps:\\n\\n:)"$(pactl list cards 2> /dev/null)"}; do'
            '    if [[ $card == *$current_card* ]]; then'
            '      raw_profiles=${card##*Profiles:};'
            '      raw_profiles=${raw_profiles%%Active Profile:*};'
            '      for profile in ${(f)raw_profiles}; do'
            '        if [[ $profile != [[:blank:]] ]]; then'
            '          profile_name=${profile%%: *};'
            '          profile_name=${profile_name//[[:blank:]]/};'
            '          profile_name=${profile_name//:/\\\\:};'
            '          echo $profile_name;'
            '        fi;'
            '      done;'
            '    fi;'
            '  done | dmenu);'
            '  if [[ ! -z "$profile" ]]; then'
            '    pactl set-card-profile "$current_card" "$profile";'
            '  fi;'
            'fi',
        ]),
        # }}}
        # bluetooth {{{
        K('c'): launch([
            'sh', '-c',
            'device=$(bluetoothctl paired-devices | while read uuid; do'
            '  if [[ -z $(bluetoothctl info $(echo "$uuid" | cut -d " " -f 2) | grep "Connected: yes") ]]; then'
            '    echo $uuid;'
            '  fi;'
            'done | dmenu)\n'
            'if [[ ! -z $device ]]; then bluetoothctl connect $(echo $device | cut -d " " -f 2); fi',
        ]),
        K('d'): launch([
            'sh', '-c',
            'device=$(bluetoothctl paired-devices | while read uuid; do'
            '  if [[ ! -z $(bluetoothctl info $(echo "$uuid" | cut -d " " -f 2) | grep "Connected: yes") ]]; then'
            '    echo $uuid;'
            '  fi;'
            'done | dmenu)\n'
            'if [[ ! -z $device ]]; then bluetoothctl disconnect $(echo $device | cut -d " " -f 2); fi',
        ]),
        # }}}
    })],
    # }}}
    # move mode {{{
    K('Super-m'): [polybar('move'), repeat(Modifier.SUPER, {
        K('h'): launch(['i3-msg', 'move', 'left']),
        K('j'): launch(['i3-msg', 'move', 'down']),
        K('k'): launch(['i3-msg', 'move', 'up']),
        K('l'): launch(['i3-msg', 'move', 'right']),

        **{K(f'KEY_{i}'): launch(['i3-msg', 'move', 'container', 'to',
                                  'workspace', 'number', n]) for i, n in workspaces},

        K('enter'): launch(['i3-msg', 'mode', 'MOVE']),
    })],
    # }}}
    # # session mode {{{
    # K('Super-q'): [polybar('session'), {
    #     K('l'): launch(['dm-tool', 'lock']),
    #     K('e'): launch(['i3-msg', 'exit']),
    #     K('s'): launch(['sh', '-c', 'dm-tool lock && sleep 1 && systemctl suspend']),
    #     K('r'): launch(['systemctl', 'reboot']),
    #     K('p'): launch(['systemctl', 'poweroff', '-i']),
    # }],
    # # }}}
})
# }}}
