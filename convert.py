#!/usr/bin/env python3

import sys, os, re, subprocess, argparse

def fatal(*args):
    print(*args, file=sys.stderr)
    sys.exit(1)

parser = argparse.ArgumentParser()
parser.add_argument('-o', '--output', type=str, help='output file')
parser.add_argument('-n', '--dry-run', action='store_true', help='print ffmpeg command and exit')
parser.add_argument('input', nargs='+', help=' input [streams ...] ... [lang ...]')
args = parser.parse_args()

re_file = re.compile(r'.+\.[^.]+$')
def is_file(path):
    return re_file.match(path) and os.path.isfile(path)

if not is_file(args.input[0]):
    fatal('first positional argument must be a valid file name')

if len(args.input) == 1:
    for line in subprocess.Popen(
        [ 'ffmpeg', '-i', args.input[0] ],
        stderr = subprocess.PIPE
    ).stderr:
        if line.startswith(b'  Stream #'):
            print(line.decode().strip())
    sys.exit()

if args.output is None:
    fatal('must specify an output file: -o/--output')

if os.path.isdir(args.output):
    args.output = os.path.join(args.output, os.path.basename(args.input[0]))

output_exists = os.path.isfile(args.output)

re_stream = re.compile(r'^(\d+|[vas](?::\d+)?)(.*)')
re_volume = re.compile(r'\*(\d+(?:\.\d*)?)')
re_lang   = re.compile(r'^([a-z]{3}):(\d+|[vas](?::\d+)?)$')

cmd = [ 'ffmpeg' ]

i = -1
o = -1
a = 0
for arg in args.input:
    if is_file(arg):
        if output_exists and os.path.samefile(arg, args.output):
            fatal('output must not overwrite any input files')

        i += 1
        cmd += [ '-i', arg ]

    else:
        if m := re_stream.match(arg):
            o += 1
            s = f'{i}:{m[1]}'
            arg = m[2].strip()

            arg = re_volume.split(arg)
            if len(arg) > 1:
                a += 1
                cmd += [
                    '-filter_complex', f'[{s}]volume={arg[-2]}[a{a}]',
                    '-map', f'[a{a}]'
                ]
                arg = ''.join(arg[::2])
            else:
                cmd += [ '-map', s ]
                arg = arg[0]

            cmd.append(f'-c:{o}')
            if arg:
                for x in arg.split():
                    cmd.append(x)
            else:
                cmd.append('copy')

        elif m := re_lang.match(arg):
            cmd += [ f'-metadata:s:{m[2]}', f'language={m[1]}' ]

        else:
            fatal(f'{arg} is not a valid argument')

cmd.append(args.output)

print(*cmd)

if not args.dry_run:
    print()
    subprocess.run(cmd)
