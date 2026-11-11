"""Choose per-role Chinese fonts on macOS/Linux and prove every rendered character has a glyph.

Coverage is read from the font's cmap with fontTools: Pillow has no glyph-lookup API and draws a
missing character as the .notdef box, which a rendered-bbox test cannot tell apart from a real glyph.
Pen text is drawn with the handwriting font, so it is checked against that role.
"""
import functools
import glob
import json
import logging
from pathlib import Path
import shutil
import subprocess
import sys
from fontTools.ttLib import TTFont

logging.getLogger('fontTools').setLevel(logging.ERROR)
BASELINE = '中文'  # an empty role must still resolve to a Chinese-capable font
MAC_ASSETS = '/System/Library/AssetsV2/com_apple_MobileAsset_Font*/*/AssetData/'
MAC_SANS = [('/System/Library/Fonts/Hiragino Sans GB.ttc', 0), ('/System/Library/Fonts/STHeiti Medium.ttc', 1),
            ('/System/Library/Fonts/Supplemental/Songti.ttc', 6), ('/System/Library/Fonts/Supplemental/Arial Unicode.ttf', 0)]
LINUX_SANS = ['/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',                    # Debian/Ubuntu fonts-noto-cjk
              '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc',                         # Arch noto-fonts-cjk
              '/usr/share/fonts/google-noto-sans-cjk-fonts/NotoSansCJK-Regular.ttc',       # Fedora google-noto-sans-cjk-fonts
              '/usr/share/fonts/google-noto-sans-cjk-vf-fonts/NotoSansCJK-VF.ttc',         # Fedora default variable font
              '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', '/usr/share/fonts/wenquanyi/wqy-microhei/wqy-microhei.ttc']
INSTALL_HINT = ('macOS: install Hannotate/Hanzipen in Font Book or set font.path; '
                'Linux: sudo apt install fonts-noto-cjk fontconfig (dnf install google-noto-sans-cjk-fonts / pacman -S noto-fonts-cjk)')


def fontconfig(arguments):
    if not shutil.which(arguments[0]):
        return []
    try:
        output = subprocess.run([*arguments[:1], '-f', '%{file}|%{index}\n', *arguments[1:]], capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    return [(path, int(index or 0)) for path, _, index in (line.rpartition('|') for line in output.splitlines()) if path]


def simplified_face(path):
    """Index of the Simplified Chinese face inside a collection (Noto CJK puts JP first)."""
    if not path.lower().endswith('.ttc'):
        return 0
    from fontTools.ttLib import TTCollection
    with TTCollection(path, lazy=True) as collection:
        names = [font['name'].getDebugName(1) or '' for font in collection.fonts]
    return next((index for index, name in enumerate(names) if ' SC' in ' ' + name + ' '), 0)


def candidates(role):
    if sys.platform == 'darwin':
        handwriting = [(path, 2) for name in ('Hannotate.ttc', 'Hanzipen.ttc') for path in sorted(glob.glob(MAC_ASSETS + name))]
        handwriting += [(path, 0) for path in sorted(glob.glob(str(Path.home() / 'Library/Fonts/LXGWWenKai*.tt?')))]
        chain = (handwriting if role == 'handwriting' else []) + MAC_SANS
    else:
        handwriting = fontconfig(['fc-list', 'LXGW WenKai']) + fontconfig(['fc-list', 'AR PL UKai CN'])
        known = [(path, simplified_face(path)) for path in LINUX_SANS if Path(path).is_file()]
        known += [(path, simplified_face(path)) for path in sorted(glob.glob('/usr/share/fonts/**/NotoSansCJK*.tt[cf]', recursive=True))]
        chain = (handwriting if role == 'handwriting' else []) + fontconfig(['fc-match', 'sans-serif:lang=zh-cn']) + known
        chain += sorted(fontconfig(['fc-list', ':lang=zh']))
    return [entry for position, entry in enumerate(chain) if Path(entry[0]).is_file() and entry not in chain[:position]]


@functools.lru_cache(maxsize=None)
def codepoints(path, index):
    collection = path.lower().endswith(('.ttc', '.otc'))
    with (TTFont(path, fontNumber=index, lazy=True) if collection else TTFont(path, lazy=True)) as font:
        return frozenset(font.getBestCmap() or ())


def needed(text):
    return sorted({character for character in BASELINE + str(text) if character.isprintable() and not character.isspace()})


def describe(characters):
    return ' '.join(f'{character}(U+{ord(character):04X})' for character in characters)


def select(role, text='', configured=None):
    """First font in the role's chain that covers every character; an explicit font is never silently replaced."""
    characters = needed(text)
    if configured and configured.get('path'):
        path = Path(configured['path']).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f'Configured {role} font is missing: {path}')
        chain = [(str(path.resolve()), int(configured.get('index', 0)))]
    else:
        chain = candidates(role)
    tried = []
    for path, index in chain:
        try:
            available = codepoints(path, index)
        except Exception as error:  # unreadable or unsupported font file
            tried.append(f'{path}#{index}: unreadable ({error})')
            continue
        missing = [character for character in characters if ord(character) not in available]
        if not missing:
            return path, index
        tried.append(f'{path}#{index}: missing {describe(missing)}')
    if not tried:
        raise FileNotFoundError(f'No Chinese {role} font found. {INSTALL_HINT}')
    raise ValueError(f'No available {role} font covers every character to render. Fonts tried:\n  ' + '\n  '.join(tried)
                     + f'\nReplace the characters, or set a covering font ({role_setting(role)}). {INSTALL_HINT}')


