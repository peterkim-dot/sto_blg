# Blogger 자동 포스팅 셋업 가이드

## 1. Google Cloud 프로젝트 + OAuth 클라이언트 (10분, 1회만)

### 1-1. 프로젝트 생성 + Blogger API 활성화

1. https://console.cloud.google.com 접속 (Google 계정 로그인)
2. 상단 프로젝트 선택 드롭다운 → **새 프로젝트** → 이름 `stock-blog-poster` → 만들기
3. 좌측 햄버거 메뉴 → **API 및 서비스 > 라이브러리**
4. 검색창에 `Blogger API v3` → 클릭 → **사용 설정**

### 1-2. OAuth 동의 화면 구성

1. **API 및 서비스 > OAuth 동의 화면**
2. User Type: **외부** 선택 → 만들기
3. 앱 정보 입력:
   - 앱 이름: `stock-blog-poster`
   - 사용자 지원 이메일: 본인 Gmail
   - 개발자 연락처: 본인 Gmail
4. **저장 후 계속**
5. 범위(Scopes) 단계: **저장 후 계속** (이 단계에선 추가 안 해도 됨, 클라이언트가 요청)
6. 테스트 사용자: 본인 Gmail 추가 → **저장 후 계속**

### 1-3. OAuth 2.0 클라이언트 ID 발급

1. **API 및 서비스 > 사용자 인증 정보** → **사용자 인증 정보 만들기 > OAuth 클라이언트 ID**
2. 애플리케이션 유형: **데스크톱 앱**
3. 이름: `stock-blog-poster-cli`
4. 만들기 → **JSON 다운로드**
5. 다운로드된 파일을 **`credentials.json`** 으로 이름 변경 후 이 프로젝트 폴더 (`stock-blog-agent`)에 복사

> ⚠️ `credentials.json` 은 비밀 파일입니다. 이미 `.gitignore`에 추가되어 있는지 확인하세요.

---

## 2. Blog ID 확인

1. https://www.blogger.com 로그인
2. 본인 블로그 선택
3. 주소창의 URL: `https://www.blogger.com/blog/posts/`**`1234567890123456789`**
4. 마지막 숫자가 **Blog ID**

또는 스크립트로 확인 가능:
```bash
.venv/Scripts/python.exe post_to_blogger.py list
```
(첫 실행 시 브라우저가 열리며 OAuth 동의 절차)

---

## 3. 첫 발행 테스트

### 3-1. 차트 이미지가 GitHub에 push 되어 있는지 확인

원격 트리거가 아니라 로컬에서 작업했을 경우, output 폴더를 GitHub에 push:
```bash
git add output/
git commit -m "publish 4/23 blog"
git push
```

### 3-2. 임시저장 (draft)으로 안전하게 테스트

```bash
.venv/Scripts/python.exe post_to_blogger.py post \
  --blog-id YOUR_BLOG_ID \
  --html "output/20260423/20260423_마감리뷰.html" \
  --draft
```

→ 첫 실행 시 브라우저 OAuth 동의 → `token.json` 자동 저장 → Blogger 관리자 페이지 "임시저장" 탭에서 확인.

### 3-3. 정식 발행

```bash
.venv/Scripts/python.exe post_to_blogger.py post \
  --blog-id YOUR_BLOG_ID \
  --html "output/20260423/20260423_마감리뷰.html" \
  --labels 마감리뷰 주식 코스피
```

성공 시 글 URL이 출력됩니다.

---

## 4. 명령어 요약

```bash
# 블로그 목록 + Blog ID 확인
.venv/Scripts/python.exe post_to_blogger.py list

# 임시저장 (테스트)
.venv/Scripts/python.exe post_to_blogger.py post --blog-id BLOG_ID --html PATH --draft

# 정식 발행 (라벨 포함)
.venv/Scripts/python.exe post_to_blogger.py post \
  --blog-id BLOG_ID \
  --html "output/20260423/20260423_마감리뷰.html" \
  --labels 마감리뷰 주식 코스피

# 다른 GitHub repo 사용 시
.venv/Scripts/python.exe post_to_blogger.py post \
  --blog-id BLOG_ID --html PATH \
  --repo other-user/other-repo --branch main
```

---

## 5. 트러블슈팅

| 증상 | 원인 / 해결 |
|---|---|
| `credentials.json 파일이 필요합니다` | 1-3 단계 완료 후 파일 복사 |
| `Access blocked: stock-blog-poster has not completed verification` | OAuth 동의 화면에서 본인을 테스트 사용자로 추가 |
| 차트 이미지 X 표시 | output 폴더가 GitHub에 push 안 됐거나 raw URL 잘못. `--repo --branch` 확인 |
| 첫 발행만 잘 되고 다음부터 401 | `token.json` 삭제 후 재인증 |
| 디자인이 깨져 보임 | Blogger 테마와 충돌. Blogger 관리 > 테마 > "테마 사용자 정의" 보존 옵션 확인 |

---

## 6. 자동화 흐름

```
[로컬 PC, 매일 18:30 KST]
1. python fetch_for_claude.py
2. python compute_indicators.py
3. python gen_charts_for_blog.py
4. python gen_sector_news.py
5. (Claude/사람이 블로그 HTML 작성)
6. git add output/ && git commit && git push
7. python post_to_blogger.py post --blog-id ... --html ... --labels ...
```

5단계까지 자동, 6~7단계도 .bat 파일로 묶으면 완전 자동화됩니다.
