import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.dependencies import get_friends_service
from app.features.friends.service import FriendsService
from app.schemas.friends import (
    FriendAcceptResponse,
    FriendListItem,
    FriendRequest,
    FriendRequestCreated,
    FriendRequestItem,
)
from app.utils.jwt import get_current_user

router = APIRouter()
logger = logging.getLogger("app.friends.router")


@router.post("/request", status_code=status.HTTP_201_CREATED, response_model=FriendRequestCreated)
async def request_friendship(
    payload: FriendRequest,
    current_user=Depends(get_current_user),
    service: FriendsService = Depends(get_friends_service),
):
    user_id = current_user.id
    try:
        friendship_id = await service.send_friend_request(
            requester_id=user_id,
            friend_id=payload.friend_id,
            friend_username=payload.friend_username,
        )
        logger.info("Friend request created requester_id=%s friendship_id=%s", user_id, friendship_id)
        return FriendRequestCreated(friendship_id=friendship_id)
    except ValueError as exc:
        logger.warning("Friend request rejected requester_id=%s reason=%s", user_id, str(exc))
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        logger.exception("Failed creating friend request requester_id=%s", user_id)
        raise HTTPException(status_code=500, detail="Failed to create friend request")


@router.post("/accept/{id}", response_model=FriendAcceptResponse)
async def accept_friendship(
    id: int,
    current_user=Depends(get_current_user),
    service: FriendsService = Depends(get_friends_service),
):
    user_id = current_user.id
    try:
        accepted = await service.accept_friend_request(id, user_id)
        if not accepted:
            raise HTTPException(status_code=404, detail="Friend request not found")
        logger.info("Friend request accepted friendship_id=%s addressee_id=%s", id, user_id)
        return FriendAcceptResponse()
    except PermissionError as exc:
        logger.warning("Friend request accept forbidden friendship_id=%s user_id=%s", id, user_id)
        raise HTTPException(status_code=403, detail=str(exc))
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed accepting friend request friendship_id=%s user_id=%s", id, user_id)
        raise HTTPException(status_code=500, detail="Failed to accept friend request")


@router.get("/", response_model=list[FriendListItem])
async def list_friends(
    current_user=Depends(get_current_user),
    service: FriendsService = Depends(get_friends_service),
):
    user_id = current_user.id
    try:
        friends = await service.get_friends(user_id)
        logger.info("Friends listed user_id=%s count=%s", user_id, len(friends))
        return friends
    except Exception:
        logger.exception("Failed listing friends user_id=%s", user_id)
        raise HTTPException(status_code=500, detail="Failed to fetch friends")


@router.get("/requests", response_model=list[FriendRequestItem])
async def list_friend_requests(
    current_user=Depends(get_current_user),
    service: FriendsService = Depends(get_friends_service),
):
    user_id = current_user.id
    try:
        requests = await service.get_pending_requests(user_id)
        logger.info("Friend requests listed user_id=%s count=%s", user_id, len(requests))
        return requests
    except Exception:
        logger.exception("Failed listing friend requests user_id=%s", user_id)
        raise HTTPException(status_code=500, detail="Failed to fetch friend requests")


@router.delete("/remove/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_friendship(
    user_id: int,
    current_user=Depends(get_current_user),
    service: FriendsService = Depends(get_friends_service),
):
    requester_id = current_user.id
    try:
        removed = await service.remove_friend(requester_id, user_id)
        if not removed:
            raise HTTPException(status_code=404, detail="Friendship not found")
        logger.info("Friend removed user_id=%s removed_user_id=%s", requester_id, user_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed removing friend user_id=%s removed_user_id=%s", requester_id, user_id)
        raise HTTPException(status_code=500, detail="Failed to remove friend")
