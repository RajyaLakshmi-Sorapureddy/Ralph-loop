from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Request, User
from app.schemas import RequestCreate, RequestResponse

router = APIRouter(prefix="/requests", tags=["requests"])


@router.post("", response_model=RequestResponse, status_code=status.HTTP_201_CREATED)
def create_request(
    payload: RequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Request:
    request = Request(
        requester_id=current_user.id,
        amount=payload.amount,
        currency=payload.currency,
        category=payload.category,
        expense_date=payload.expense_date,
        description=payload.description,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request
