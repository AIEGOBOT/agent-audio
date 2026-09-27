# 저장소 작업 지침

Agent Audio는 특정 에이전트·모델·하드웨어·사용 목적에 종속되지 않는 구조를 지향합니다.

## 구조와 작업 원칙

- MCP 도구를 범용으로 유지하세요. 코어 프로토콜에 특정 게임 엔진용 인자를 추가하지 마세요.
- Stable Audio 구현 세부사항은 백엔드·런타임 모듈 안에 두세요.
- 새 하드웨어 지원은 여러 곳에 조건문을 흩뜨리지 말고 백엔드 어댑터로 추가하세요.
- 제3자 모델 가중치를 저장소에 포함하지 마세요.
- 접근 제한 모델의 라이선스 또는 인증 절차를 우회하지 마세요.
- 검증하지 않은 가속 지원을 주장하지 말고 검증된 대체 백엔드를 사용하세요.
- 설치기 변경 시 Windows·macOS·Linux 동작을 함께 고려하세요.
- Skill은 가능한 한 공개 Agent Skills의 `SKILL.md` 형식을 따르세요.
- GitHub의 기본 사용자 문서는 한국어로 작성하세요. 영어 안내는 `README.en.md`에 유지하고, 명령어·경로·API 식별자는 번역하지 마세요.
- 기존 사용자 설정·Skill·모델·런타임은 보존하세요. 충돌 처리와 보안 경계는 [SECURITY.md](SECURITY.md)를 따르세요.

## 주요 파일

- [INSTALL_AGENT.md](INSTALL_AGENT.md): 에이전트의 설치·등록·실제 생성 검증 절차
- `src/agent_audio/installer.py`: Skill 설치와 클라이언트 설정 병합
- `src/agent_audio/runtime.py`, `src/agent_audio/download_models.py`: 전용 런타임과 모델 준비
- `src/agent_audio/mcp_server.py`: MCP 도구
- `src/agent_audio/storage.py`, `src/agent_audio/process.py`: 파일 보존과 추론 프로세스 제어
- `tests/`: 모델 가중치 없이 실행하는 회귀 테스트

## 설치기 변경 완료 조건

저장소 루트에서 실행하세요.

```text
uv sync --frozen
uv run --frozen ruff check src install tests
uv run --frozen ruff format --check src install tests
uv run --frozen python -m compileall -q src install
uv run --frozen pytest -q
uv run --frozen python install/bootstrap.py --doctor
```

- 컴파일·정적 검사와 단위 테스트가 통과해야 합니다.
- 단위 테스트는 모델 가중치를 요구하지 않아야 합니다.
- `--doctor`는 네트워크 없이 동작해야 합니다.
- 기존 Cursor `mcp.json`은 전체 교체하지 않고 병합해야 합니다.
- 지원하지 않는 가속기는 문서에 명시한 백엔드로 동작해야 합니다.
- 실제 모델 생성 검증과 모델 없는 테스트 결과를 구분해서 보고하세요.
