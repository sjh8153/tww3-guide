# TWW3 공략 위키 — GitHub + Cloudflare Pages 배포 가이드

이 프로젝트는 `content/**/*.md`를 원본으로 사용하고, Cloudflare Pages가 GitHub 변경사항을 감지해 자동으로 사이트를 다시 빌드하도록 구성합니다.

## 최종 구조

```text
ChatGPT에서 공략 수정
        ↓
GitHub 저장소의 content/**/*.md 변경
        ↓
Cloudflare Pages 자동 빌드
        ↓
https://<프로젝트명>.pages.dev
또는 사용자 지정 도메인
```

## 0. 준비물

- GitHub 계정
- Cloudflare 계정
- 이 프로젝트 폴더 전체

## 1. GitHub 저장소 만들기

GitHub에서 새 저장소를 만듭니다.

권장값:

- Repository name: `tww3-guide`
- Visibility: Public
- README / .gitignore / License 자동 생성: 체크하지 않기

빈 저장소를 만든 뒤 주소를 복사합니다.

예시:

```text
https://github.com/<사용자명>/tww3-guide.git
```

## 2. 프로젝트를 GitHub에 올리기

프로젝트 폴더에서 터미널을 열고 다음을 실행합니다.

```bash
git init
git add .
git commit -m "Initial TWW3 guide site"
git branch -M main
git remote add origin https://github.com/<사용자명>/tww3-guide.git
git push -u origin main
```

이미 Git 저장소인 경우 `git init`은 생략합니다.

## 3. Cloudflare Pages와 GitHub 연결

Cloudflare 대시보드에서:

1. **Workers & Pages** 이동
2. **Create application** 선택
3. **Pages** 탭 선택
4. **Import an existing Git repository** 선택
5. GitHub 연결 및 `tww3-guide` 저장소 선택
6. **Begin setup**

빌드 설정은 아래처럼 입력합니다.

```text
Production branch: main
Framework preset: None
Build command: bash cloudflare-build.sh
Build output directory: docs
Root directory: 비워두기
```

`cloudflare-build.sh`가 의존성 설치 → 사이트 빌드 → 결과 검증까지 한 번에 수행합니다.

첫 배포에 성공하면 아래와 비슷한 주소가 생깁니다.

```text
https://tww3-guide.pages.dev
```

프로젝트명이 이미 사용 중이면 Cloudflare가 다른 이름을 요구할 수 있습니다.

## 4. 이후 업데이트 방법

평소에는 `docs/`를 직접 수정하지 않습니다.

수정 대상은:

```text
content/cathay/*.md
content/bretonnia/*.md
```

입니다.

수정 후 직접 올릴 때는:

```bash
python build.py
python verify_site.py
git add .
git commit -m "Update Bretonnia cavalry guide"
git push
```

하지만 Cloudflare가 빌드를 담당하므로 `docs/`를 로컬에서 미리 빌드하지 않아도 됩니다. GitHub에 Markdown과 빌드 코드가 올라가면 Cloudflare에서 `cloudflare-build.sh`를 실행합니다.

즉 가장 단순한 갱신은:

```bash
git add .
git commit -m "Update guides"
git push
```

입니다.

## 5. ChatGPT에서 갱신하는 흐름

GitHub 저장소가 ChatGPT의 GitHub 연결에서 접근 가능해진 뒤에는 이 프로젝트 채팅에서 예를 들어:

```text
브레토니아 기병 공략 최신화해줘. 사이트 소스에도 반영해줘.
```

라고 요청합니다.

목표 워크플로는:

1. 최신 정보 확인
2. 해당 `content/**/*.md` 수정
3. GitHub 반영
4. Cloudflare 자동 배포

입니다.

Cloudflare 대시보드를 매번 열 필요는 없습니다.

## 6. 새 문서 추가

예를 들어 브레토니아 연구 문서를 추가하려면:

```text
content/bretonnia/bretonnia_research.md
```

를 만듭니다.

메뉴 이름과 정렬 순서를 원하는 대로 지정하려면 `build.py`의 `DOC_META`에 항목을 추가합니다.

```python
'bretonnia_research.md': ('연구', '연구 우선순위와 상황별 선택', 60),
```

그 뒤 GitHub에 push하면 Cloudflare가 자동으로 다시 배포합니다.

## 7. 새 종족 추가

예를 들어 제국을 추가한다면:

```text
content/empire/
```

폴더를 만들고 `build.py`의 `FACTIONS`에 종족 정보를 추가합니다.

```python
'empire': {
    'name': '제국',
    'short': '제국',
    'icon': '⚔',
    'tagline': '제병협동 · 화약 · 포병',
    'accent': '#c9a75d'
},
```

그리고 `DOC_META`에 문서 메뉴 정보를 추가합니다.

## 8. 사용자 지정 도메인 연결

`*.pages.dev` 주소만 써도 아무 문제가 없습니다.

개인 도메인을 붙이고 싶다면 Cloudflare Pages 프로젝트에서:

1. **Custom domains**
2. **Set up a domain**
3. 원하는 도메인 입력
4. 안내에 따라 DNS 연결

예시:

```text
tww3.example.com
```

## 9. 로컬 미리보기

Python 3이 설치돼 있다면:

```bash
python -m pip install -r requirements.txt
python build.py
python verify_site.py
python -m http.server 8000 -d docs
```

브라우저에서:

```text
http://localhost:8000
```

으로 접속합니다.

## 10. 파일 역할

```text
content/                공략 Markdown 원본 — 가장 중요
templates/              HTML 템플릿
static/                 CSS / JavaScript 원본
deploy/_headers         Cloudflare Pages 응답 헤더
build.py                Markdown → 정적 사이트 빌더
cloudflare-build.sh     Cloudflare용 전체 빌드 명령
verify_site.py          배포 전 결과 검증
requirements.txt        Python 패키지 버전 고정
.python-version         Cloudflare/Python 버전 고정
docs/                   생성된 정적 사이트
```

## 핵심 원칙

**`content/`가 진짜 원본이고 `docs/`는 결과물입니다.**

공략 수정할 때 `docs/articles/*.html`을 직접 고치면 다음 빌드 때 날아갑니다.
