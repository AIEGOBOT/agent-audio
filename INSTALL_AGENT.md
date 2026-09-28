# AI 에이전트용 설치 지침

이 문서는 Agent Audio를 설치하는 AI 코딩 에이전트를 위한 절차입니다. 사용자의 라이선스·인증 정보·시스템 변경 권한을 존중하면서, 가능한 설치 작업을 자동으로 수행하세요.

## 반드시 지킬 규칙

1. Stability AI, Gemma, Hugging Face 등 제3자 약관을 사용자를 대신해 수락하지 마세요.
2. 인증 토큰을 채팅이나 로그에 노출하지 마세요.
3. 기존 MCP 설정 전체를 교체하지 마세요. 안전하게 병합하고 변경 전 백업을 남기세요.
4. ComfyUI를 요구하거나 기존 오디오 환경으로 우회하지 마세요. 전용 런타임과 모델 경로를 사용하세요.
5. 사용자 범위의 설치를 우선하며, 꼭 필요한 경우 외에는 관리자/root 권한을 사용하지 마세요.
6. 가속 설정이 실패하면 현재 구현에서 지원되고 검증된 대체 백엔드를 사용하세요. 지원되지 않는 자동 전환을 가정하지 마세요.
7. 실제 설치된 백엔드를 보고하세요. 검증하지 않은 CUDA·XPU·Metal 가속을 사용했다고 주장하지 마세요.
8. 기존 Skill·MCP·런타임과 충돌하면 보존하고 충돌 내용을 보고하세요. 기존 디렉터리를 초기화하거나 지우지 말고, 필요한 경우 별도의 `AGENT_AUDIO_HOME`을 사용하세요.

## 1. 저장소 확인

다음 파일을 읽으세요.

- [README.md](README.md)
- [skills/audio-production/SKILL.md](skills/audio-production/SKILL.md)
- [models/registry.json](models/registry.json)
- [SECURITY.md](SECURITY.md)

## 2. 환경 조사

다음 항목을 확인하고 기록하세요.

- 운영체제, CPU 아키텍처, GPU 제조사
- NVIDIA 도구, Apple Silicon, Intel 그래픽의 존재 여부
- 설치된 에이전트 클라이언트: Codex, Claude Code, Cursor
- Python, `uv`, Git의 설치 상태
- 시스템 RAM 총량·현재 사용 가능한 메모리, 설치 대상 볼륨의 디스크 여유 공간

[용량·메모리 안내](docs/resource-requirements.md)와 비교해 부족할 수 있는 자원을 설치 전에 보고하세요. Windows CPU 구성은 디스크 여유 25GB 이상과 32GB급 RAM을 운영 권장치로 안내합니다. 이는 검증된 최소 사양이 아니므로 8GB·16GB 환경의 성공이나 실패를 단정하지 마세요. MLX에는 별도 검증이 필요합니다. 여유 공간을 확보하려고 기존 사용자 파일·모델·캐시를 임의로 삭제하지 마세요.

GPU 이름만으로 가속 지원 여부를 추정하지 마세요. 기존 Skill이나 MCP가 있어도 설치 과정에서 관련 없는 서버를 실행하지 마세요.

## 3. Python 도구 준비

MCP 애플리케이션에는 Python 3.11 이상과 `uv`를 사용합니다. 별도 오디오 런타임의 가상환경은 Python 3.12로 준비됩니다.

`uv`가 없으면 해당 운영체제의 일반적인 사용자 범위 설치 방법을 사용하세요. 관리자 권한이 필요한 패키지 관리자 작업은 실행 전에 사용자 승인을 받으세요.

저장소 루트에서 실행하세요.

```text
uv sync --frozen
```

## 4. 진단

```text
uv run --frozen python install/bootstrap.py --doctor
```

선택된 백엔드, 실제 경로, 준비 상태와 경고를 확인하세요. `--doctor`는 네트워크 없이 동작해야 합니다.

## 5. Stable Audio 런타임·모델 설치

```text
uv run --frozen python install/bootstrap.py --runtime-only
```

