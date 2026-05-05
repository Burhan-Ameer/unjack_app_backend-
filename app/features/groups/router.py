import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies import get_group_service
from app.features.groups.service import GroupService
from app.schemas.groups import GroupCreate, GroupUpdate, GroupResponse, GroupMemberAdd, GroupMemberResponse
from app.utils.jwt import get_current_user

router = APIRouter()
logger = logging.getLogger("app.groups.router")

@router.post("/", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    payload: GroupCreate,
    current_user=Depends(get_current_user),
    service: GroupService = Depends(get_group_service)
):
    try:
        group = await service.create_group(payload.name)
        logger.info("Group created name=%s created_by=%s", payload.name, current_user.id)
        return group
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        logger.exception("Failed creating group name=%s", payload.name)
        raise HTTPException(status_code=500, detail="Failed to create group")

@router.get("/", response_model=List[GroupResponse])
async def list_groups(
    current_user=Depends(get_current_user),
    service: GroupService = Depends(get_group_service)
):
    try:
        return await service.list_groups()
    except Exception:
        logger.exception("Failed listing groups")
        raise HTTPException(status_code=500, detail="Failed to fetch groups")

@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: int,
    current_user=Depends(get_current_user),
    service: GroupService = Depends(get_group_service)
):
    group = await service.get_group(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group

@router.patch("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: int,
    payload: GroupUpdate,
    current_user=Depends(get_current_user),
    service: GroupService = Depends(get_group_service)
):
    try:
        group = await service.update_group(group_id, payload.name)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        return group
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        logger.exception("Failed updating group id=%s", group_id)
        raise HTTPException(status_code=500, detail="Failed to update group")

@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: int,
    current_user=Depends(get_current_user),
    service: GroupService = Depends(get_group_service)
):
    success = await service.delete_group(group_id)
    if not success:
        raise HTTPException(status_code=404, detail="Group not found")
    return

@router.post("/{group_id}/add", response_model=GroupMemberResponse)
async def add_member(
    group_id: int,
    payload: GroupMemberAdd,
    current_user=Depends(get_current_user),
    service: GroupService = Depends(get_group_service)
):
    try:
        member = await service.add_user_to_group(group_id, payload.user_id)
        logger.info("User added to group group_id=%s user_id=%s", group_id, payload.user_id)
        return member
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        logger.exception("Failed adding user to group group_id=%s user_id=%s", group_id, payload.user_id)
        raise HTTPException(status_code=500, detail="Failed to add user to group")
