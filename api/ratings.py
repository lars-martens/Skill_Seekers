#!/usr/bin/env python3
"""
Simple rating/voting system for Skill Seeker configs.
Uses JSON file for persistent storage.
"""

import json
from pathlib import Path
from typing import Dict, Optional


class RatingsManager:
    """Manage config ratings and votes."""

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize ratings manager with storage path."""
        if storage_path is None:
            storage_path = Path(__file__).parent / "ratings_data.json"
        self.storage_path = storage_path
        self.ratings = self._load_ratings()

    def _load_ratings(self) -> Dict:
        """Load ratings from storage file."""
        if not self.storage_path.exists():
            return {}

        try:
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_ratings(self):
        """Save ratings to storage file."""
        with open(self.storage_path, 'w') as f:
            json.dump(self.ratings, f, indent=2)

    def get_rating(self, config_id: str) -> Dict:
        """Get rating info for a config."""
        if config_id not in self.ratings:
            return {
                "upvotes": 0,
                "downvotes": 0,
                "score": 0,
                "total_votes": 0
            }

        data = self.ratings[config_id]
        upvotes = data.get("upvotes", 0)
        downvotes = data.get("downvotes", 0)

        return {
            "upvotes": upvotes,
            "downvotes": downvotes,
            "score": upvotes - downvotes,
            "total_votes": upvotes + downvotes
        }

    def upvote(self, config_id: str) -> Dict:
        """Add an upvote to a config."""
        if config_id not in self.ratings:
            self.ratings[config_id] = {"upvotes": 0, "downvotes": 0}

        self.ratings[config_id]["upvotes"] += 1
        self._save_ratings()

        return self.get_rating(config_id)

    def downvote(self, config_id: str) -> Dict:
        """Add a downvote to a config."""
        if config_id not in self.ratings:
            self.ratings[config_id] = {"upvotes": 0, "downvotes": 0}

        self.ratings[config_id]["downvotes"] += 1
        self._save_ratings()

        return self.get_rating(config_id)

    def remove_upvote(self, config_id: str) -> Dict:
        """Remove an upvote from a config."""
        if config_id in self.ratings and self.ratings[config_id]["upvotes"] > 0:
            self.ratings[config_id]["upvotes"] -= 1
            self._save_ratings()

        return self.get_rating(config_id)

    def remove_downvote(self, config_id: str) -> Dict:
        """Remove a downvote from a config."""
        if config_id in self.ratings and self.ratings[config_id]["downvotes"] > 0:
            self.ratings[config_id]["downvotes"] -= 1
            self._save_ratings()

        return self.get_rating(config_id)

    def get_all_ratings(self) -> Dict[str, Dict]:
        """Get ratings for all configs."""
        return {
            config_id: self.get_rating(config_id)
            for config_id in self.ratings
        }

    def get_top_rated(self, limit: int = 10) -> list:
        """Get top-rated configs."""
        all_ratings = []
        for config_id in self.ratings:
            rating = self.get_rating(config_id)
            rating["config_id"] = config_id
            all_ratings.append(rating)

        # Sort by score (descending), then by total votes (descending)
        all_ratings.sort(key=lambda x: (x["score"], x["total_votes"]), reverse=True)

        return all_ratings[:limit]


if __name__ == "__main__":
    # Test the ratings system
    manager = RatingsManager()

    print("Testing Ratings Manager...")
    print("\n1. Upvoting 'react' config:")
    print(manager.upvote("react"))

    print("\n2. Getting 'react' rating:")
    print(manager.get_rating("react"))

    print("\n3. Downvoting 'vue' config:")
    print(manager.downvote("vue"))

    print("\n4. Getting all ratings:")
    print(json.dumps(manager.get_all_ratings(), indent=2))

    print("\n5. Top rated configs:")
    for rating in manager.get_top_rated():
        print(f"  {rating['config_id']}: {rating['score']} ({rating['upvotes']}↑ {rating['downvotes']}↓)")
