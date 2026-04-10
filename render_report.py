"""마크다운 보고서를 HTML로 변환하여 브라우저에서 열기"""
import sys
import os
import webbrowser
import re
import base64

sys.stdout.reconfigure(encoding='utf-8')

md_path = sys.argv[1] if len(sys.argv) > 1 else "./output/20260409/20260409_마감리뷰_FULL.md"

with open(md_path, "r", encoding="utf-8") as f:
    md_content = f.read()

# 간단한 마크다운 → HTML 변환
def md_to_html(md):
    lines = md.split("\n")
    html_lines = []
    in_table = False
    in_blockquote = False
    in_ul = False

    for line in lines:
        stripped = line.strip()

        # 빈 줄
        if not stripped:
            if in_table:
                html_lines.append("</table>")
                in_table = False
            if in_blockquote:
                html_lines.append("</blockquote>")
                in_blockquote = False
            if in_ul:
                html_lines.append("</ul>")
                in_ul = False
            html_lines.append("")
            continue

        # 테이블 구분선 스킵
        if re.match(r"^\|[\s\-:]+\|", stripped):
            continue

        # 테이블
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if not in_table:
                html_lines.append('<table>')
                tag = "th"
                in_table = True
            else:
                tag = "td"
            row = "<tr>" + "".join(f"<{tag}>{c}</{tag}>" for c in cells) + "</tr>"
            html_lines.append(row)
            continue

        if in_table:
            html_lines.append("</table>")
            in_table = False

        # 헤더
        if stripped.startswith("######"):
            html_lines.append(f"<h6>{inline_fmt(stripped[6:].strip())}</h6>")
        elif stripped.startswith("#####"):
            html_lines.append(f"<h5>{inline_fmt(stripped[5:].strip())}</h5>")
        elif stripped.startswith("####"):
            html_lines.append(f"<h4>{inline_fmt(stripped[4:].strip())}</h4>")
        elif stripped.startswith("###"):
            html_lines.append(f"<h3>{inline_fmt(stripped[3:].strip())}</h3>")
        elif stripped.startswith("##"):
            html_lines.append(f"<h2>{inline_fmt(stripped[2:].strip())}</h2>")
        elif stripped.startswith("# "):
            html_lines.append(f"<h1>{inline_fmt(stripped[2:].strip())}</h1>")
        elif stripped.startswith("> "):
            if not in_blockquote:
                html_lines.append("<blockquote>")
                in_blockquote = True
            html_lines.append(f"<p>{inline_fmt(stripped[2:])}</p>")
        elif stripped.startswith("---"):
            html_lines.append("<hr>")
        elif stripped.startswith("- ") or stripped.startswith("* "):
            if not in_ul:
                html_lines.append("<ul>")
                in_ul = True
            html_lines.append(f"<li>{inline_fmt(stripped[2:])}</li>")
        elif re.match(r"^\d+\.\s", stripped):
            content = re.sub(r"^\d+\.\s", "", stripped)
            html_lines.append(f"<p class='numbered'>{inline_fmt(content)}</p>")
        elif stripped.startswith("!["):
            # 이미지 — base64 임베드 (네이버 블로그 복붙 호환)
            m = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", stripped)
            if m:
                alt, src = m.group(1), m.group(2)
                if not src.startswith("http"):
                    base_dir = os.path.dirname(os.path.abspath(md_path))
                    abs_src = os.path.normpath(os.path.join(base_dir, src))
                    try:
                        with open(abs_src, "rb") as img_f:
                            b64 = base64.b64encode(img_f.read()).decode()
                        src = f"data:image/png;base64,{b64}"
                    except:
                        src = "file:///" + abs_src.replace("\\", "/")
                html_lines.append(f'<div class="chart"><img src="{src}" alt="{alt}"><p class="caption">{alt}</p></div>')
            else:
                html_lines.append(f"<p>{inline_fmt(stripped)}</p>")
        else:
            if in_ul:
                html_lines.append("</ul>")
                in_ul = False
            html_lines.append(f"<p>{inline_fmt(stripped)}</p>")

    if in_table:
        html_lines.append("</table>")
    if in_blockquote:
        html_lines.append("</blockquote>")
    if in_ul:
        html_lines.append("</ul>")

    return "\n".join(html_lines)


def inline_fmt(text):
    # 볼드
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # 이탤릭
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    # 코드
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    # 링크
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


body = md_to_html(md_content)

html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>주식 블로그 리포트 — 2026.04.09 마감리뷰</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Pretendard', 'Noto Sans KR', 'Malgun Gothic', sans-serif;
    background: #ffffff;
    color: #222222;
    line-height: 1.85;
    padding: 0;
  }}
  .container {{
    max-width: 860px;
    margin: 0 auto;
    padding: 40px 24px 80px;
  }}
  h1 {{
    font-size: 1.8em;
    color: #1a1a1a;
    border-bottom: 2px solid #e74c3c;
    padding-bottom: 14px;
    margin: 40px 0 24px;
    line-height: 1.4;
  }}
  h2 {{
    font-size: 1.4em;
    color: #2c3e50;
    margin: 36px 0 14px;
    padding-left: 12px;
    border-left: 4px solid #3498db;
  }}
  h3 {{
    font-size: 1.15em;
    color: #34495e;
    margin: 24px 0 10px;
  }}
  h4 {{ font-size: 1.05em; color: #555; margin: 18px 0 8px; }}
  p {{ margin: 10px 0; color: #333; }}
  p.numbered {{
    padding-left: 20px;
    margin: 6px 0;
    position: relative;
  }}
  strong {{ color: #1a1a1a; }}
  em {{ color: #666; font-style: italic; }}
  a {{ color: #2980b9; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  hr {{
    border: none;
    border-top: 1px solid #ddd;
    margin: 32px 0;
  }}
  blockquote {{
    background: #f0f4f8;
    border-left: 4px solid #3498db;
    padding: 16px 20px;
    margin: 16px 0;
    border-radius: 0 6px 6px 0;
    font-size: 1.02em;
  }}
  blockquote p {{ color: #2c3e50; }}
  ul {{
    margin: 8px 0 8px 24px;
  }}
  li {{
    margin: 5px 0;
    color: #444;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
    font-size: 0.92em;
    background: #fff;
    border: 1px solid #ddd;
  }}
  th {{
    background: #f5f7fa;
    color: #2c3e50;
    padding: 10px 12px;
    text-align: left;
    font-weight: 600;
    border-bottom: 2px solid #ccc;
  }}
  td {{
    padding: 8px 12px;
    border-bottom: 1px solid #eee;
    color: #333;
  }}
  tr:hover td {{ background: #f9fbfd; }}
  .chart {{
    margin: 24px 0;
    text-align: center;
  }}
  .chart img {{
    max-width: 100%;
    border-radius: 6px;
    border: 1px solid #ddd;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  }}
  .chart .caption {{
    color: #888;
    font-size: 0.85em;
    margin-top: 6px;
  }}
  code {{
    background: #f0f0f0;
    color: #c0392b;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 0.9em;
  }}
  /* 상승/하락 색상 */
  td:nth-child(3), td:nth-child(4) {{
    font-weight: 600;
  }}
</style>
</head>
<body>
<div class="container">
{body}
</div>
</body>
</html>"""

html_path = md_path.replace(".md", ".html")
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"HTML 생성 완료: {html_path}")
webbrowser.open("file:///" + os.path.abspath(html_path).replace("\\", "/"))
print("브라우저에서 열었습니다.")
