from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, ConfigDict, Field

from app.models import RequestStatus, UserRole


class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: UserRole
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RequestCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    currency: str = Field(min_length=1, max_length=3)
    category: str = Field(min_length=1)
    expense_date: date
    description: str = Field(min_length=1)


class RequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    requester_id: int
    amount: Decimal
    currency: str
    category: str
    expense_date: date
    description: str
    status: RequestStatus
    created_at: datetime
    updated_at: datetime


class RequestDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_id: int
    file_name: str
    file_size: int
    uploaded_at: datetime


class RequestStatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: RequestStatus
    reason: str | None
    changed_by_user_id: int
    changed_at: datetime


class RequestDetailResponse(RequestResponse):
    documents: list[RequestDocumentResponse]
    status_history: list[RequestStatusHistoryResponse]
