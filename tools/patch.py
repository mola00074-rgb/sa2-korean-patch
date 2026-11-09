"""소닉 어드벤처 2 (Steam PC) 한글 패치 적용 도구.

사용법:
  python tools/patch.py --install "C:\\...\\steamapps\\common\\Sonic Adventure 2"
      원본을 _korean_patch_backup 폴더에 백업한 뒤 게임 폴더에 바로 적용합니다.
  python tools/patch.py --out out_dir "C:\\...\\Sonic Adventure 2"
      게임 폴더는 건드리지 않고 out_dir 아래에 패치된 파일만 만듭니다.
  python tools/patch.py --uninstall "C:\\...\\Sonic Adventure 2"
      백업해 둔 원본 메시지 파일을 되돌립니다. (폰트는 Steam 무결성 검사로 복구)
"""
import sys, os, json, shutil, argparse
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import prs, msgfile, units, charmap

ROOT = os.path.dirname(HERE)
FONT_NAME = 'EFMSGFONT_KANJI24.BIN'
PREBUILT_FONT = os.path.join(ROOT, 'font', FONT_NAME)
BACKUP_DIR = '_korean_patch_backup'


def load_translations(path=None):
    path = path or os.path.join(ROOT, 'translation', 'ko.json')
    data = json.load(open(path, encoding='utf-8'))
    return {k: v for k, v in data.items() if v}


def patch_bytes(src, rel, tr, table, missing):
    d = msgfile.load(src)
    e, b = msgfile.fmt_for(rel)
    S, ptrs, strs = msgfile.parse(d, e, b)
    new = {}
    for o, s in strs.items():
        out = bytearray()
        for is_text, part in units.split(s):
            if is_text and units.is_translatable(part):
                uid = units.unit_id(part)
                ko = tr.get(uid)
                if ko is None:
                    missing.add(uid)
                    out += part
                else:
                    out += charmap.encode(ko, table)
            else:
                out += part
        new[o] = bytes(out)
    data = msgfile.rebuild(d, e, b, S, ptrs, new)
    if rel.lower().endswith('.prs'):
        data = prs.compress(data)
    return data


def looks_patched(src, rel, tr):
    """원본이면 번역 대상 문장 대부분이 ko.json 키와 일치한다. 하나도 안 맞으면 이미 패치된 파일."""
    d = msgfile.load(src)
    e, b = msgfile.fmt_for(rel)
    S, ptrs, strs = msgfile.parse(d, e, b)
    total = hit = 0
    for s in strs.values():
        for is_text, part in units.split(s):
            if is_text and units.is_translatable(part):
                total += 1
                hit += units.unit_id(part) in tr
    return total > 0 and hit == 0


def gd_of(game_dir):
    gd = os.path.join(game_dir, 'resource', 'gd_PC')
    if not os.path.isdir(gd):
        raise SystemExit('resource\\gd_PC 폴더를 찾을 수 없습니다: %s' % game_dir)
    return gd


def write_font(dst):
    if os.path.exists(PREBUILT_FONT):
        shutil.copyfile(PREBUILT_FONT, dst)
    else:
        import build_font
        build_font.main(dst)


