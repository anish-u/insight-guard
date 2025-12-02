import os
from pathlib import Path
from typing import Literal

from ..config import settings  # optional, but we use env var directly too

UploadType = Literal["weekly_dhs", "monthly_dhs_web", "dept_scan"]

BASE_DIR = Path(os.getenv("UPLOAD_BASE_DIR", settings.upload_base_dir)).resolve()


def ensure_base_dir() -> None:
  BASE_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_dept(dept: str) -> str:
  slug = dept.strip().lower().replace(" ", "_")
  allowed = "".join(ch for ch in slug if ch.isalnum() or ch in ("_", "-"))
  return allowed or "unknown"


def build_upload_path(
  report_type: UploadType,
  year: int,
  month: int,
  department: str | None = None,
  week_index: int | None = None,
) -> Path:
  ensure_base_dir()

  if report_type == "weekly_dhs":
    if week_index is None:
      raise ValueError("week_index is required for weekly_dhs uploads")
    folder = (
      BASE_DIR
      / "weekly_dhs"
      / f"{year:04d}"
      / f"{month:02d}"
      / f"week-{week_index}"
    )
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "report.csv"

  if report_type == "monthly_dhs_web":
    folder = BASE_DIR / "monthly_dhs_web" / f"{year:04d}" / f"{month:02d}"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "report.csv"

  if report_type == "dept_scan":
    if department is None:
      raise ValueError("department is required for dept_scan uploads")
    dept_slug = sanitize_dept(department)
    folder = BASE_DIR / "dept_scan" / dept_slug / f"{year:04d}" / f"{month:02d}"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "report.csv"

  raise ValueError(f"Unknown report_type: {report_type}")
