"""
사용자 도메인의 데이터베이스 접근 로직을 담당하는 파일입니다. repository 계층은 service 계층과 데이터베이스 사이에서실제 조회 및 저장 작업을 수행합니다. 즉, service 계층은 처리 흐름을 결정하고, repository 계층은 DB에서 어떻게 조회하고 저장할지를 담당합니다.
"""

from sqlalchemy.orm import Session

from app.domains.user.models import User


def get_user_by_email(db: Session, email: str) -> User | None:
    """
    이메일을 기준으로 사용자를 조회합니다.
    로그인 시 사용자를 찾거나, 회원가입 시 중복 이메일 여부를 확인할 때 사용합니다.

    Args:
        db: 데이터베이스 세션입니다.
        email: 조회할 사용자 이메일입니다.

    Returns:
        사용자가 존재하면 User 객체를 반환하고,
        존재하지 않으면 None을 반환합니다.
    """
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """
    사용자 ID를 기준으로 사용자를 조회합니다. 토큰에 포함된 사용자 식별값으로 사용자를 다시 찾거나, 특정 사용자 정보를 조회할 때 사용할 수 있습니다.

    Args:
        db: 데이터베이스 세션입니다.
        user_id: 조회할 사용자 ID입니다.

    Returns:
        사용자가 존재하면 User 객체를 반환하고, 존재하지 않으면 None을 반환합니다.
    """
    return db.query(User).filter(User.id == user_id).first()


def create_user(
    db: Session,
    email: str,
    hashed_password: str,
    name: str,
    role: str,
) -> User:
    """
    새로운 사용자를 생성하고 데이터베이스에 저장합니다. 회원가입 시 service 계층에서 전달받은 데이터를 바탕으로 User 객체를 생성하고 저장합니다.

    Args:
        db: 데이터베이스 세션입니다.
        email: 저장할 사용자 이메일입니다.
        hashed_password: 해시 처리된 비밀번호입니다.
        name: 사용자 이름입니다.
        role: 사용자 역할입니다.

    Returns:
        저장이 완료된 User 객체를 반환합니다.
    """
    user = User(
        email=email,
        hashed_password=hashed_password,
        name=name,
        role=role,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user

"""
service.py는 생각하는 곳이고,
repository.py는 DB에 손대는 곳입니다.

예를 들면 회원가입 흐름은 나중에 이렇게 됩니다.

service.py
이메일 중복인지 확인해야겠다
repository.py
get_user_by_email() 호출
service.py
중복 아니면 비밀번호 해시해야겠다
repository.py
create_user() 호출
service.py
응답 반환
즉:

service = 흐름 제어
repository = DB 접근
"""