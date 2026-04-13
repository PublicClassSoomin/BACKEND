# app\domains\knowledge\agent_utils.py
import redis
import json
import os

r = redis.from_url(os.getenv('REDIS_URL'))

# redis reader 함수
def get_meeting_context(meeting_id: str) -> str:
    # 발화 전체 읽기
    utterances_raw = r.lrange(f"meeting:{meeting_id}:utterances", 0, -1)

    # 화자 이름 매핑
    # {speaker_id: speaker_name}, hgetall: hash 형태로 데이터 읽기
    speakers = r.hgetall(f"meeting:{meeting_id}:speakers")
    speakers = {k.decode(): v.decode() for k, v in speakers.items()}

    # 컨텍스트 문자열 조합
    lines = []
    for u in utterances_raw:
        # json.loads: string -> dict, loads(): json 문자열을 파이썬 객체로 변환
        utterance = json.loads(u)
        name = speakers.get(utterance['speaker_id'], utterance["speaker_id"])
        lines.append(f"[{name}] {utterance['content']}")

    return "\n".join(lines)

# 기능별 프롬프트 템플릿
def build_qa_prompt(context: str, question: str) -> str:
    return f"""
        다음은 현재 진행 중인 회의의 발화 내용입니다.

        {context}

        위 회의 내용을 바탕으로 아래 질문에 답해주세요.
        질문: {question}
    """

def build_summary_prompt(context: str) -> str:
    return f"""
        다음은 현재까지의 회의 발화 내용입니다.

        {context}

        위 내용을 아래 형식으로 요약해주세요.
        - 주요 논의 사항
        - 결정된 사항
        - 미결 사항
    """