"""Blogger API v3 자동 포스팅
- 첫 실행: 브라우저 OAuth 동의 → token.json 자동 저장
- 이후: 토큰 갱신으로 무한 자동 발행
- 차트 이미지: GitHub raw URL로 자동 치환 (repo의 main 브랜치에 push 되어 있어야 함)
"""
import os, sys, re, argparse
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/blogger']
DEFAULT_REPO = 'peterkim-dot/sto_blg'
DEFAULT_BRANCH = 'main'


def get_service():
    """OAuth 인증 → Blogger API 서비스 객체 반환"""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                sys.exit("❌ credentials.json 파일이 필요합니다. README 참고하여 Google Cloud에서 받아주세요.")
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w', encoding='utf-8') as f:
            f.write(creds.to_json())
        print("✅ token.json 저장 완료 (다음부턴 자동 인증)")

    return build('blogger', 'v3', credentials=creds)


def list_blogs():
    """본인의 블로그 목록과 ID 출력"""
    service = get_service()
    blogs = service.blogs().listByUser(userId='self').execute()
    print("\n📚 사용자 블로그 목록:")
    for b in blogs.get('items', []):
        print(f"  Blog ID: {b['id']}")
        print(f"  이름: {b['name']}")
        print(f"  URL: {b['url']}")
        print()
    return blogs


def transform_image_paths(html, date_str, repo, branch):
    """charts/xxx.png → https://raw.githubusercontent.com/{repo}/{branch}/output/{date}/charts/xxx.png"""
    base = f'https://raw.githubusercontent.com/{repo}/{branch}/output/{date_str}/charts/'
    return re.sub(
        r'src="charts/([^"]+)"',
        lambda m: f'src="{base}{m.group(1)}"',
        html,
    )


def extract_title(html):
    """<title>...</title> 추출"""
    m = re.search(r'<title>([^<]+)</title>', html)
    return m.group(1).strip() if m else '제목 없음'


def extract_body_with_style(html):
    """<style>...</style> + <body> 안의 내용을 합쳐서 반환 (Blogger는 head를 제거하므로)"""
    style_match = re.search(r'<style[^>]*>(.*?)</style>', html, re.DOTALL)
    body_match = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL)
    style = style_match.group(0) if style_match else ''
    body = body_match.group(1).strip() if body_match else html
    return style + '\n' + body


def post_to_blogger(blog_id, html_path, date_str=None, repo=DEFAULT_REPO,
                    branch=DEFAULT_BRANCH, draft=False, labels=None):
    html_file = Path(html_path)
    if not html_file.exists():
        sys.exit(f'❌ 파일 없음: {html_path}')

    if date_str is None:
        date_str = html_file.parent.name  # 부모 폴더 이름이 날짜 (예: 20260423)

    html = html_file.read_text(encoding='utf-8')
    html = transform_image_paths(html, date_str, repo, branch)
    title = extract_title(html)
    content = extract_body_with_style(html)

    service = get_service()
    post = {
        'kind': 'blogger#post',
        'title': title,
        'content': content,
    }
    if labels:
        post['labels'] = labels

    print(f"\n📤 Blogger 포스팅 중...")
    print(f"  제목: {title}")
    print(f"  HTML: {html_path}")
    print(f"  이미지 호스팅: github.com/{repo}@{branch}")
    print(f"  draft: {draft}, labels: {labels or '없음'}")

    result = service.posts().insert(
        blogId=blog_id, body=post, isDraft=draft,
    ).execute()

    print(f"\n✅ {'임시저장' if draft else '발행'} 완료!")
    print(f"   포스트 ID: {result['id']}")
    if not draft:
        print(f"   URL: {result.get('url', '(URL 미반환)')}")
    else:
        print(f"   임시저장 → Blogger 관리자 페이지에서 확인 후 발행")
    return result


def main():
    p = argparse.ArgumentParser(description='Blogger 자동 포스팅')
    sub = p.add_subparsers(dest='command', required=True)

    sub.add_parser('list', help='본인의 블로그 목록 조회')

    p_post = sub.add_parser('post', help='블로그에 글 발행')
    p_post.add_argument('--blog-id', required=True, help='Blogger Blog ID')
    p_post.add_argument('--html', required=True, help='HTML 파일 경로')
    p_post.add_argument('--date', help='날짜 (예: 20260423). 미지정 시 부모 폴더명 사용')
    p_post.add_argument('--repo', default=DEFAULT_REPO, help=f'GitHub repo (default: {DEFAULT_REPO})')
    p_post.add_argument('--branch', default=DEFAULT_BRANCH, help=f'Branch (default: {DEFAULT_BRANCH})')
    p_post.add_argument('--draft', action='store_true', help='임시저장 (발행하지 않음)')
    p_post.add_argument('--labels', nargs='*', help='라벨 목록 (예: --labels 마감리뷰 주식)')

    args = p.parse_args()

    if args.command == 'list':
        list_blogs()
    elif args.command == 'post':
        post_to_blogger(
            args.blog_id, args.html, args.date,
            args.repo, args.branch, args.draft, args.labels,
        )


if __name__ == '__main__':
    main()
