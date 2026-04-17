#!/usr/bin/env python3
"""교안의 ASCII 박스 다이어그램을 한글 폭 보정하여 정렬 수정.

문제: 한글 1자 = 폭 2칸, 영문/기호 1자 = 폭 1칸인데
      라인 길이를 len()으로만 맞추면 들쑥날쑥.

전략:
1. ``` 코드블록 내 +---+ 또는 ┌───┐ 스타일 박스를 감지
2. 각 라인의 "표시 폭(display width)"을 계산
3. 박스 구분선(+---+, ┌───┐)의 최대 표시 폭에 맞춰 패딩 조정
4. | 내용 | 라인은 오른쪽 패딩을 표시 폭 기준으로 맞춤

Usage:
  python3 scripts/fix_ascii_boxes.py                    # 전체
  python3 scripts/fix_ascii_boxes.py --dry-run           # 미리보기
  python3 scripts/fix_ascii_boxes.py contents/education/course11-battle/week09/lecture.md
"""
import argparse, glob, re, unicodedata


def display_width(s: str) -> int:
    """문자열의 터미널 표시 폭 계산 (한글=2, 영문=1)."""
    w = 0
    for ch in s:
        if ch == '\t':
            w += 4
            continue
        cat = unicodedata.east_asian_width(ch)
        w += 2 if cat in ('W', 'F') else 1
    return w


def pad_to_width(s: str, target_width: int, fill=' ') -> str:
    """문자열을 target_width 표시 폭으로 오른쪽 패딩."""
    current = display_width(s)
    if current >= target_width:
        return s
    return s + fill * (target_width - current)


def fix_box_block(lines: list[str]) -> list[str]:
    """단일 박스 블록의 라인들을 정렬 보정."""
    if not lines:
        return lines

    # 박스 구분선 감지 (+---+, |---|, ┌───┐ 등)
    border_char_h = None
    border_char_v = None
    if any('+' in l and '-' in l for l in lines):
        border_char_h = '+'
        border_char_v = '|'
    elif any('┌' in l or '└' in l for l in lines):
        border_char_h = '┌'
        border_char_v = '│'

    if not border_char_v:
        return lines  # 박스가 아님

    # 최대 표시 폭 계산 (구분선 기준)
    max_width = 0
    for line in lines:
        stripped = line.rstrip()
        if not stripped:
            continue
        w = display_width(stripped)
        max_width = max(max_width, w)

    if max_width == 0:
        return lines

    result = []
    for line in lines:
        stripped = line.rstrip()
        if not stripped:
            result.append(line)
            continue

        # 구분선 재생성 (+-...-+ 또는 ┌─...─┐ 스타일)
        if border_char_h == '+' and re.match(r'^\s*\+[-=+]+\+\s*$', stripped):
            # 리딩 공백 유지
            indent = len(stripped) - len(stripped.lstrip())
            inner = max_width - indent - 2  # +와 + 제외
            if inner < 1:
                inner = len(stripped) - indent - 2
            fill = '=' if '=' in stripped else '-'
            new_line = ' ' * indent + '+' + fill * inner + '+'
            result.append(new_line)
            continue

        # 내용 라인: | 내용 | → 오른쪽 | 위치를 맞춤
        if border_char_v in stripped:
            # 마지막 | 뒤 공백 제거하고 표시 폭에 맞춰 재패딩
            # | 로 시작하고 | 로 끝나는 패턴
            m = re.match(r'^(\s*\|)(.*?)(\|\s*)$', stripped)
            if m:
                prefix = m.group(1)
                content = m.group(2)
                suffix = '|'
                # content를 target 폭에 맞춤
                target_content_width = max_width - display_width(prefix) - display_width(suffix)
                if target_content_width > 0:
                    padded = pad_to_width(content, target_content_width)
                    result.append(prefix + padded + suffix)
                    continue

        result.append(stripped)

    return result


def fix_lecture(path: str, dry_run: bool = False) -> int:
    """단일 교안 파일의 ASCII 박스를 수정. 수정 횟수 반환."""
    content = open(path, encoding='utf-8').read()

    # ``` 코드블록 추출
    parts = re.split(r'(```[^\n]*\n.*?```)', content, flags=re.DOTALL)
    fixed_count = 0
    new_parts = []

    for part in parts:
        if part.startswith('```'):
            # 코드블록 내부 처리
            header_end = part.index('\n')
            header = part[:header_end + 1]
            footer = '```'
            body = part[header_end + 1:]
            if body.endswith('```'):
                body = body[:-3]

            lines = body.split('\n')

            # 박스가 있는지 확인
            has_box = any(
                re.search(r'\+[-=+]{3,}\+|[┌└╔╚]', l)
                for l in lines
            )

            if has_box:
                # 박스 블록 단위로 분리하여 수정
                blocks = []
                current_block = []
                in_box = False

                for line in lines:
                    is_border = bool(re.search(r'^\s*\+[-=+]+\+|^\s*[┌└╔╚]', line))
                    has_pipe = '|' in line or '│' in line

                    if is_border or (in_box and (has_pipe or line.strip() == '')):
                        current_block.append(line)
                        in_box = True
                    else:
                        if current_block:
                            blocks.append(('box', current_block))
                            current_block = []
                            in_box = False
                        blocks.append(('text', [line]))

                if current_block:
                    blocks.append(('box', current_block))

                new_lines = []
                for btype, blines in blocks:
                    if btype == 'box':
                        fixed = fix_box_block(blines)
                        if fixed != blines:
                            fixed_count += 1
                        new_lines.extend(fixed)
                    else:
                        new_lines.extend(blines)

                new_parts.append(header + '\n'.join(new_lines) + footer)
            else:
                new_parts.append(part)
        else:
            new_parts.append(part)

    if fixed_count > 0 and not dry_run:
        open(path, 'w', encoding='utf-8').write(''.join(new_parts))

    return fixed_count


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('files', nargs='*', help='특정 파일만 (기본: 전체 교안)')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    if args.files:
        paths = args.files
    else:
        paths = sorted(glob.glob('contents/education/*/week*/lecture.md'))

    total = 0
    for path in paths:
        n = fix_lecture(path, dry_run=args.dry_run)
        if n > 0:
            print(f"{'[DRY] ' if args.dry_run else ''}Fixed {n} boxes in {path}")
            total += n

    print(f"\nTotal: {total} boxes fixed in {len(paths)} files")


if __name__ == '__main__':
    main()
