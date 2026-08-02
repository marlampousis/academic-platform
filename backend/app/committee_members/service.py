from sqlalchemy.orm import Session, joinedload

from app.committee_members.models import (
    CommitteeMember,
)
from app.committee_members.schemas import (
    CommitteeMemberCreate,
    CommitteeMemberUpdate,
)


def create_committee_member(
    db: Session,
    committee_id: int,
    member_data: CommitteeMemberCreate,
) -> CommitteeMember:
    committee_member = CommitteeMember(
        committee_id=committee_id,
        user_id=member_data.user_id,
        role_in_committee=(
            member_data.role_in_committee
        ),
        is_active=True,
    )

    db.add(committee_member)
    db.commit()
    db.refresh(committee_member)

    return get_committee_member_by_id(
        db=db,
        member_id=committee_member.id,
    )


def get_committee_members(
    db: Session,
    committee_id: int,
) -> list[CommitteeMember]:
    return (
        db.query(CommitteeMember)
        .options(
            joinedload(CommitteeMember.user)
        )
        .filter(
            CommitteeMember.committee_id
            == committee_id
        )
        .order_by(
            CommitteeMember.is_active.desc(),
            CommitteeMember.joined_at.asc(),
            CommitteeMember.id.asc(),
        )
        .all()
    )


def get_committee_member_by_id(
    db: Session,
    member_id: int,
) -> CommitteeMember | None:
    return (
        db.query(CommitteeMember)
        .options(
            joinedload(CommitteeMember.user)
        )
        .filter(
            CommitteeMember.id == member_id
        )
        .first()
    )


def get_committee_member_by_user(
    db: Session,
    committee_id: int,
    user_id: int,
) -> CommitteeMember | None:
    return (
        db.query(CommitteeMember)
        .filter(
            CommitteeMember.committee_id
            == committee_id,
            CommitteeMember.user_id == user_id,
        )
        .first()
    )


def get_active_committee_chair(
    db: Session,
    committee_id: int,
    excluded_member_id: int | None = None,
) -> CommitteeMember | None:
    query = (
        db.query(CommitteeMember)
        .filter(
            CommitteeMember.committee_id
            == committee_id,
            CommitteeMember.role_in_committee
            == "CHAIR",
            CommitteeMember.is_active.is_(True),
        )
    )

    if excluded_member_id is not None:
        query = query.filter(
            CommitteeMember.id
            != excluded_member_id
        )

    return query.first()


def update_committee_member(
    db: Session,
    committee_member: CommitteeMember,
    member_data: CommitteeMemberUpdate,
) -> CommitteeMember:
    update_data = member_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(
            committee_member,
            field,
            value,
        )

    db.commit()
    db.refresh(committee_member)

    return get_committee_member_by_id(
        db=db,
        member_id=committee_member.id,
    )


def delete_committee_member(
    db: Session,
    committee_member: CommitteeMember,
) -> None:
    db.delete(committee_member)
    db.commit()