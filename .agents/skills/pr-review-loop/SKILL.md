---
name: pr-review-loop
description: PR 리뷰 루프를 끝까지 굴릴 때 사용합니다. Codex/Claude/GitHub 리뷰 확인, 리뷰 없을 때 멘션, 최신 head 기준 리뷰 판정, 실제로 필요한 수정만 반영, 검증/커밋/푸시/재리뷰 요청, clean review·PR 종료·사용자 판단 필요 시 루프 종료까지 처리합니다. 사용자가 "계속 확인", "5분마다", "자동화", "다시 말 안 해도", "리뷰 달리면 알아서"처럼 반복 확인을 원하면 각 에이전트의 heartbeat/loop 수단으로 자동화를 반드시 생성합니다.
---

# PR Review Loop

이 스킬은 PR 리뷰를 "확인 → 판단 → 필요한 수정 → 검증 → 커밋/푸시 → 재리뷰 요청 → 종료"까지 닫는 데 사용합니다.

목표는 리뷰어 의견을 무조건 따르는 것이 아닙니다.
목표는 현재 프로젝트 맥락에 맞게 리뷰를 분류하고, 진짜 필요한 것만 고쳐서 PR을 안정적으로 마무리하는 것입니다.

## 에이전트별 반복 확인(heartbeat/loop) 수단

이 스킬의 분류·정지·판정 규칙은 도구와 무관하게 동일합니다. 반복 확인 자동화를 만드는 "수단"만 에이전트별로 다릅니다.

- **Claude Code**: `/loop`(주기 실행) 또는 `ScheduleWakeup`(다음 확인 예약)으로 heartbeat를 만듭니다. 폴링에는 항상 캡을 둡니다(무한 금지).
- **Codex**: `codex_app.automation_update`로 heartbeat 자동화를 생성합니다.
- **Google Antigravity**: 예약/재실행 수단이 있으면 그것으로, 없으면 명시형 workflow로 사용자가 주기적으로 재실행합니다.

프로젝트에서 자동 리뷰 누락·오판 같은 교훈이 쌓이면 `docs/lessons.md`에 남겨 다음 세션이 재사용하게 합니다.

## 가장 중요한 구분: 스킬 사용과 자동화 생성은 다릅니다

이 스킬을 읽거나 사용했다고 해서 자동으로 주기 확인이 생기지 않습니다.

사용자가 반복 확인을 원하면, 답변을 끝내기 전에 반드시 위의 에이전트별 수단으로 heartbeat/loop 자동화를 생성합니다.

특히 아래 상황에서는 자동화 생성이 필수입니다.

- PR에 `@codex review`(또는 해당 리뷰어 멘션)를 새로 남긴 뒤 리뷰 답변을 기다려야 하는 경우
- 리뷰 반영 commit/push 후 최신 head에 대한 clean review가 아직 없는 경우
- 사용자가 이 스킬을 호출하면서 자동화/루프/계속 확인을 기대한다고 말한 경우
- 사용자가 "왜 heartbeat/자동화가 안 됐지?"라고 지적한 경우

이 경우에는 "이번 리뷰만 조치했다"고 생각하고 끝내지 말고, clean review 또는 stop condition이 확인될 때까지 주기 확인을 유지합니다.

반복 확인 의도로 봐야 하는 표현:

- `자동화 만들어줘`
- `5분마다 확인`
- `5분 뒤에 다시 확인`
- `계속 체크`
- `리뷰 달리면 알아서 처리`
- `내가 다시 말 안 해도`
- `예약해줘`
- `heartbeat`
- `루프 자동화`
- `PR 리뷰 자동 확인`
- `왜 자동화가 안 되어 있지?`
- `Codex 리뷰 달리면 확인하고 조치해줘`

기본 주기 설정(권장):

- 주기: 5분 간격 (Codex `rrule=FREQ=MINUTELY;INTERVAL=5`, Claude Code `/loop 5m` 등)
- 자동화/루프 이름에는 프로젝트/PR 번호를 포함합니다.
- 자동화/루프 prompt에는 반드시 대상 PR URL, repo path, `$pr-review-loop` 사용 지시를 넣습니다.
- Claude Code 폴링은 반드시 최대 반복 횟수/시간 캡을 둡니다.

반대로 아래처럼 명확한 1회성 요청이고, 새 리뷰 요청을 남기지 않았으며, 사용자가 반복 확인을 기대하지 않는 경우에는 자동화를 만들지 않습니다.

- `리뷰 확인해줘`
- `Codex가 리뷰 달았는지 봐줘`
- `PR 상태 한 번만 알려줘`

