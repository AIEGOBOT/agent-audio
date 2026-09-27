# Agent Audio

**AI 코딩 에이전트를 위한 독립형 로컬 오디오 생성 MCP와 Skill입니다.**

한국어 | [English](README.en.md)

Agent Audio는 Stable Audio 3를 MCP 서버로 제공하고, Codex·Claude Code·Cursor 등 MCP와 Agent Skills를 지원하는 클라이언트에 `audio-production` Skill을 설치합니다. ComfyUI, Stability Matrix, 기존 Stable Audio 환경이나 모델 폴더 없이 전용 런타임과 모델을 준비합니다.

## 에이전트에게 설치 맡기기

AI 코딩 에이전트에게 이 저장소 주소와 함께 다음을 요청하세요.

> 이 저장소를 설치해 줘. 먼저 INSTALL_AGENT.md를 읽고 지침을 따라 진행해. 현재 OS·하드웨어·Python·uv·에이전트 설치 상태를 확인하고, 전용 런타임과 모델을 설치한 다음 MCP 서버와 audio-production Skill을 등록해. 기존 설정은 보존하고, 모델 이용약관을 내 대신 수락하지 마. 마지막으로 MCP를 통해 짧은 WAV를 실제 생성해서 확인해.

설치 흐름은 다음과 같습니다.

```text
저장소 주소 전달 → INSTALL_AGENT.md 확인 → 환경 조사
→ 전용 런타임·모델 설치 → MCP·Skill 등록 → 실제 WAV 생성 검증
```

설치 후에는 효과음·음악·환경음 등 오디오가 필요한 작업을 요청할 수 있습니다. Skill은 더 큰 개발·미디어 작업에서도 오디오가 필요한 상황을 판단하도록 안내합니다.

## 현재 지원 및 검증 범위

v0.1 초기 버전이며, 기본 모델은 **Stable Audio 3 Medium**입니다.

| 환경 | 선택하는 백엔드 | 검증 상태 |
|---|---|---|
| Windows / Intel·NVIDIA 등 | TFLite / LiteRT CPU | Windows Intel 환경에서 독립 설치와 MCP를 통한 실제 생성 확인 |
| Linux 및 Apple Silicon 이외 환경 | TFLite / LiteRT CPU | 모델 없이 실행하는 CI 테스트 통과; 모든 환경의 실제 모델 생성까지 검증한 것은 아님 |
| macOS Apple Silicon | 공식 MLX 런타임 | 모델 없이 실행하는 macOS CI 테스트 통과; MLX 실제 생성은 별도 하드웨어 검증 필요 |

NVIDIA CUDA·TensorRT와 Intel XPU 가속은 자동 선택하지 않습니다. 검증된 가속 어댑터가 추가되기 전까지 해당 하드웨어에서는 CPU 백엔드를 사용합니다. MCP 도구는 특정 GPU나 게임 엔진에 종속되지 않습니다.

2026-09-27 검증에서 기존 오디오 환경을 사용하지 않고 MCP로 **3초·44.1 kHz·스테레오 WAV**를 생성했습니다. GitHub CI에서는 Windows·macOS·Linux의 5개 Python/OS 조합에서 각각 45개 테스트와 의존성 감사·CodeQL 검사가 통과했습니다.

## 직접 설치하기

Git, Python 3.11 이상, `uv`가 필요합니다. MCP 애플리케이션과 별도로 설치되는 오디오 런타임은 Python 3.12를 사용합니다. 모델 다운로드를 위한 네트워크와 디스크 공간을 준비하세요.

```bash
git clone https://github.com/AIEGOBOT/agent-audio.git
cd agent-audio
uv sync --frozen
uv run --frozen python install/bootstrap.py --doctor
```

진단 결과를 확인한 뒤 런타임·모델을 설치하고 MCP·Skill을 등록합니다.

```bash
uv run --frozen python install/bootstrap.py --runtime-only
uv run --frozen python install/bootstrap.py --register-only
```

두 단계를 한 번에 실행하려면 다음 명령을 사용합니다.

```bash
uv run --frozen python install/bootstrap.py
```

이미 런타임이 준비되어 있다면 `--register-only`로 등록만 진행할 수 있습니다. 새 MCP나 Skill을 찾지 못하는 클라이언트는 관련 세션을 다시 여세요. 이용약관 동의나 인증이 필요한 경우 사용자가 직접 완료해야 합니다.

