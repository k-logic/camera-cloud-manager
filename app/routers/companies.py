from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_admin_user
from app.models.company import Company
from app.models.user import User
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.get("", response_model=list[CompanyResponse])
def list_companies(db: Session = Depends(get_db), _user: User = Depends(get_admin_user)):
    return db.query(Company).order_by(Company.id).all()


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
def create_company(
    req: CompanyCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_admin_user),
):
    if db.query(Company).filter(Company.name == req.name).first():
        raise HTTPException(status_code=400, detail="Company name already exists")
    company = Company(name=req.name)
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(
    company_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_admin_user),
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.put("/{company_id}", response_model=CompanyResponse)
def update_company(
    company_id: int,
    req: CompanyUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_admin_user),
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    if req.name is not None:
        company.name = req.name
    db.commit()
    db.refresh(company)
    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(
    company_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_admin_user),
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    db.delete(company)
    db.commit()
