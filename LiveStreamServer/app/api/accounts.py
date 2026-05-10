"""Account (RTMP target) endpoints."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import require_token
from app.database import get_db
from app.models import Account
from app.schemas import AccountIn, AccountOut, AccountUpdate
from app.utils.security import mask_stream_key


router = APIRouter(prefix="/accounts", tags=["accounts"], dependencies=[Depends(require_token)])


def _to_out(acc: Account) -> AccountOut:
    return AccountOut(
        id=acc.id,
        name=acc.name,
        platform=acc.platform,
        rtmp_url=acc.rtmp_url,
        stream_key_masked=mask_stream_key(acc.stream_key),
        default_bitrate=acc.default_bitrate or "2500k",
        default_resolution=acc.default_resolution or "1280x720",
        is_active=acc.is_active,
        created_at=acc.created_at,
    )


@router.get("", response_model=List[AccountOut])
def list_accounts(db: Session = Depends(get_db)) -> List[AccountOut]:
    return [_to_out(a) for a in db.query(Account).order_by(Account.created_at.desc()).all()]


@router.post("", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
def create_account(payload: AccountIn, db: Session = Depends(get_db)) -> AccountOut:
    account = Account(**payload.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return _to_out(account)


@router.patch("/{account_id}", response_model=AccountOut)
def update_account(account_id: int, payload: AccountUpdate, db: Session = Depends(get_db)) -> AccountOut:
    account = db.query(Account).get(account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="akun tidak ditemukan")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(account, key, value)
    db.commit()
    db.refresh(account)
    return _to_out(account)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(account_id: int, db: Session = Depends(get_db)) -> None:
    account = db.query(Account).get(account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="akun tidak ditemukan")
    db.delete(account)
    db.commit()
