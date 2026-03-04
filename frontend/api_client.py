# frontend/api_client.py
import httpx
from typing import Optional, Dict, List, Any
import json


class APIClient:
    """HTTP client wrapper for backend API calls."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    # Session endpoints
    async def create_session(self) -> Dict:
        """Create a new session."""
        response = await self.client.post(f"{self.base_url}/sessions")
        response.raise_for_status()
        return response.json()

    async def get_session(self, code: str) -> Dict:
        """Get session by code."""
        response = await self.client.get(f"{self.base_url}/sessions/{code}")
        response.raise_for_status()
        return response.json()

    async def join_session(self, session_id: int, participant_data: Dict) -> Dict:
        """Join a session."""
        response = await self.client.post(
            f"{self.base_url}/sessions/{session_id}/join",
            json=participant_data
        )
        response.raise_for_status()
        return response.json()

    async def lock_session(self, session_id: int) -> Dict:
        """Lock a session for settlement."""
        response = await self.client.post(
            f"{self.base_url}/sessions/{session_id}/lock"
        )
        response.raise_for_status()
        return response.json()

    async def settle_session(self, session_id: int) -> Dict:
        """Mark session as settled."""
        response = await self.client.post(
            f"{self.base_url}/sessions/{session_id}/settle"
        )
        response.raise_for_status()
        return response.json()

    async def auto_assign(self, session_id: int) -> Dict:
        """Auto-assign items equally."""
        response = await self.client.post(
            f"{self.base_url}/sessions/{session_id}/auto-assign"
        )
        response.raise_for_status()
        return response.json()

    # Item endpoints
    async def add_item(self, session_id: int, item_data: Dict) -> Dict:
        """Add an item to session."""
        response = await self.client.post(
            f"{self.base_url}/sessions/{session_id}/items",
            json=item_data
        )
        response.raise_for_status()
        return response.json()

    async def add_items_bulk(self, session_id: int, items: List[Dict]) -> List[Dict]:
        """Add multiple items at once."""
        response = await self.client.post(
            f"{self.base_url}/sessions/{session_id}/items/bulk",
            json=items
        )
        response.raise_for_status()
        return response.json()

    async def update_item(self, item_id: int, item_data: Dict) -> Dict:
        """Update an item."""
        response = await self.client.patch(
            f"{self.base_url}/items/{item_id}",
            json=item_data
        )
        response.raise_for_status()
        return response.json()

    async def delete_item(self, item_id: int) -> Dict:
        """Delete an item."""
        response = await self.client.delete(
            f"{self.base_url}/items/{item_id}"
        )
        response.raise_for_status()
        return response.json()

    async def dispute_item(self, item_id: int, reason: str) -> Dict:
        """Flag item as disputed."""
        response = await self.client.post(
            f"{self.base_url}/items/{item_id}/dispute",
            json={"reason": reason}
        )
        response.raise_for_status()
        return response.json()

    # Assignment endpoints
    async def assign_item(self, item_id: int, assignment_data: Dict) -> Dict:
        """Assign item to participant."""
        response = await self.client.post(
            f"{self.base_url}/items/{item_id}/assign",
            json=assignment_data
        )
        response.raise_for_status()
        return response.json()

    async def remove_assignment(self, assignment_id: int) -> Dict:
        """Remove an assignment."""
        response = await self.client.delete(
            f"{self.base_url}/assignments/{assignment_id}"
        )
        response.raise_for_status()
        return response.json()

    # OCR endpoint
    async def process_receipt(self, image_bytes: bytes, filename: str = "receipt.jpg") -> Dict:
        """Process receipt image with OCR."""
        files = {"file": (filename, image_bytes, "image/jpeg")}
        response = await self.client.post(
            f"{self.base_url}/ocr",
            files=files
        )
        response.raise_for_status()
        return response.json()

    # Health check
    async def health_check(self) -> Dict:
        """Check API health."""
        response = await self.client.get(f"{self.base_url}/health")
        return response.json()


# Global API client instance
api_client = APIClient()
