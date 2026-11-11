"""Regenerates docs/screenshots with each plug-in's snapshot tool (configure with the tools on and build every
<Stem>Snapshot first): <pluginid>.png per plug-in at its design size at 100 % (the tool's standard call, or the
arguments a plug-in lists in MAIN below), the views it lists in VIEWS as <pluginid>-<view>.png, and hero.png, the
plug-ins side by side 24 px apart, each centred in height (at most 1800 px wide). Every image is our own editor, rendered without a window, so a run gives the same files on every
machine. Needs Pillow (requirements.txt).

    python scripts/make_screenshots.py [--build build]
"""
import argparse, os, subprocess, sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'docs', 'screenshots')
GAP = 24          # hero.png: between the editors
HERO_MAX = 1800   # hero.png: the widest it may be

# The views of each plug-in beyond its main image: the plug-in id (packaging/plugins.txt) to a list of
# (view, arguments of its snapshot tool), written as <pluginid>-<view>.png. The arguments are the tool's own:
# paramID=value in real units, --levels=inDb,outDb, --size=W, and an --option the editor's snapshot hooks take.
# The main image takes the arguments under MAIN (none: the standard call).
VIEWS = {
    'Positron': [
        ('classic-style', ['--scale=1', '--levels=-10,-9', '--audio', '--classic']),
    ],
    'Scorpius': [
        ('classic-style', ['--levels=-14,-12', '--audio', '--style=classic']),
    ],
    'Wraith': [],
}
MAIN = {
    'Positron': ['--scale=1', '--levels=-10,-9', '--audio', '--anti'],
    'Scorpius': ['--levels=-14,-12', '--audio', '--style=scorpius'],
    'Wraith': ['--scale=1', '--levels=-12,-14'],
}


def plugins():
    with open(os.path.join(ROOT, 'packaging', 'plugins.txt'), encoding='utf-8') as h:
        return [line.split('|')[0].strip() for line in h if line.strip() and not line.startswith('#')]


def tool(build, target):
    """<Stem>Snapshot: the class stem is the target without a leading The."""
    stem = target[3:] if target.startswith('The') else target
    exe = os.path.join(build, f'{stem}Snapshot_artefacts', 'Release', f'{stem}Snapshot' + ('.exe' if sys.platform == 'win32' else ''))
    if not os.path.isfile(exe):
        sys.exit(f'{exe} is not built (configure with the tools on and build {stem}Snapshot)')
    return exe


def shot(exe, name, args):
    subprocess.run([exe, os.path.join(OUT, name + '.png')] + list(args), check=True, stdout=subprocess.DEVNULL, cwd=ROOT)
    print('wrote', name + '.png')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--build', default=os.path.join(ROOT, 'build'))
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    mains = []
    for target in plugins():
        exe, pid = tool(a.build, target), target.lower()
        shot(exe, pid, MAIN.get(target, []))
        for view, args in VIEWS.get(target, []):
            shot(exe, f'{pid}-{view}', args)
        mains.append(Image.open(os.path.join(OUT, pid + '.png')).convert('RGBA'))

    # hero.png: the editors side by side, each centred in height, on a transparent page
    w = sum(m.width for m in mains) + GAP * (len(mains) - 1)
    h = max(m.height for m in mains)
    hero = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    x = 0
    for m in mains:
        hero.paste(m, (x, (h - m.height) // 2)); x += m.width + GAP
    if hero.width > HERO_MAX:
        hero = hero.resize((HERO_MAX, round(hero.height * HERO_MAX / hero.width)), Image.LANCZOS)
    hero.save(os.path.join(OUT, 'hero.png'), optimize=True)
    print('wrote hero.png', hero.size)


if __name__ == '__main__':
    main()
