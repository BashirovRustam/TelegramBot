from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.session import get_async_session
from app.services.task_service import TaskService
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskWithDetails
from app.db.models import TaskStatus

router = APIRouter()


@router.get("/", response_model=List[TaskWithDetails])
async def get_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[TaskStatus] = None,
    assignee_id: Optional[int] = None,
    creator_id: Optional[int] = None,
    db: AsyncSession = Depends(get_async_session)
):
    task_service = TaskService(db)
    tasks = await task_service.get_tasks(
        skip=skip, 
        limit=limit, 
        status=status, 
        assignee_id=assignee_id, 
        creator_id=creator_id
    )
    return tasks


@router.get("/{task_id}", response_model=TaskWithDetails)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    task_service = TaskService(db)
    task = await task_service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/", response_model=TaskWithDetails)
async def create_task(
    task_data: TaskCreate,
    creator_id: int,  # In real app, this would come from authentication
    db: AsyncSession = Depends(get_async_session)
):
    task_service = TaskService(db)
    task = await task_service.create_task(task_data, creator_id)
    return await task_service.get_task_by_id(task.id)


@router.put("/{task_id}", response_model=TaskWithDetails)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    user_id: int,  # In real app, this would come from authentication
    db: AsyncSession = Depends(get_async_session)
):
    task_service = TaskService(db)
    task = await task_service.update_task(task_id, task_data, user_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return await task_service.get_task_by_id(task_id)


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    task_service = TaskService(db)
    success = await task_service.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully"}


@router.post("/{task_id}/assign")
async def assign_task(
    task_id: int,
    assignee_id: int,
    user_id: int,  # In real app, this would come from authentication
    db: AsyncSession = Depends(get_async_session)
):
    task_service = TaskService(db)
    task = await task_service.assign_task(task_id, assignee_id, user_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return await task_service.get_task_by_id(task_id)


@router.get("/user/{user_id}/assigned", response_model=List[TaskWithDetails])
async def get_user_assigned_tasks(
    user_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    task_service = TaskService(db)
    tasks = await task_service.get_user_tasks(user_id, as_assignee=True)
    return tasks


@router.get("/user/{user_id}/created", response_model=List[TaskWithDetails])
async def get_user_created_tasks(
    user_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    task_service = TaskService(db)
    tasks = await task_service.get_user_tasks(user_id, as_assignee=False)
    return tasks
