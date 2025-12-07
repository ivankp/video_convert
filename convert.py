#!/usr/bin/env python3

import sys, os, re, subprocess

def fatal(*args):
    print(*args, file=sys.stderr)
    sys.exit(1)

if len(sys.argv) < 2:
    fatal('usage:', sys.argv[0], 'input [streams ...] ... [output]')

if len(sys.argv) == 2:
    process = subprocess.Popen(
        [ 'ffmpeg', '-i', sys.argv[-1] ],
        stderr = subprocess.PIPE
    )
    for line in process.stderr:
        if line.startswith(b'  Stream #'):
            print(line.decode().strip())
    sys.exit()

if (set(sys.argv[-1]) & set('^%:*?<>|"\'')) or not re.match(r'.+\.[^.]+$', sys.argv[-1]):
    fatal('last argument must be an output file name')

re_stream = re.compile(r'^([0-9]+|[vas](?::[0-9]+)?)(.*)')
re_volume = re.compile(r'\*([0-9]+(?:\.[0-9]+))')
re_format = re.compile(r'\[([^\[\]]+)\]')
re_lang   = re.compile(r'\(([a-z]{3})\)')

cmd = [ 'ffmpeg' ]

i = -1
o = -1
a = 0
for arg in sys.argv[1:-1]:
    if os.path.isfile(arg):
        i += 1
        cmd += [ '-i', arg ]
    elif i < 0:
        fatal(f'{arg} is not a file')
    else:
        m = re_stream.match(arg)
        if m:
            o += 1

            if mv := re_volume.search(m[2]):
                a += 1
                cmd += [
                    '-filter_complex', f'[{i}:{m[1]}]volume={mv[1]}[a{a}]',
                    '-map', f'[a{a}]'
                ]
            else:
                cmd += [ '-map', f'{i}:{m[1]}' ]

            if mf := re_format.search(m[2]):
                cmd += [ f'-c:{o}', *mf[1].split() ]
            else:
                cmd += [ f'-c:{o}', 'copy' ]

            # TODO: language

        else:
            fatal(f'{arg} is not a valid stream argument')

cmd.append(sys.argv[-1])

print(cmd)
subprocess.run(cmd)
