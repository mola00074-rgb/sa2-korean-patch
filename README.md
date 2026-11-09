# 소닉 어드벤처 2 한글 패치 (Steam PC판)

Steam판 **Sonic Adventure 2** 를 위한 비공식 한글 패치입니다.
이 저장소에는 **게임 데이터가 들어 있지 않습니다.** 패치 도구와 번역문, 그리고 Noto Sans CJK로 새로 그린 폰트만 들어 있으며,
가지고 있는 게임 파일에 직접 적용하는 방식입니다.

## 번역 범위

| 항목 | 상태 |
|---|---|
| 컷신 자막 (히어로 / 다크 / 라스트 스토리) | ✅ |
| 오모차오 힌트, 스테이지 안내, 미션 문구 | ✅ |
| 보물찾기(너클즈·루즈) 에메랄드 힌트 | ✅ |
| 일시 정지 메뉴, 액션 창, 아이템 설명 | ✅ |
| 차오 가든·차오 유치원·레이스·가라테 메시지 | ✅ |
| 메인 메뉴, 스테이지 타이틀 등 **이미지로 된 글자** | ❌ (텍스처라 별도 작업 필요) |
| 차오 이름 목록 | ❌ (원본 유지) |

총 4,953개 문장(중복 제외)을 번역했습니다.

## 설치 방법

### 1. 준비물
- Steam판 Sonic Adventure 2
- [Python 3](https://www.python.org/downloads/) (설치할 때 "Add Python to PATH" 체크)

### 2. 적용
1. 이 저장소를 내려받아 압축을 풉니다. (초록색 **Code** 버튼 → **Download ZIP**)
2. `install.bat` 을 실행하고, 게임 폴더 경로를 묻는 창에 그냥 Enter를 누릅니다.
   (기본 경로 `C:\Program Files (x86)\Steam\steamapps\common\Sonic Adventure 2` 가 아니라면 직접 입력)
   - 명령어로 하려면: `python tools\patch.py --install "C:\Program Files (x86)\Steam\steamapps\common\Sonic Adventure 2"`
3. 게임 **런처(Launcher.exe)** 의 설정에서 **텍스트 언어(Text Language)를 「日本語(일본어)」** 로 바꿉니다.
   한글은 일본어 텍스트 자리에 들어가 있습니다. 음성 언어는 영어·일본어 아무거나 괜찮습니다.

### 3. 제거
- `uninstall.bat` 실행 → 원본 메시지 파일을 백업에서 되돌립니다.
- 그다음 Steam 라이브러리에서 게임 우클릭 → **속성 → 설치된 파일 → 게임 파일 무결성 확인** 을 하면 폰트까지 원래대로 돌아옵니다.

## 동작 원리

SA2 PC판의 일본어 폰트(`EFMSGFONT_KANJI24.BIN`)는 24×24 RGBA 글리프 3,423자를 JIS 순서로 담고 있습니다.
이 중 JIS 제1수준 한자 자리(2,965칸)에 KS X 1001 한글 2,350자를 그려 넣고,
번역문의 한글은 해당 한자의 Shift-JIS 코드로 인코딩합니다.
띄어쓰기·숫자·영문은 원래 일본어 모드에서도 쓰이는 1바이트 ASCII 폰트를 그대로 씁니다.

메시지 파일은 SEGA PRS 압축을 풀고, 문자열 포인터 테이블을 다시 계산해 새로 압축합니다.

| 파일 | 내용 |
|---|---|
| `resource/gd_PC/Message/*j.prs` | 힌트·시스템·미션·차오 메시지 (게임패드용) |
| `resource/gd_PC/MessageK/*j.prs` | 같은 내용의 키보드 조작용 버전 |
| `resource/gd_PC/event/evmes{H,D,L}0.prs` | 컷신 자막 (0 = 일본어) |
| `resource/gd_PC/msgChao*_j.*` | 차오 관련 메시지 |
| `resource/gd_PC/EFMSGFONT_KANJI24.BIN` | 폰트 (`font/` 폴더에 미리 만든 파일 포함) |

## 저장소 구성

```
tools/
  prs.py          SEGA PRS 압축/해제
  msgfile.py      메시지 파일(포인터 테이블 + 문자열) 파서
  units.py        제어 코드와 번역 단위 분리
  charmap.py      한글 ↔ Shift-JIS 슬롯 매핑
  build_font.py   폰트 생성 (Pillow, numpy, Noto Sans CJK 필요)
  patch.py        패치 적용/제거
  extract.py      번역 대조표(TSV) 생성·반영
translation/ko.json   번역문 (원문 해시 → 한국어)
font/                 미리 생성한 폰트 + OFL 라이선스
```

번역문은 원문 문장의 SHA-1 해시를 키로 저장하므로 원문 텍스트는 저장소에 없습니다.

## 번역 고치기

```
python tools\extract.py "C:\...\Sonic Adventure 2" sheet.tsv
```
로 `원문 | 번역` 대조표를 만든 뒤, 엑셀 등에서 `korean` 열을 고치고

```
python tools\extract.py --apply sheet.tsv
python tools\patch.py --install "C:\...\Sonic Adventure 2"
```
로 반영합니다. 줄바꿈은 `\n` 으로 적습니다. KS X 1001에 없는 한글(예: 똠, 쌰)도 자동으로 빈 슬롯에 추가됩니다.

## 알려진 한계
- 메뉴 그림, 스테이지 이름 그림, 결과 화면 등 텍스처에 그려진 글자는 아직 영어/일본어입니다.
- 실행 파일 안에 들어 있는 일부 문자열은 바꾸지 않았습니다. 일본어 모드에서 이런 문자열의 한자는 엉뚱한 한글로 보일 수 있습니다.
- PC판에 남아 있는 게임큐브·드림캐스트 시절 안내문(GBA 연결 등)도 원문 그대로 번역했습니다.

## 크레딧·라이선스
- 패치 도구와 번역문: MIT License
- 폰트 글리프: [Noto Sans CJK](https://github.com/notofonts/noto-cjk) (SIL Open Font License 1.1) — `font/OFL.txt`
- 일본어 폰트 문자 배열(`tools/kanji_order.txt`)은 [X-Hax/sa_tools](https://github.com/X-Hax/sa_tools) SAFontEdit 를 참고했고,
  폰트 포맷 정보는 [sa2b-render-fix](https://github.com/shaddatic/sa2b-render-fix) 를 참고했습니다.
- Sonic Adventure 2 및 관련 상표의 권리는 SEGA에 있습니다. 이 프로젝트는 SEGA와 관계없는 팬 번역입니다.
