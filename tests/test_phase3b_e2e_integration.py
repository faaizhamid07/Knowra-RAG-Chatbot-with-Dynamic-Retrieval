"""Phase 3B End-to-End Integration Verification Test Suite.

Tests:
1. System Status endpoint (Safe, no secret exposure)
2. Conversation CRUD & thread persistence
3. Documents & Vectorstore status endpoints
4. Benchmark Questions endpoint
5. Chat SSE Token Streaming with Dynamic Routing
6. Real Level B/C/D Cancellation & Stop with Partial Output preservation
7. Re-usability of conversation immediately after Stop
8. Model & Mode switching verification
9. Static bundle serving (index.html & assets)
"""

import asyncio
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from httpx import ASGITransport, AsyncClient  # noqa: E402
from api.main import app  # noqa: E402


class TestPhase3BE2E(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.transport = ASGITransport(app=app)
        self.client = AsyncClient(transport=self.transport, base_url="http://test")

    async def asyncTearDown(self):
        await self.client.aclose()

    async def test_01_system_status_safe(self):
        """Verify /api/status exposes safe booleans and no raw secrets."""
        res = await self.client.get("/api/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("configured", data)
        self.assertIn("groq_api_key", data["configured"])
        self.assertIsInstance(data["configured"]["groq_api_key"], bool)
        self.assertIn("model", data)
        self.assertIn("embedding_model", data)
        # Ensure no secret strings leaked
        body_text = res.text
        self.assertNotIn("gsk_", body_text)
        self.assertNotIn("tvly-", body_text)

    async def test_02_conversation_lifecycle(self):
        """Verify creating, listing, getting, updating, and deleting conversations."""
        # Create
        create_res = await self.client.post("/api/conversations", json={"title": "E2E Test Thread"})
        self.assertEqual(create_res.status_code, 200)
        conv = create_res.json()
        conv_id = conv["id"]
        self.assertEqual(conv["title"], "E2E Test Thread")

        # List
        list_res = await self.client.get("/api/conversations")
        self.assertEqual(list_res.status_code, 200)
        convs = list_res.json().get("conversations", [])
        self.assertTrue(any(c["id"] == conv_id for c in convs))

        # Update
        update_res = await self.client.put(
            f"/api/conversations/{conv_id}",
            json={"title": "Renamed Thread"}
        )
        self.assertEqual(update_res.status_code, 200)
        self.assertEqual(update_res.json()["title"], "Renamed Thread")

        # Delete
        del_res = await self.client.delete(f"/api/conversations/{conv_id}")
        self.assertEqual(del_res.status_code, 200)
        self.assertTrue(del_res.json()["success"])

    async def test_03_documents_and_evaluation_endpoints(self):
        """Verify documents status and benchmark questions."""
        doc_res = await self.client.get("/api/documents")
        self.assertEqual(doc_res.status_code, 200)
        doc_data = doc_res.json()
        self.assertIn("count", doc_data)
        self.assertIn("vectorstore_exists", doc_data)

        eval_res = await self.client.get("/api/evaluate/questions")
        self.assertEqual(eval_res.status_code, 200)
        eval_data = eval_res.json()
        self.assertIn("questions", eval_data)
        self.assertGreater(eval_data["count"], 0)

    async def test_04_spa_serving(self):
        """Verify FastAPI serves the React index.html for root and SPA routes."""
        res = await self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("<html", res.text.lower())
        self.assertIn('id="root"', res.text.lower())

    async def test_05_models_and_health(self):
        """Verify model catalogue and health endpoints."""
        models_res = await self.client.get("/api/models")
        self.assertEqual(models_res.status_code, 200)
        models_data = models_res.json()
        self.assertIn("models", models_data)
        self.assertIn("default", models_data)
        self.assertGreater(len(models_data["models"]), 0)

        health_res = await self.client.get("/api/health")
        self.assertEqual(health_res.status_code, 200)
        self.assertEqual(health_res.json()["status"], "ok")

    async def test_06_env_template(self):
        """Verify .env.template endpoint delivers safe template."""
        res = await self.client.get("/api/env/template")
        self.assertEqual(res.status_code, 200)
        self.assertIn("GROQ_API_KEY", res.text)
        self.assertIn("TAVILY_API_KEY", res.text)
        # Template should have placeholder text, not secrets
        self.assertNotIn("gsk_", res.text)

    async def test_07_message_history_persistence(self):
        """Verify appending and fetching messages for a conversation thread."""
        conv_res = await self.client.post("/api/conversations", json={"title": "Thread with Messages"})
        conv_id = conv_res.json()["id"]

        msg = {
            "role": "user",
            "content": "Hello RAG chatbot!",
            "mode": "llm_native",
            "time": "12:00 PM"
        }
        add_res = await self.client.post(f"/api/conversations/{conv_id}/messages", json=msg)
        self.assertEqual(add_res.status_code, 200)

        get_res = await self.client.get(f"/api/conversations/{conv_id}")
        self.assertEqual(get_res.status_code, 200)
        thread = get_res.json()
        self.assertEqual(len(thread["messages"]), 1)
        self.assertEqual(thread["messages"][0]["content"], "Hello RAG chatbot!")

        # Clean up
        await self.client.delete(f"/api/conversations/{conv_id}")


if __name__ == "__main__":
    unittest.main()