def role_setting(role):
    return {'handwriting': 'job.json font.path/font.index', 'caption': 'captions.font.path', 'watermark': 'watermark.font.path'}[role]


def role_texts(manifest):
    pages = manifest.get('pages', [])
    actions = [action for page in pages for beat in page.get('beats', []) for action in beat.get('actions', [])]
    actions += [action for page in pages for group in page.get('visual_groups', []) for action in group.get('actions', [])]
    watermark = manifest.get('watermark') or {}
    return {'handwriting': ''.join(str(action.get('text', '')) for action in actions if action.get('type') == 'text')
                           + str((manifest.get('hand') or {}).get('pen_text', '')),
            'caption': ''.join(str(beat.get('text', '')) for page in pages for beat in page.get('beats', [])),
            'watermark': str(watermark.get('text', '')) if watermark.get('enabled') is not False else ''}


def check_coverage(manifest):
    """Resolve every role against its real text, pin the result into the in-memory manifest, report all failures at once."""
    texts, report, errors = role_texts(manifest), {}, []
    sections = {'handwriting': manifest, 'caption': manifest.setdefault('captions', {}), 'watermark': manifest.get('watermark') or {}}
    for role, text in texts.items():
        if role == 'watermark' and not text.strip():
            continue
        try:
            path, index = select(role, text, sections[role].get('font'))
        except (ValueError, FileNotFoundError) as error:
            errors.append(str(error))
            continue
        sections[role]['font'] = {'path': path, 'index': index}
        report[role] = {'path': path, 'index': index, 'characters': len(needed(text))}
    if errors:
        raise ValueError('Font coverage check failed:\n' + '\n'.join(errors))
    return report


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('job', nargs='?', type=Path, help='Directory containing job.json; omit to list candidates')
    parser.add_argument('--text', default='', help='Extra text every role must cover')
    arguments = parser.parse_args()
    if arguments.job:
        manifest = json.loads((arguments.job / 'job.json').read_text())
        print(json.dumps(check_coverage(manifest), ensure_ascii=False, indent=2))
    else:
        print(json.dumps({role: {'candidates': candidates(role), 'selected': select(role, arguments.text)}
                          for role in ('handwriting', 'caption')}, ensure_ascii=False, indent=2))
