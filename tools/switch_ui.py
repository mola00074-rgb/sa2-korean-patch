"""닌텐도 스위치 Pro 컨트롤러 UI 옵션.

Steam 설정에서 「Nintendo 버튼 배치 사용」을 켠 상태(버튼에 적힌 글자 = 게임의 A/B/X/Y) 기준입니다.
- 텍스트: LT/RT -> ZL/ZR, LB/RB -> L/R, START -> +, BACK -> -, Xbox 360 컨트롤러 -> Pro 컨트롤러
- 아이콘: 액션 창의 Xbox 빨간 B 버튼 그림을 스위치 스타일 B 버튼으로 교체
"""
import io, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import pak, dds

RULES = [
    (r'Xbox 360 컨트롤러', 'Pro 컨트롤러'),
    (r'LT와 RT 트리거', 'ZL과 ZR 버튼'),
    (r'L과 R 트리거', 'ZL과 ZR 버튼'),
    (r'LT RT 트리거 버튼', 'ZL ZR 버튼'),
    (r'LT RT', 'ZL ZR'),
    (r'LR 트리거 버튼', 'ZL·ZR 버튼'),
    (r'LR 트리거', 'ZL·ZR 버튼'),
    (r'L2 R2 트리거', 'ZL ZR 버튼'),
    (r'\bLT\b', 'ZL'),
    (r'\bRT\b', 'ZR'),
    (r'\bLB\b', 'L'),
    (r'\bRB\b', 'R'),
    (r'START 버튼', '+ 버튼'),
    (r'\bSTART\b', '+'),
    (r'BACK 버튼', '- 버튼'),
]


def convert_text(s):
    for a, b in RULES:
        s = re.sub(a, b, s)
    return s.replace('버튼로', '버튼으로').replace('버튼를', '버튼을').replace('버튼는', '버튼은').replace('버튼가', '버튼이')


FONT_CANDIDATES = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    'C:/Windows/Fonts/arialbd.ttf',
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
]


def _font(size):
    for f in FONT_CANDIDATES:
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def draw_button(letter, size=64, scale=8):
    """스위치 Pro 컨트롤러 느낌의 버튼 아이콘 (짙은 회색 원 + 흰 글자, 검은 테두리)."""
    S = size * scale
    img = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    m = int(S * 0.04)
    d.ellipse([m, m, S - m, S - m], fill=(10, 10, 10, 255))                      # 검은 외곽선
    m2 = int(S * 0.11)
    # 세로 그라데이션 몸체
    body = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    grad = np.zeros((S, S, 4), np.uint8)
    top, bot = np.array([92, 92, 98]), np.array([38, 38, 42])
    t = np.linspace(0, 1, S)[:, None]
    grad[..., :3] = (top * (1 - t) + bot * t)[:, None, :].astype(np.uint8)
    grad[..., 3] = 255
    mask = Image.new('L', (S, S), 0)
    ImageDraw.Draw(mask).ellipse([m2, m2, S - m2, S - m2], fill=255)
    body = Image.fromarray(grad, 'RGBA'); body.putalpha(mask)
    img.alpha_composite(body)
    # 상단 하이라이트
    hl = Image.new('L', (S, S), 0)
    ImageDraw.Draw(hl).ellipse([int(S * .22), int(S * .15), int(S * .78), int(S * .45)], fill=70)
    white = Image.new('RGBA', (S, S), (255, 255, 255, 0)); white.putalpha(hl)
    img.alpha_composite(white)
    # 글자
    f = _font(int(S * 0.52))
    l, t_, r, b = d.textbbox((0, 0), letter, font=f)
    x = (S - (r - l)) / 2 - l
    y = (S - (b - t_)) / 2 - t_
    d.text((x, y), letter, font=f, fill=(240, 240, 240, 255), stroke_width=int(S * 0.012), stroke_fill=(240, 240, 240, 255))
    return img.resize((size, size), Image.LANCZOS)


ICONS = {
    # pak 파일: {텍스처 이름: 글자}
    'console.pak': {'actionw02.dds': 'B'},
}


def patch_paks(gd_in, gd_out):
    """원본 PRS/*.pak 를 읽어 아이콘을 바꾼 pak 를 gd_out/PRS 에 쓴다. 바꾼 파일 목록을 반환."""
    done = []
    for pk, icons in ICONS.items():
        src = os.path.join(gd_in, 'PRS', pk)
        if not os.path.exists(src):
            continue
        header, files = pak.read(src)
        new = []
        for longname, name, data in files:
            base = name.split('\\')[-1]
            if base in icons:
                w = int.from_bytes(data[16:20], 'little')
                data = dds.write_dxt5(draw_button(icons[base], size=w))
            new.append((longname, name, data))
        dst = os.path.join(gd_out, 'PRS', pk)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        pak.write(dst, header, new)
        done.append('PRS/' + pk)
    return done
