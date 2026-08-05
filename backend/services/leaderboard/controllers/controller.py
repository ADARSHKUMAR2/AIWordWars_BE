from datetime import datetime, timezone
from typing import Optional
from services.leaderboard.models.leaderboard_entry import LeaderboardEntry


async def submit_score(
    firebase_uid: str,
    display_name: Optional[str],
    photo_url: Optional[str],
    board_id: str,
    mode: str,
    score: int,
) -> dict:
    """
    Submit a score to the leaderboard.
    Uses a best-score-only strategy: only updates if the new score is higher.
    Returns the saved entry and whether it was a personal best.
    """
    # Check if this player already has an entry for this board + mode
    existing = await LeaderboardEntry.find_one(
        LeaderboardEntry.firebase_uid == firebase_uid,
        LeaderboardEntry.board_id == board_id,
        LeaderboardEntry.mode == mode,
    )

    is_personal_best = False

    if existing:
        if score > existing.score:
            # New high score — update it
            existing.score = score
            existing.display_name = display_name or existing.display_name
            existing.photo_url = photo_url or existing.photo_url
            existing.submitted_at = datetime.now(timezone.utc)
            await existing.save()
            is_personal_best = True
            print(f"🏆 New personal best for {firebase_uid} on [{board_id}/{mode}]: {score}")
        else:
            print(f"📊 Score {score} not a new best for {firebase_uid} on [{board_id}/{mode}] (current best: {existing.score})")
        entry = existing
    else:
        # First time on this board — create a new entry
        entry = LeaderboardEntry(
            firebase_uid=firebase_uid,
            display_name=display_name,
            photo_url=photo_url,
            board_id=board_id,
            mode=mode,
            score=score,
        )
        await entry.insert()
        is_personal_best = True
        print(f"🆕 First entry for {firebase_uid} on [{board_id}/{mode}]: {score}")

    return {
        "firebase_uid": entry.firebase_uid,
        "board_id": entry.board_id,
        "mode": entry.mode,
        "score": entry.score,
        "is_personal_best": is_personal_best,
        "submitted_at": entry.submitted_at.isoformat(),
    }


async def get_leaderboard(
    board_id: str,
    mode: str = "simple",
    limit: int = 20,
) -> list[dict]:
    """
    Fetch the top N players for a board, sorted by score descending.
    Returns a ranked list (rank 1 = highest score).
    """
    entries = await (
        LeaderboardEntry
        .find(
            LeaderboardEntry.board_id == board_id,
            LeaderboardEntry.mode == mode,
        )
        .sort(-LeaderboardEntry.score)
        .limit(limit)
        .to_list()
    )

    return [
        {
            "rank": idx + 1,
            "firebase_uid": e.firebase_uid,
            "display_name": e.display_name or "Anonymous",
            "photo_url": e.photo_url,
            "score": e.score,
            "submitted_at": e.submitted_at.isoformat(),
        }
        for idx, e in enumerate(entries)
    ]


async def get_player_rank(
    firebase_uid: str,
    board_id: str,
    mode: str = "simple",
) -> Optional[dict]:
    """
    Get a specific player's rank and score on a board.
    Used to show 'Your Rank: #42' in the Unity HUD.
    Returns None if the player hasn't submitted a score yet.
    """
    player_entry = await LeaderboardEntry.find_one(
        LeaderboardEntry.firebase_uid == firebase_uid,
        LeaderboardEntry.board_id == board_id,
        LeaderboardEntry.mode == mode,
    )

    if not player_entry:
        return None

    # Count how many players scored HIGHER than this player
    higher_count = await LeaderboardEntry.find(
        LeaderboardEntry.board_id == board_id,
        LeaderboardEntry.mode == mode,
        LeaderboardEntry.score > player_entry.score,
    ).count()

    return {
        "firebase_uid": firebase_uid,
        "rank": higher_count + 1,   # Rank = number of players above + 1
        "score": player_entry.score,
        "board_id": board_id,
        "mode": mode,
    }
