"""번역 작업용 대조표 만들기.

자신의 게임 파일(일본어 원문)과 translation/ko.json 을 나란히 놓은 TSV를 만듭니다.
저장소에는 원문을 올리지 않으므로, 번역을 고칠 때는 이 스크립트로 로컬에서 대조표를 만드세요.

사용법:
  python tools/extract.py "C:\\...\\Sonic Adventure 2" sheet.tsv
  (sheet.tsv 를 고친 뒤)
  python tools/extract.py --apply sheet.tsv      # ko.json 에 반영
"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import msgfile, units

ROOT = os.path.dirname(HERE)
KO = os.path.join(ROOT, 'translation', 'ko.json')
BACKUP_DIR = '_korean_patch_backup'


def esc(s):
    return s.replace('\\', '\\\\').replace('\t', '\\t').replace('\n', '\\n')


def unesc(s):
    out, i = [], 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            out.append({'n': '\n', 't': '\t', '\\': '\\'}.get(s[i + 1], s[i + 1]))
            i += 2
        else:
            out.append(s[i]); i += 1
    return ''.join(out)


def extract(game_dir, out):
    gd = os.path.join(game_dir, 'resource', 'gd_PC')
    bak = os.path.join(game_dir, BACKUP_DIR, 'resource', 'gd_PC')
    ko = json.load(open(KO, encoding='utf-8')) if os.path.exists(KO) else {}
    seen = set()
    with open(out, 'w', encoding='utf-8-sig') as f:
        f.write('id\tfile\tjapanese\tkorean\n')
        for rel in msgfile.targets(gd):
            if any(k in rel for k in units.SKIP_FILES):
                continue
            src = os.path.join(bak, rel) if os.path.exists(os.path.join(bak, rel)) else os.path.join(gd, rel)
            d = msgfile.load(src)
            e, b = msgfile.fmt_for(rel)
            S, ptrs, strs = msgfile.parse(d, e, b)
            for _, o in sorted(ptrs):
                for is_text, part in units.split(strs[o]):
                    if not (is_text and units.is_translatable(part)):
                        continue
                    uid = units.unit_id(part)
                    if uid in seen:
                        continue
                    seen.add(uid)
                    jp = part.decode('cp932', 'backslashreplace')
                    f.write('%s\t%s\t%s\t%s\n' % (uid, rel, esc(jp), esc(ko.get(uid, ''))))
    print('%d개 항목을 %s 에 저장했습니다.' % (len(seen), out))


def apply(sheet):
    ko = json.load(open(KO, encoding='utf-8')) if os.path.exists(KO) else {}
    n = 0
    for ln in open(sheet, encoding='utf-8-sig'):
        cols = ln.rstrip('\r\n').split('\t')
        if len(cols) < 4 or cols[0] == 'id':
            continue
        t = unesc(cols[3])
        if t and ko.get(cols[0]) != t:
            ko[cols[0]] = t
            n += 1
    json.dump(dict(sorted(ko.items())), open(KO, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('%d개 번역을 갱신했습니다.' % n)


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--apply':
        apply(sys.argv[2])
    elif len(sys.argv) == 3:
        extract(sys.argv[1], sys.argv[2])
    else:
        print(__doc__)
