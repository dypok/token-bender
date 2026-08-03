import asyncio
from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel
from app.models.schemas import (
    BatchUploadResponse
)
from app.batch_tasks import create_task, get_logs, get_result, is_done
from app.services.batch import (
    read_df_from_file, detect_text_column, process_batch_dataframe,
    run_batch_background_bytes,
)
from app.services.batch.economics import empty_summary

router = APIRouter()


class ProgressResponse(BaseModel):
    logs: list[str]
    done: bool
    result: BatchUploadResponse | None = None


@router.post("/api/batch/upload", response_model=BatchUploadResponse)
async def batch_upload(
    file: UploadFile = File(...),
    optent_tokens: bool = Form(True),
):
    df = read_df_from_file(file)
    text_col = detect_text_column(df)
    return await process_batch_dataframe(df, text_col, optent_tokens)


@router.post("/api/batch/folder", response_model=BatchUploadResponse)
async def batch_folder_upload(
    files: list[UploadFile] = File(...),
    optent_tokens: bool = Form(True),
):
    all_dfs = []
    for file in files:
        if not file.filename:
            continue
        all_dfs.append(read_df_from_file(file))

    if not all_dfs:
        return BatchUploadResponse(results=[], economic_summary=empty_summary())

    df = pd.concat(all_dfs, ignore_index=True)
    text_col = detect_text_column(df)
    return await process_batch_dataframe(df, text_col, optent_tokens)


@router.post("/api/batch/start")
async def batch_start(
    file: UploadFile = File(...),
    optent_tokens: bool = Form(True),
):
    task_id = create_task()
    content = await file.read()
    filename = file.filename or "uploaded.xlsx"
    asyncio.create_task(run_batch_background_bytes(task_id, content, filename, optent_tokens))
    return {"task_id": task_id}


@router.get("/api/batch/progress/{task_id}", response_model=ProgressResponse)
async def batch_progress(task_id: str):
    result = get_result(task_id)
    return ProgressResponse(
        logs=get_logs(task_id),
        done=is_done(task_id),
        result=result,
    )
