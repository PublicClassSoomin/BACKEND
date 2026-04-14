# scripts/seed.py
from app.infra.database.session import SessionLocal
from app.domains.user.models import User
from app.domains.workspace.models import Workspace, WorkspaceMember
from app.domains.meeting.models import Meeting
from app.domains.integration.models import Integration, ServiceType


def seed_test_data():
    db = SessionLocal()
    try:
        if db.query(User).first():
            return

        user = User(
            email="test@workb.com",
            password_hash="placeholder",
            name="테스트유저",
        )
        db.add(user)
        db.flush()

        workspace = Workspace(
            owner_id=user.id,
            name="테스트 워크스페이스",
            industry="IT",
            default_language="ko",
        )
        db.add(workspace)
        db.flush()

        db.add(WorkspaceMember(
            workspace_id=workspace.id,
            user_id=user.id,
            role="admin",
        ))

        db.add(Meeting(
            workspace_id=workspace.id,
            created_by=user.id,
            title="테스트 회의",
            status="scheduled",
        ))

        for service in ServiceType:
            db.add(Integration(
                workspace_id=workspace.id,
                service=service,
                is_connected=False,
            ))

        db.commit()
        print("🌱 [DEBUG] 테스트 데이터 삽입 완료")

    except Exception as e:
        db.rollback()
        print(f"❌ [DEBUG] 테스트 데이터 삽입 실패: {e}")
    finally:
        db.close()