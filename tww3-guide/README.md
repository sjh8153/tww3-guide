# TWW3 개인 공략 위키

ChatGPT에서 정리한 토탈 워: 워해머 3 공략 Markdown을 웹사이트로 자동 변환하는 개인 정적 위키입니다.

현재 수록 종족:

- 대 캐세이
- 브레토니아

## 핵심 구조

```text
content/        # 공략 Markdown 원본 — 여기만 고치면 됨
templates/      # HTML 템플릿
static/         # CSS / JS
deploy/         # Cloudflare Pages 전용 정적 설정
build.py        # Markdown → HTML
verify_site.py  # 결과 검증
cloudflare-build.sh
requirements.txt
docs/           # 빌드 결과물
```

## 로컬 실행

```bash
python -m pip install -r requirements.txt
python build.py
python verify_site.py
python -m http.server 8000 -d docs
```

그 뒤 `http://localhost:8000` 접속.

## Cloudflare Pages 배포 설정

GitHub 저장소를 Cloudflare Pages에 연결하고 다음 값을 사용합니다.

```text
Production branch: main
Framework preset: None
Build command: bash cloudflare-build.sh
Build output directory: docs
Root directory: 비워두기
```

GitHub의 `main` 브랜치에 변경사항이 push될 때마다 Cloudflare가 자동 배포합니다.

전체 처음 설치 절차는 [`SETUP_CLOUDFLARE.md`](SETUP_CLOUDFLARE.md)를 참고하세요.

## 공략 업데이트 원칙

`content/` 아래의 Markdown만 수정합니다.

```text
content/cathay/
content/bretonnia/
```

`docs/`는 자동 생성 결과물이므로 직접 편집하지 않습니다.

## 새 문서 / 새 종족

- 새 문서: 해당 종족 `content/<faction>/`에 `.md` 추가
- 메뉴 이름/순서: `build.py`의 `DOC_META` 수정
- 새 종족: `build.py`의 `FACTIONS` 추가 + `content/<slug>/` 폴더 생성
