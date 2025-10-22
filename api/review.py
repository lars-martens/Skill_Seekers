#!/usr/bin/env python3
"""
Simple review queue system for community-submitted configs.
Tracks review status and handles approval/rejection.
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class ReviewManager:
    """Manage config review queue and status."""

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize review manager with storage path."""
        if storage_path is None:
            storage_path = Path(__file__).parent / "review_data.json"
        self.storage_path = storage_path
        self.reviews = self._load_reviews()

    def _load_reviews(self) -> Dict:
        """Load review data from storage file."""
        if not self.storage_path.exists():
            return {}

        try:
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_reviews(self):
        """Save review data to storage file."""
        with open(self.storage_path, 'w') as f:
            json.dump(self.reviews, f, indent=2)

    def get_pending_configs(self) -> List[Dict]:
        """Get all configs pending review."""
        repo_root = Path(__file__).parent.parent
        community_dir = repo_root / "configs" / "community"

        if not community_dir.exists():
            return []

        pending = []
        for config_file in community_dir.glob("*.json"):
            config_id = config_file.stem
            review_status = self.get_review_status(config_id)

            if review_status["status"] == "pending":
                # Load config details
                try:
                    with open(config_file, 'r') as f:
                        config_data = json.load(f)

                    pending.append({
                        "id": config_id,
                        "name": config_data.get("name", config_id),
                        "description": config_data.get("description", ""),
                        "base_url": config_data.get("base_url", ""),
                        "submitted_at": review_status["submitted_at"],
                        "file_path": str(config_file.relative_to(repo_root))
                    })
                except Exception:
                    pass

        # Sort by submission time (newest first)
        pending.sort(key=lambda x: x.get("submitted_at", ""), reverse=True)
        return pending

    def get_review_status(self, config_id: str) -> Dict:
        """Get review status for a config."""
        if config_id not in self.reviews:
            return {
                "status": "pending",
                "submitted_at": datetime.now().isoformat(),
                "reviewed_at": None,
                "reviewer_note": None
            }

        return self.reviews[config_id]

    def approve_config(self, config_id: str, note: str = None) -> Dict:
        """Approve a config and move it to the main configs directory."""
        repo_root = Path(__file__).parent.parent
        community_path = repo_root / "configs" / "community" / f"{config_id}.json"
        main_path = repo_root / "configs" / f"{config_id}.json"

        # Check if config exists in community dir
        if not community_path.exists():
            raise FileNotFoundError(f"Config '{config_id}' not found in community directory")

        # Check if already exists in main configs
        if main_path.exists():
            raise FileExistsError(f"Config '{config_id}' already exists in main configs directory")

        # Move file from community to main configs
        shutil.move(str(community_path), str(main_path))

        # Update review status
        self.reviews[config_id] = {
            "status": "approved",
            "submitted_at": self.get_review_status(config_id).get("submitted_at"),
            "reviewed_at": datetime.now().isoformat(),
            "reviewer_note": note
        }
        self._save_reviews()

        return {
            "success": True,
            "status": "approved",
            "message": f"Config '{config_id}' approved and moved to main configs",
            "new_path": str(main_path.relative_to(repo_root))
        }

    def reject_config(self, config_id: str, note: str = None) -> Dict:
        """Reject a config (keeps in community dir but marks as rejected)."""
        repo_root = Path(__file__).parent.parent
        community_path = repo_root / "configs" / "community" / f"{config_id}.json"

        # Check if config exists
        if not community_path.exists():
            raise FileNotFoundError(f"Config '{config_id}' not found in community directory")

        # Update review status
        self.reviews[config_id] = {
            "status": "rejected",
            "submitted_at": self.get_review_status(config_id).get("submitted_at"),
            "reviewed_at": datetime.now().isoformat(),
            "reviewer_note": note
        }
        self._save_reviews()

        return {
            "success": True,
            "status": "rejected",
            "message": f"Config '{config_id}' rejected",
            "note": note
        }

    def get_review_stats(self) -> Dict:
        """Get review queue statistics."""
        pending = self.get_pending_configs()
        approved = sum(1 for r in self.reviews.values() if r["status"] == "approved")
        rejected = sum(1 for r in self.reviews.values() if r["status"] == "rejected")

        return {
            "pending": len(pending),
            "approved": approved,
            "rejected": rejected,
            "total": len(pending) + approved + rejected
        }


if __name__ == "__main__":
    # Test the review manager
    manager = ReviewManager()

    print("Review Queue Stats:")
    print(json.dumps(manager.get_review_stats(), indent=2))

    print("\nPending Configs:")
    for config in manager.get_pending_configs():
        print(f"  - {config['id']}: {config['name']}")