주의: `이번 리뷰만 조치해줘`처럼 보이는 요청이라도, 조치 후 `@codex review`를 남겼다면 이제 "리뷰 응답 대기" 상태입니다. 이때 사용자가 `$pr-review-loop`를 호출했거나 자동화를 기대하는 맥락이면 자동화를 생성합니다.

단, 사용자가 "왜 5분 뒤 체크 자동화가 안 됐냐"처럼 말하면 이전 요청이 애매했더라도 반복 확인 의도로 보고 자동화를 생성합니다.

이미 heartbeat/loop 안에서 실행 중이면 새 자동화를 만들지 않습니다. 현재 루프를 계속 진행하고, 종료 조건을 만족하면 현재 자동화를 삭제(또는 중단)합니다.

## 입력으로 받을 수 있는 PR 정보

다음 중 하나로 PR을 찾습니다.

- 명시된 PR URL 또는 PR 번호
- 현재 git branch에 연결된 PR
- 현재 thread에서 최근에 작업하던 PR
- repo/branch/base 정보

여러 후보가 있으면 사용자가 명시한 PR을 우선합니다.
확실한 후보가 없으면 오래 추측하지 말고 "적절한 PR을 찾지 못했다"고 보고합니다. 자동화 실행 중이면 자동화를 삭제(또는 중단)합니다.

## 작업 절차

### 1. 로컬/원격 상태 확인

- repo에서 `git status --short --branch`를 실행합니다.
- `gh pr view` 또는 GitHub connector로 PR을 확인합니다.
- head commit, base branch, PR state, draft 여부, merge 여부를 기록합니다.

### 2. 루프 대상이 아니면 즉시 중단

다음이면 코드를 수정하지 않습니다.

- PR을 찾을 수 없음
- PR이 closed/merged
- PR head/base가 현재 작업 맥락과 다름
- 리뷰 루프 대상 PR이 아님
- 사용자 판단이 필요한 정책/제품 결정만 남음

자동화 실행 중이면, 일시적 GitHub/network/auth 문제가 아닌 한 자동화를 삭제(또는 중단)하고 이유를 보고합니다.

### 3. 최신 head commit 기준 clean review 확인

`Codex Review: Didn't find any major issues` 같은 clean review는 반드시 현재 PR head commit을 대상으로 한 것인지 확인합니다.

> ⚠️ **두 곳을 모두 본다 (중요).** Codex는 **지적이 있을 때만** 정식 review(`GET /repos/{o}/{r}/pulls/{n}/reviews`, inline 코멘트 포함)로 답니다. **지적이 없으면(clean)** "Codex Review: Didn't find any major issues"를 **PR 일반 코멘트**(`GET /repos/{o}/{r}/issues/{n}/comments`)로 답니다 — `/reviews`엔 아무것도 안 생깁니다. 그래서 `/pulls/N/reviews`만 확인하면 clean 리뷰를 놓쳐 "리뷰 안 붙음(flaky)"으로 오판합니다. 반드시:
> - **clean 판정**: `/issues/N/comments`에서 `chatgpt-codex-connector[bot]`의 "Didn't find any major issues" 코멘트를 찾고, 그 본문의 `Reviewed commit: <sha>`가 현재 head와 같은지 확인.
> - **지적 판정**: `/pulls/N/reviews`(+ `/pulls/N/comments` inline)에서 현재 head 커밋(`commit_id`)의 미해결 지적을 확인.
> - 둘 다 없으면 진짜 미도착 → 4번(멘션)으로.

- 최신 head에 대한 clean review가 있으면 수정하지 않습니다.
- 자동화 실행 중이면 자동화를 삭제(또는 중단)하고 루프 완료를 보고합니다.

### 4. 리뷰가 없으면 요청하되, 멘션을 반복 스팸하지 않기

최신 head에 대한 리뷰가 없고 최근 요청도 없으면 다음처럼 comment합니다.

```text
@codex review
```

이미 방금 요청했거나 리뷰어가 반응했지만 아직 답변이 없으면, 다음 주기 확인까지 기다립니다.

### 5. 리뷰 thread를 정확히 읽기

GitHub inline review는 flat comment만 보면 빠질 수 있습니다.

- 가능하면 inline 리뷰까지 정확히 읽는 도구(전용 스킬 또는 GraphQL script)를 사용합니다.
- unresolved / resolved / outdated / flat conversation comment를 구분합니다.
- PR conversation comment만 보고 전체 리뷰 상태라고 판단하지 않습니다.

### 6. 리뷰 항목 분류

각 리뷰를 다음 중 하나로 분류합니다.

