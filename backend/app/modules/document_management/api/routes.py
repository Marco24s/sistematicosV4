from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.modules.document_management.domain.models import DocumentType, AssetDocument
from app.modules.assets.domain.models import Asset

router = APIRouter()

@router.get("/document-management/types", tags=["document_management"])
def get_document_types(db: Session = Depends(get_db)):
    return db.query(DocumentType).filter_by(deleted_at=None).all()

@router.get("/document-management/assets/{asset_id}/documents", tags=["document_management"])
def get_asset_documents(asset_id: UUID, db: Session = Depends(get_db)):
    asset = db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset no encontrado.")
        
    docs = db.query(AssetDocument).filter_by(asset_id=asset_id, deleted_at=None).all()
    results = []
    for doc in docs:
        dtype = db.get(DocumentType, doc.document_type_id)
        results.append({
            "id": str(doc.id),
            "document_code": doc.document_code,
            "version": doc.version,
            "type_name": dtype.name if dtype else "Unknown",
            "issued_date": str(doc.issued_date),
            "status": doc.status
        })
    return results

@router.post("/document-management/assets/{asset_id}/documents", tags=["document_management"])
def add_asset_document(asset_id: UUID, document_type_id: UUID, document_code: str, version: str, issued_date: str, created_by: str, db: Session = Depends(get_db)):
    from datetime import datetime
    import uuid
    
    asset = db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset no encontrado.")
        
    dtype = db.get(DocumentType, document_type_id)
    if not dtype:
        raise HTTPException(status_code=404, detail="Document type no encontrado.")
        
    try:
        parsed_date = datetime.strptime(issued_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="issued_date debe estar en formato YYYY-MM-DD")
        
    doc = AssetDocument(
        id=uuid.uuid4(),
        asset_id=asset_id,
        document_type_id=document_type_id,
        document_code=document_code,
        version=version,
        issued_date=parsed_date,
        created_by=created_by,
    )
    db.add(doc)
    db.commit()
    return {"status": "ok", "document_id": str(doc.id)}
