# -*- coding: utf-8 -*-
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from arasCore.lib.services.workflow import WorkflowDef, TransitionDef, generate_mermaid
from arasCore.lib.services.openapi import generate_openapi_spec, _model_to_schema
from sqlalchemy import Column, Integer, String, Table, MetaData

class MockModel:
    __tablename__ = "mock_table"
    __name__ = "MockModel"
    metadata = MetaData()
    __table__ = Table(
        "mock_table", metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String(50), nullable=False),
        Column("description", String(200), nullable=True)
    )

class TestEnhancementsUnit(unittest.TestCase):
    def test_mermaid_generation(self):
        wf = WorkflowDef(
            name="test_wf",
            resource_key="test/res",
            states=["draft", "approved"],
            initial="draft",
            transitions=[
                TransitionDef("approve", "draft", "approved", roles=["admin"])
            ]
        )
        mermaid = generate_mermaid(wf)
        self.assertIn("stateDiagram-v2", mermaid)
        self.assertIn("[*] --> draft", mermaid)
        self.assertIn("draft --> approved: approve [admin]", mermaid)

    def test_model_to_schema(self):
        # We pass empty AppManagerColumn list for now
        schema = _model_to_schema(MockModel, [])
        self.assertEqual(schema["type"], "object")
        self.assertIn("id", schema["properties"])
        self.assertIn("name", schema["properties"])
        self.assertEqual(schema["properties"]["name"]["type"], "string")
        self.assertIn("name", schema["required"])
        self.assertNotIn("description", schema["required"])

if __name__ == "__main__":
    unittest.main()