설치기는 Stability AI의 공식 `stable-audio-3` 런타임을 고정 커밋에서 받아 Agent Audio 전용 데이터 디렉터리에 설치합니다. 기본 경로는 `~/.agent-audio`이며 `AGENT_AUDIO_HOME`으로 변경할 수 있습니다. 모델도 고정 revision과 전용 캐시를 사용합니다.

모델 접근에 인증이나 약관 동의가 필요하면 해당 단계에서 멈추고 사용자가 직접 처리하도록 요청하세요. 사용자 처리가 완료된 뒤에만 재개하세요.

### 백엔드 선택 기준

- Apple Silicon: 공식 MLX 최적화 런타임을 선택합니다. 실제 생성 검증은 해당 하드웨어에서 별도로 수행해야 합니다.
- 그 외 환경: 공식 TFLite/LiteRT CPU 런타임을 기본으로 사용합니다.
- NVIDIA 가속: 현재 자동 선택하지 않습니다. 현재 OS에서 검증된 어댑터가 추가된 경우에만 사용하세요.
- Intel XPU: 현재 활성화되지 않았습니다. Intel 환경도 CPU 백엔드로 동작해야 합니다.

## 6. MCP와 Skill 등록

```text
uv run --frozen python install/bootstrap.py --register-only
```

탐지된 클라이언트에 다음 사용자 범위 Skill 경로를 사용합니다.

| 클라이언트 | Skill 경로 |
|---|---|
| Codex | `~/.agents/skills/audio-production/` |
| Claude Code | `~/.claude/skills/audio-production/` |
| Cursor | `~/.cursor/skills/audio-production/` |

모든 클라이언트에 저장소의 동일한 Skill 원본을 사용하세요. 클라이언트별로 내용이 다른 복사본을 관리하지 마세요.

MCP는 `agent-audio`라는 이름의 stdio 서버로 등록합니다.

- Codex·Claude Code: 기본 CLI 등록 명령을 빈 임시 설정에서 실행한 뒤 Agent Audio 항목만 실제 설정에 병합합니다.
- Cursor: `~/.cursor/mcp.json`의 기존 항목을 보존하며 병합합니다.
- Python 실행 인자는 `-I -m agent_audio.mcp_server`이며, 저장소의 전용 `.venv` 실행 파일을 사용합니다.
- 새 항목에 `AGENT_AUDIO_HOME`을 저장합니다. Codex에는 도구 제한시간 600초를 설정합니다.

일치하는 기존 등록은 중복 생성하지 마세요. 구형 등록에 `-I`가 없거나 다른 설치 경로를 가리키면 충돌로 보고됩니다. 기존 Agent Audio 항목의 내용을 먼저 검토하고 사용자 지시에 따라 전환하세요. 관련 없는 설정이나 Skill은 변경하지 마세요.

## 7. 필요할 때만 클라이언트 다시 열기

클라이언트가 새 MCP 서버나 Skill을 찾으려면 새 세션이 필요할 수 있습니다. 필요한 클라이언트만 다시 열고 관련 없는 서비스를 재시작하지 마세요.

## 8. 실제 검증

먼저 MCP의 `audio_status`를 호출해 런타임 Python과 모델 경로를 확인하세요. 그다음 짧은 오디오를 MCP의 `generate_audio`로 생성하세요.

```json
{
  "prompt": "A clean cinematic metallic impact, isolated one-shot, no music, no voice.",
  "seconds": 3
}
```

기본 출력 폴더 또는 테스트용 디렉터리의 새 경로를 사용하세요. WAV의 존재 여부, 0보다 큰 크기, 길이, 실제 저장 경로를 확인하세요. 요청이 없으면 사용자 작업 프로젝트에 테스트 오디오를 추가하지 마세요.

## 9. 완료 보고

확인한 사실만 보고하세요.

- 실제 설치·생성에 사용한 백엔드와 모델
- 런타임·Python·모델·캐시의 실제 경로와 준비 상태
- 클라이언트별 MCP·Skill 등록 결과와 Skill 설치 경로
- MCP 호출 결과, 생성 WAV 경로·크기·길이
- 사용한 대체 백엔드와 검증하지 못한 항목
- 기존 설정과의 충돌, 수동 처리가 필요한 부분

지원되지 않는 기능은 구체적으로 밝히고, 검증된 동작 경로를 유지하세요.
