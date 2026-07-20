from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_finance_user
from app.models import Request, RequestDocument, RequestStatus, User, UserRole
from app.schemas import (
    RequestCreate,
    RequestDetailResponse,
    RequestDocumentResponse,
    RequestResponse,
    RequestWithRequesterResponse,
)
from app.services.email import send_new_request_notification
from app.services.storage import save_request_document, validate_upload_batch

router = APIRouter(prefix="/requests", tags=["requests"])


def _get_request_or_404(db: Session, request_id: int) -> Request:
    request = db.get(Request, request_id)
    if request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    return request


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

    send_new_request_notification(
        requester_name=current_user.name,
        amount=str(request.amount),
        currency=request.currency,
        category=request.category,
        request_id=request.id,
    )

    return request


@router.get("/mine", response_model=list[RequestResponse])
def list_my_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Request]:
    return (
        db.query(Request)
        .filter(Request.requester_id == current_user.id)
        .order_by(Request.updated_at.desc())
        .all()
    )


@router.get("/pending", response_model=list[RequestWithRequesterResponse])
def list_pending_requests(
    current_user: User = Depends(require_finance_user),
    db: Session = Depends(get_db),
) -> list[RequestWithRequesterResponse]:
    requests = (
        db.query(Request)
        .filter(Request.status.in_([RequestStatus.pending, RequestStatus.more_info_needed]))
        .order_by(Request.created_at.desc())
        .all()
    )
    return [
        RequestWithRequesterResponse(
            **RequestResponse.model_validate(request).model_dump(),
            requester_name=request.requester.name,
            requester_email=request.requester.email,
        )
        for request in requests
    ]


@router.get("", response_model=list[RequestWithRequesterResponse])
def list_all_requests(
    requester_id: int | None = Query(None),
    status_filter: RequestStatus | None = Query(None, alias="status"),
    category: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    current_user: User = Depends(require_finance_user),
    db: Session = Depends(get_db),
) -> list[RequestWithRequesterResponse]:
    query = db.query(Request)
    if requester_id is not None:
        query = query.filter(Request.requester_id == requester_id)
    if status_filter is not None:
        query = query.filter(Request.status == status_filter)
    if category is not None:
        query = query.filter(Request.category == category)
    if date_from is not None:
        query = query.filter(Request.expense_date >= date_from)
    if date_to is not None:
        query = query.filter(Request.expense_date <= date_to)

    requests = query.order_by(Request.created_at.desc()).all()
    return [
        RequestWithRequesterResponse(
            **RequestResponse.model_validate(request).model_dump(),
            requester_name=request.requester.name,
            requester_email=request.requester.email,
        )
        for request in requests
    ]


@router.get("/{request_id}", response_model=RequestDetailResponse)
def get_request_detail(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Request:
    request = _get_request_or_404(db, request_id)
    if request.requester_id != current_user.id and current_user.role != UserRole.finance:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this request",
        )
    return request


@router.post(
    "/{request_id}/documents",
    response_model=list[RequestDocumentResponse],
    status_code=status.HTTP_201_CREATED,
)
def upload_documents(
    request_id: int,
    files: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[RequestDocument]:
    request = _get_request_or_404(db, request_id)
    if request.requester_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to upload documents to this request",
        )

    existing_count = (
        db.query(RequestDocument).filter(RequestDocument.request_id == request_id).count()
    )
    validated_files = validate_upload_batch(existing_count, files)

    documents = []
    for filename, content in validated_files:
        file_path, file_size = save_request_document(request_id, filename, content)
        document = RequestDocument(
            request_id=request_id,
            file_name=filename,
            file_path=file_path,
            file_size=file_size,
        )
        db.add(document)
        documents.append(document)

    db.commit()
    for document in documents:
        db.refresh(document)
    return documents


@router.get("/{request_id}/documents/{doc_id}")
def download_document(
    request_id: int,
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    request = _get_request_or_404(db, request_id)
    if request.requester_id != current_user.id and current_user.role != UserRole.finance:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this document",
        )

    document = db.get(RequestDocument, doc_id)
    if document is None or document.request_id != request_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    return FileResponse(document.file_path, filename=document.file_name)