### 설치 경로와 기존 설정 보존

| 항목 | 기본 경로 |
|---|---|
| MCP Python | 저장소의 `.venv/` |
| Stable Audio 런타임 | `~/.agent-audio/runtime/stable-audio-3/` |
| 런타임 Python | 위 경로의 `optimized/<backend>/.venv/` |
| 모델 | 위 경로의 `optimized/<backend>/models/` |
| Hugging Face 캐시 | `~/.agent-audio/cache/huggingface/` |
| 기본 WAV 출력 | `~/.agent-audio/output/` |
| Codex Skill | `~/.agents/skills/audio-production/` |
| Claude Code Skill | `~/.claude/skills/audio-production/` |
| Cursor Skill | `~/.cursor/skills/audio-production/` |

`~`는 현재 사용자 홈 폴더입니다. 설치 전에 `AGENT_AUDIO_HOME`을 지정하면 런타임·모델·캐시·기본 출력의 루트 경로를 분리할 수 있습니다. 새 MCP 등록에도 이 경로를 저장합니다.

기존 Skill 내용이나 같은 이름의 MCP 설정이 다르면 덮어쓰지 않고 충돌을 보고합니다. Python `-I` 옵션이 없는 구형 MCP 항목도 검토 후 전환해야 합니다. 자세한 동작과 제약은 [보안 안내](SECURITY.md)를 확인하세요.

## MCP 도구

| 도구 | 기능 |
|---|---|
| `audio_status` | OS·하드웨어·선택 백엔드·런타임 준비 상태·실제 Python 및 모델 경로 확인 |
| `generate_audio` | 프롬프트와 길이를 받아 선택된 백엔드로 WAV 생성 |

3초 효과음 생성 요청 예시입니다.

```json
{
  "prompt": "Heavy cinematic metallic robot impact, dense mechanical body, sharp transient, subtle electrical crackle, isolated sound effect, no voice, no music",
  "seconds": 3
}
```

`output_path`를 생략하면 기본 출력 폴더에 고유한 이름으로 저장합니다. 직접 지정할 때는 아직 존재하지 않는 `.wav` 경로를 사용하세요. 길이는 0초 초과 380초 이하이며, 긴 CPU 생성은 540초 실행 제한에 도달할 수 있습니다. 출력 파일시스템은 하드링크를 지원해야 합니다.

게임·영상·애플리케이션·웹사이트·광고 등에서 같은 MCP 도구를 사용할 수 있습니다. 모델 자체의 전체 기능이 이 두 도구로 모두 제공되는 것은 아닙니다.

## 개발 및 검증

저장소 루트에서 다음 검사를 실행합니다. 단위 테스트에는 모델 가중치가 필요하지 않습니다.

```bash
uv run --frozen ruff check src install tests
uv run --frozen ruff format --check src install tests
uv run --frozen python -m compileall -q src install
uv run --frozen pytest -q
uv run --frozen python install/bootstrap.py --doctor
```

`--doctor`는 네트워크 없이 동작합니다. 실제 모델 설치·생성 검증과 모델 없는 단위 테스트 결과는 구분해서 보고해야 합니다.

## 문서와 구성

- [에이전트 설치 지침](INSTALL_AGENT.md): 환경 조사부터 실제 생성 검증까지의 순서
- [저장소 작업 지침](AGENTS.md): 구조 원칙과 변경 후 필수 검사
- [보안 안내](SECURITY.md): 설정 보존, 실행 격리, 제한사항
- [제3자 고지](THIRD_PARTY_NOTICES.md): 모델·런타임의 별도 이용약관

```text
agent-audio/
├─ INSTALL_AGENT.md
├─ AGENTS.md
├─ SECURITY.md
├─ skills/audio-production/
├─ src/agent_audio/
├─ install/bootstrap.py
├─ models/registry.json
├─ tests/
└─ .github/workflows/
```

## 라이선스

Agent Audio 소스 코드는 [MIT 라이선스](LICENSE)를 따릅니다. 모델 가중치는 저장소에 포함하지 않습니다. Stable Audio 3와 T5Gemma 등 제3자 모델·런타임에는 각각의 이용약관이 적용되며, 설치기는 사용자를 대신해 약관을 수락하지 않습니다. 자세한 내용은 [제3자 고지](THIRD_PARTY_NOTICES.md)를 확인하세요.