- `actionable`: 실제 버그, 권한/인증 우회, 상태 전이 오류, validation 누락, 빌드 실패, 명확한 UI 회귀, 작은 gate/notice 누락
- `already-addressed`: 이후 commit에서 이미 고쳐졌거나 중복
- `outdated`: 오래된 diff에 달렸고 현재 코드에는 적용 안 됨
- `not-accepted`: 기술적으로 가능하지만 사용자 결정, 회의 결론, 제품 정책, 의도적 단순화와 충돌
- `needs-user-decision`: 제품 정책, DB schema, 보안/스토리지 정책, migration, role model, 데이터 삭제 정책, 큰 디자인 선택이 필요함

### 7. `actionable`만 수정

- 수정은 최소 범위로 합니다.
- 현재 사용자/회의 결정이 리뷰어 추정보다 우선입니다.
- 새 기능, 큰 리팩터, schema/보안/스토리지 정책 변경은 사용자가 명시적으로 승인하지 않으면 하지 않습니다.
- 남은 항목이 `not-accepted`, `outdated`, `needs-user-decision`뿐이면 코드를 수정하지 않습니다.

### 8. 수정 후 검증

프로젝트의 검증 명령을 사용합니다. 예:

```text
git diff --check
# 프론트엔드 예: npm run lint / npm run build
# 그 외: 해당 프로젝트의 lint / test / build 명령
```

렌더링, auth, upload/download, data flow가 바뀌었으면 브라우저 smoke 또는 백엔드 smoke도 수행합니다.

### 9. 커밋/푸시/재리뷰 요청

- 커밋 메시지는 각 repo의 컨벤션을 따릅니다. 이 템플릿은 한국어 커밋 메시지를 기본 권장합니다(언어 규칙). Conventional Commits(`fix`/`feat`/`docs`/`chore` + scope)를 쓰는 repo면 그 컨벤션을 따릅니다.
- 의미 있는 새 head commit이 생긴 뒤에만 `@codex review`를 다시 요청합니다.

### 10. 결과 보고

보고에는 다음을 포함합니다.

- PR URL
- 최신 head commit
- 수정/스킵한 리뷰 항목
- 실행한 검증
- heartbeat/loop 자동화 생성/유지/삭제 여부

## 루프 실행 중 종료 규칙

heartbeat/loop 안에서 이 스킬이 실행 중일 때:

- 최신 head clean review 확인 → 자동화 삭제(또는 중단)
- PR closed/merged → 자동화 삭제(또는 중단)
- 적절한 PR 없음 → 자동화 삭제(또는 중단)
- 리뷰 루프 대상이 아님 → 자동화 삭제(또는 중단)
- 사용자 판단 필요 항목만 남음 → 수정 중단, 사용자에게 보고, 자동화 삭제(또는 중단)
- GitHub/network/auth 일시 오류 → 자동화를 유지하고 조용히 다음 실행에서 재시도

## 리뷰어 판단 원칙

리뷰어 의견은 명령이 아니라 신호입니다.

- concrete defect를 잡은 리뷰는 우선 반영합니다.
- 사용자 결정/회의 결론과 충돌하는 리뷰는 그대로 따르지 않습니다.
- 사용자가 제거하라고 한 UI를 리뷰 때문에 되살리지 않습니다.
- GitHub review thread resolve/reply는 사용자가 명시적으로 요청하지 않으면 하지 않습니다.

## 자동화 prompt 템플릿

PR 리뷰 루프 자동화를 만들 때는 아래 템플릿을 사용합니다. (Codex는 heartbeat automation, Claude Code는 `/loop`/`ScheduleWakeup` prompt로 사용)

```text
Use $pr-review-loop for this PR review loop.

Target PR: <PR URL or current branch PR>
Repo: <absolute repo path>

Keep checking the latest head commit. If review is missing, request it without spamming repeated mentions. If review feedback is actionable, judge it against the current project context, fix minimally, validate with `git diff --check`, project lint/build checks, then commit, push, and request review again. If Codex/Claude reports no major issues for the latest head commit, or if no suitable PR exists, the PR is closed/merged, or only user-decision items remain, delete/stop this automation and report why.
```

권장 생성값 (Codex heartbeat 기준):

- `kind=heartbeat`
- `destination=thread`
- `rrule=FREQ=MINUTELY;INTERVAL=5`
- `status=ACTIVE`

Claude Code에서는 위 prompt를 `/loop 5m`의 작업 지시로 쓰거나, 한 번의 확인 뒤 `ScheduleWakeup`으로 다음 확인을 예약합니다. 어느 경우든 최대 반복 캡을 함께 둡니다.
