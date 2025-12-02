from fastapi import (
  APIRouter,
  UploadFile,
  File,
  Form,
  Depends,
  HTTPException,
  status,
)
from neo4j import Driver

from ..neo4j_client import driver_dependency
from ..ingestion.weekly_dhs_ingestor import ingest_weekly_dhs_scan
from ..ingestion.monthly_dhs_web_ingestor import ingest_monthly_dhs_web_scan
from ..ingestion.dept_scan_ingestor import ingest_dept_scan

router = APIRouter(prefix="/ingest", tags=["ingest"])


def validate_csv(file: UploadFile) -> None:
  if not file.filename or not file.filename.lower().endswith(".csv"):
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="Only .csv files are supported.",
    )


@router.post("/weekly-dhs")
async def upload_weekly_dhs(
  year: int = Form(..., ge=2000, le=2100),
  month: int = Form(..., ge=1, le=12),
  week_index: int = Form(..., ge=1, le=6),
  report: UploadFile = File(...),
  driver: Driver = Depends(driver_dependency),
):
  validate_csv(report)
  file_bytes = await report.read()

  result = ingest_weekly_dhs_scan(
      driver=driver,
      file_bytes=file_bytes,
      filename=report.filename or "report.csv",
      year=year,
      month=month,
      week_index=week_index,
  )

  return {"status": "ok", "type": "weekly_dhs", **result}


@router.post("/monthly-dhs-web")
async def upload_monthly_dhs_web(
  year: int = Form(..., ge=2000, le=2100),
  month: int = Form(..., ge=1, le=12),
  report: UploadFile = File(...),
  driver: Driver = Depends(driver_dependency),
):
  validate_csv(report)
  file_bytes = await report.read()

  result = ingest_monthly_dhs_web_scan(
      driver=driver,
      file_bytes=file_bytes,
      filename=report.filename or "report.csv",
      year=year,
      month=month,
  )

  return {"status": "ok", "type": "monthly_dhs_web", **result}


@router.post("/dept-scan")
async def upload_dept_scan(
  year: int = Form(..., ge=2000, le=2100),
  month: int = Form(..., ge=1, le=12),
  department: str = Form(...),
  report: UploadFile = File(...),
  driver: Driver = Depends(driver_dependency),
):
  if not department.strip():
      raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST,
          detail="Department is required.",
      )

  validate_csv(report)
  file_bytes = await report.read()

  result = ingest_dept_scan(
      driver=driver,
      file_bytes=file_bytes,
      filename=report.filename or "report.csv",
      year=year,
      month=month,
      department=department,
  )

  return {"status": "ok", "type": "dept_scan", **result}
