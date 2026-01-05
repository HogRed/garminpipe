from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

import garth
from garth.exc import GarthException

@dataclass
class GarthClient:
    """
    Thin adapter around garth.
    Auth pattern follows garth docs: resume() first, login() if needed,
    then save(). :contentReference[oaicite:3]{index=3}
    """
    session_dir: Path

    def resume_or_login(self, email: Optional[str], password: Optional[str], prompt_mfa=None) -> None:
        # Try to resume first
        try:
            garth.resume(str(self.session_dir))
            _ = garth.client.username  # triggers validation
            return
        except Exception:
            pass
        
        # if no email or password, cannot login
        if not email or not password:
            raise RuntimeError(
                "No valid session found. Provide email/password (CLI: garminpipe auth login) to create one."
            )
        
        # otherwise, login
        garth.login(email, password, prompt_mfa=prompt_mfa)
        garth.save(str(self.session_dir))

    # list activities using the Connect endpoint
    def list_activities(
        self,
        start_date: date,
        end_date: date,
        start: int = 0,
        limit: int = 100,
        activity_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Uses the Connect endpoint commonly used for activity listing:
        /activitylist-service/activities/search/activities

        Params are somewhat flexible; Garmin may change behavior over time.
        """
        # build params
        params: Dict[str, Any] = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "start": start,
            "limit": limit,
        }
        # add activity type if given
        if activity_type:
            params["activityType"] = activity_type

        # make request
        try:
            return garth.connectapi("/activitylist-service/activities/search/activities", params=params)
        except GarthException as e:
            raise RuntimeError(f"Garmin request failed: {e}") from e

    # method to just resume session
    def resume(self) -> bool:
        try:
            garth.resume(str(self.session_dir))
            _ = garth.client.username
            return True
        except Exception:
            return False