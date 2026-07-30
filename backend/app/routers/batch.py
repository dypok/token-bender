import os
import asyncio
import pandas as pd
from fastapi import APIRouter, UploadFile, File, Header, Form, HTTPException
from pydantic import BaseModel
from app.models.schemas import (
    BatchFolderRequest, ProjectionRequest,
    ProjectionResponse, BatchUploadResponse
)
from app.batch_tasks import create_task, get_logs, get_result, is_done
from app.services.batch_processor import (
    read_df_from_file, detect_text_column, process_batch_dataframe,
    run_batch_background_bytes, empty_summary
)

router = APIRouter()


class ProgressResponse(BaseModel):
    logs: list[str]
    done: bool
    result: BatchUploadResponse | None = None


@router.post("/api/batch/upload", response_model=BatchUploadResponse)
async def batch_upload(
    file: UploadFile = File(...),
    optent_tokens: bool = Form(True),
    engine: str = Form("ctranslate2"),
    deepl_api_key: str = Header(default=""),
):
    df = read_df_from_file(file)
    text_col = detect_text_column(df)
    return await process_batch_dataframe(df, text_col, optent_tokens, deepl_api_key)


@router.post("/api/batch/folder", response_model=BatchUploadResponse)
async def batch_folder(req: BatchFolderRequest, deepl_api_key: str = Header(default="")):
    folder = req.folder_path
    if not os.path.isdir(folder):
        return BatchUploadResponse(results=[], economic_summary=empty_summary())

    all_dfs = []
    for fname in os.listdir(folder):
        if fname.endswith((".xlsx", ".csv")):
            path = os.path.join(folder, fname)
            if fname.endswith(".csv"):
                df = pd.read_csv(path)
            else:
                df = pd.read_excel(path)
            all_dfs.append(df)

    if not all_dfs:
        return BatchUploadResponse(results=[], economic_summary=empty_summary())

    df = pd.concat(all_dfs, ignore_index=True)
    text_col = detect_text_column(df)
    return await process_batch_dataframe(df, text_col, req.optent_tokens, deepl_api_key)


@router.post("/api/batch/start")
async def batch_start(
    file: UploadFile = File(...),
    optent_tokens: bool = Form(True),
    engine: str = Form("ctranslate2"),
    deepl_api_key: str = Header(default=""),
):
    task_id = create_task()
    content = await file.read()
    filename = file.filename or "uploaded.xlsx"
    asyncio.create_task(run_batch_background_bytes(task_id, content, filename, optent_tokens, deepl_api_key))
    return {"task_id": task_id}


@router.get("/api/batch/progress/{task_id}", response_model=ProgressResponse)
async def batch_progress(task_id: str):
    result = get_result(task_id)
    return ProgressResponse(
        logs=get_logs(task_id),
        done=is_done(task_id),
        result=result,
    )


@router.post("/api/analyze/projection", response_model=ProjectionResponse)
def projection(req: ProjectionRequest):
    diff_per_review = req.tokens_original - req.tokens_translated
    daily_diff = diff_per_review * req.reviews_per_day
    monthly_diff = daily_diff * req.days
    savings = (monthly_diff / 1_000_000) * req.cost_per_million_tokens_usd
    return ProjectionResponse(
        daily_token_diff=daily_diff,
        monthly_token_diff=monthly_diff,
        monthly_savings_usd=round(savings, 2),
    )