def run(game_dir, out_dir=None, install=False, tr_path=None, controller='xbox'):
    gd = gd_of(game_dir)
    tr = load_translations(tr_path)
    tr_orig = tr
    if controller == 'switch':
        import switch_ui
        tr = {k: switch_ui.convert_text(v) for k, v in tr.items()}
    table = charmap.build_table()
    missing = set()
    backup_root = os.path.join(game_dir, BACKUP_DIR, 'resource', 'gd_PC')
    targets = [r for r in msgfile.targets(gd) if not any(k in r for k in units.SKIP_FILES)]
    for rel in targets:
        src = os.path.join(gd, rel)
        if not install and os.path.exists(os.path.join(backup_root, rel)):
            src = os.path.join(backup_root, rel)
        if install:
            bak = os.path.join(backup_root, rel)
            if os.path.exists(bak):
                src = bak                      # 이미 패치된 상태면 원본 백업에서 다시 만든다
            else:
                if looks_patched(src, rel, tr_orig):
                    raise SystemExit('%s 은(는) 이미 한글 패치가 적용된 파일입니다.\n'
                                     'Steam에서 「게임 파일 무결성 확인」으로 원본을 복구한 뒤 다시 실행하세요.' % rel)
                os.makedirs(os.path.dirname(bak), exist_ok=True)
                shutil.copy2(src, bak)
        data = patch_bytes(src, rel, tr, table, missing)
        dst = os.path.join(gd if install else os.path.join(out_dir, 'resource', 'gd_PC'), rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, 'wb').write(data)
    font_dst = os.path.join(gd if install else os.path.join(out_dir, 'resource', 'gd_PC'), FONT_NAME)
    write_font(font_dst)
    if controller == 'switch':
        import switch_ui
        out_gd = gd if install else os.path.join(out_dir, 'resource', 'gd_PC')
        src_gd = backup_root if os.path.isdir(os.path.join(backup_root, 'PRS')) else gd
        if install:
            for pk in switch_ui.ICONS:
                srcp = os.path.join(gd, 'PRS', pk)
                bak = os.path.join(backup_root, 'PRS', pk)
                if not os.path.exists(bak) and os.path.exists(srcp):
                    os.makedirs(os.path.dirname(bak), exist_ok=True)
                    shutil.copy2(srcp, bak)
            src_gd = backup_root
        done = switch_ui.patch_paks(src_gd, out_gd)
        print('스위치 Pro 컨트롤러 아이콘 적용: %s' % ', '.join(done))
    elif install:
        bak_prs = os.path.join(backup_root, 'PRS')
        if os.path.isdir(bak_prs):            # 이전에 스위치 아이콘을 적용했다면 원래 아이콘으로 되돌린다
            for f in os.listdir(bak_prs):
                shutil.copy2(os.path.join(bak_prs, f), os.path.join(gd, 'PRS', f))
    print('메시지 파일 %d개 패치 완료 (미번역 %d개)' % (len(targets), len(missing)))
    if install:
        print('원본 메시지 파일 백업 위치: %s' % os.path.join(game_dir, BACKUP_DIR))
        print('게임 런처에서 텍스트 언어를 「日本語」로 설정하세요.')


def uninstall(game_dir):
    gd = gd_of(game_dir)
    backup_root = os.path.join(game_dir, BACKUP_DIR, 'resource', 'gd_PC')
    if not os.path.isdir(backup_root):
        raise SystemExit('백업 폴더가 없습니다.')
    n = 0
    for base, _, files in os.walk(backup_root):
        for f in files:
            src = os.path.join(base, f)
            rel = os.path.relpath(src, backup_root)
            shutil.copy2(src, os.path.join(gd, rel))
            n += 1
    print('원본 메시지 파일 %d개 복원 완료.' % n)
    print('폰트(EFMSGFONT_KANJI24.BIN)는 Steam에서 「게임 파일 무결성 확인」으로 복구하세요.')


def main(argv=None):
    ap = argparse.ArgumentParser(description='Sonic Adventure 2 (Steam) Korean patch')
    ap.add_argument('game_dir', help='Sonic Adventure 2 설치 폴더')
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--install', action='store_true', help='게임 폴더에 바로 적용 (원본 백업)')
    g.add_argument('--out', help='패치된 파일을 이 폴더에 출력')
    g.add_argument('--uninstall', action='store_true', help='백업에서 원본 복원')
    ap.add_argument('--translations', help='번역 JSON 경로 (기본: translation/ko.json)')
    ap.add_argument('--controller', choices=['xbox', 'switch'], default='xbox',
                    help='버튼 표기: xbox(기본) 또는 switch (스위치 Pro 컨트롤러, Steam의 Nintendo 버튼 배치 사용)')
    a = ap.parse_args(argv)
    if a.uninstall:
        uninstall(a.game_dir)
    else:
        run(a.game_dir, out_dir=a.out, install=a.install, tr_path=a.translations, controller=a.controller)


if __name__ == '__main__':
    main()
