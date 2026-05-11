import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies import get_group_service
from app.features.groups.service import GroupService
from app.features.groups.schemas import GroupCreate, GroupUpdate, GroupResponse, GroupMemberAdd, GroupMemberResponse
from app.utils.jwt import get_current_user

router = APIRouter()
logger = logging.getLogger("app.groups.router")

@router.post("/", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    payload: GroupCreate,
    current_user=Depends(get_current_user),
    service: GroupService = Depends(get_group_service)
):
    """
    Create a new group.
    
    - **payload**: The data required to create a group (e.g., name).
    - **Returns**: The created group with its initial state.
    """
    try:
        group = await service.create_group(payload.name, current_user.id)
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
    """
    Retrieve a list of all groups.
    
    - **Returns**: A list of groups including their statistics and members.
    """
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
    """
    Retrieve details of a specific group by its ID.
    
    - **group_id**: The unique identifier of the group.
    - **Returns**: The requested group object.
    - **Raises 404**: If the group does not exist.
    """
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
    """
    Update an existing group's information.
    
    - **group_id**: The unique identifier of the group to update.
    - **payload**: The fields to update (e.g., name).
    - **Returns**: The updated group object.
    - **Raises 403**: If the user is not a group admin.
    - **Raises 404**: If the group does not exist.
    """
    try:
        group = await service.update_group(group_id, payload.name, current_user.id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        return group
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
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
    """
    Delete a group by its ID.
    
    - **group_id**: The unique identifier of the group to delete.
    - **Returns**: HTTP 204 No Content on successful deletion.
    - **Raises 404**: If the group does not exist.
    """
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
    """
    Add a user to a specific group.
    
    - **group_id**: The unique identifier of the group.
    - **payload**: The data containing the user_id to be added.
    - **Returns**: The newly created group member record.
    """
    try:
        member = await service.add_user_to_group(group_id, payload.user_id)
        logger.info("User added to group group_id=%s user_id=%s", group_id, payload.user_id)
        return member
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        logger.exception("Failed adding user to group group_id=%s user_id=%s", group_id, payload.user_id)
        raise HTTPException(status_code=500, detail="Failed to add user to group")
