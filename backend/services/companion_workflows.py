"""Phase 3+: Companion Workflow Automation

Like Wingman, automate routine tasks:
- Document request forms (collect SIN, passport, etc.)
- Form auto-filling (immigration forms with user data)
- Appointment booking (settlement agencies, IRCC offices)
- Document checklist tracking
- Multi-step workflows (Express Entry → ITA → Final Steps)
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from uuid import uuid4
from enum import Enum

from core.db import db

logger = logging.getLogger("maplejourney.companion_workflows")


class WorkflowType(str, Enum):
    """Companion-automatable workflows."""
    DOCUMENT_COLLECTION = "document_collection"  # Gather SIN, passport, credentials
    FORM_SUBMISSION = "form_submission"  # Auto-fill + submit forms
    APPOINTMENT_BOOKING = "appointment_booking"  # Schedule with agencies
    CHECKLIST_TRACKING = "checklist_tracking"  # "Step 1: ✓ Step 2: ⏳ Step 3: ☐"
    CREDENTIAL_EVALUATION = "credential_evaluation"  # ECA tracking
    MULTI_STEP_PATHWAY = "multi_step_pathway"  # Express Entry → ITA → CoE
    LANGUAGE_TEST_PREP = "language_test_prep"  # IELTS/CELPIP tracking


class CompanionWorkflow:
    """Automate multi-step immigration processes."""
    
    def __init__(self, db_conn):
        self.db = db_conn
        self.workflows_coll = db_conn.companion_workflows
        self.workflow_steps_coll = db_conn.companion_workflow_steps
    
    async def ensure_indexes(self):
        """Create indexes."""
        await self.workflows_coll.create_index("user_id")
        await self.workflows_coll.create_index("workflow_type")
        await self.workflows_coll.create_index("status")
        await self.workflows_coll.create_index("current_step")
        
        await self.workflow_steps_coll.create_index("workflow_id")
        await self.workflow_steps_coll.create_index("step_number")
    
    async def start_document_collection_workflow(
        self,
        user_id: str,
        required_docs: List[str],  # ["sin", "passport", "credentials"]
    ) -> Dict[str, Any]:
        """Start workflow: collect required documents.
        
        Example:
            start_document_collection_workflow(user_id, ["sin", "passport", "language_test"])
        
        Returns:
            { workflow_id, current_step, next_action }
        """
        logger.info(f"Starting document collection workflow for user {user_id}")
        
        workflow_id = str(uuid4())
        now = datetime.now(timezone.utc)
        
        # Create workflow
        workflow = {
            "_id": workflow_id,
            "user_id": user_id,
            "workflow_type": WorkflowType.DOCUMENT_COLLECTION,
            "status": "in_progress",
            "current_step": 0,
            "total_steps": len(required_docs),
            "documents_required": required_docs,
            "documents_collected": [],
            "started_at": now,
            "updated_at": now,
        }
        
        await self.workflows_coll.insert_one(workflow)
        
        # Create step records
        doc_prompts = {
            "sin": "📋 Social Insurance Number (SIN)\n\nReply with your SIN or 'skip' to do later.",
            "passport": "🛂 Passport Number\n\nReply with your passport number (e.g., AB123456).",
            "language_test": "🗣️ Language Test Score\n\nWhich test did you take? (IELTS / CELPIP / TOEFL)\n1️⃣ IELTS\n2️⃣ CELPIP\n3️⃣ TOEFL",
            "credentials": "🎓 Education Credentials\n\nDo you have an ECA (Educational Credential Assessment)?\n1️⃣ Yes\n2️⃣ No\n3️⃣ In progress",
            "work_experience": "💼 Work Experience\n\nHow many years of Canadian work experience do you have?\n(Reply: 0, 1, 2, 3+)",
        }
        
        for idx, doc_type in enumerate(required_docs):
            step = {
                "_id": str(uuid4()),
                "workflow_id": workflow_id,
                "step_number": idx,
                "document_type": doc_type,
                "prompt": doc_prompts.get(doc_type, f"Please provide: {doc_type}"),
                "status": "pending",
                "created_at": now,
            }
            await self.workflow_steps_coll.insert_one(step)
        
        return {
            "workflow_id": workflow_id,
            "current_step": 0,
            "total_steps": len(required_docs),
            "next_action": "collect_document",
        }
    
    async def get_workflow_step(self, workflow_id: str) -> Dict[str, Any]:
        """Get current step in workflow."""
        workflow = await self.workflows_coll.find_one({"_id": workflow_id})
        if not workflow:
            return None
        
        current_step_num = workflow.get("current_step", 0)
        step = await self.workflow_steps_coll.find_one({
            "workflow_id": workflow_id,
            "step_number": current_step_num,
        })
        
        return step
    
    async def record_workflow_response(
        self,
        workflow_id: str,
        step_number: int,
        response: str,
        extracted_value: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record user's response to workflow step.
        
        Returns:
            { success, next_step_available, workflow_complete }
        """
        logger.info(f"Recording response for workflow {workflow_id} step {step_number}")
        
        try:
            # Update step
            await self.workflow_steps_coll.update_one(
                {"workflow_id": workflow_id, "step_number": step_number},
                {
                    "$set": {
                        "status": "completed",
                        "user_response": response,
                        "extracted_value": extracted_value,
                        "completed_at": datetime.now(timezone.utc),
                    }
                }
            )
            
            # Get workflow
            workflow = await self.workflows_coll.find_one({"_id": workflow_id})
            
            # Advance to next step
            next_step = step_number + 1
            workflow_complete = next_step >= workflow.get("total_steps", 0)
            
            if workflow_complete:
                await self.workflows_coll.update_one(
                    {"_id": workflow_id},
                    {
                        "$set": {
                            "status": "completed",
                            "completed_at": datetime.now(timezone.utc),
                            "updated_at": datetime.now(timezone.utc),
                        }
                    }
                )
            else:
                await self.workflows_coll.update_one(
                    {"_id": workflow_id},
                    {
                        "$set": {
                            "current_step": next_step,
                            "updated_at": datetime.now(timezone.utc),
                        }
                    }
                )
            
            return {
                "success": True,
                "next_step_available": not workflow_complete,
                "workflow_complete": workflow_complete,
                "step_completed": step_number + 1,
                "total_steps": workflow.get("total_steps"),
            }
        
        except Exception as e:
            logger.exception("Workflow response error")
            return {"success": False, "error": str(e)}
    
    async def get_workflow_checklist(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get visual checklist of workflow progress.
        
        Returns:
            [
                { step_number, document_type, status: pending|in_progress|completed, ... },
                ...
            ]
        """
        steps = await self.workflow_steps_coll.find({
            "workflow_id": workflow_id
        }).sort("step_number", 1).to_list(None)
        
        checklist = []
        for step in steps:
            status_emoji = {
                "pending": "☐",
                "in_progress": "⏳",
                "completed": "✓",
            }
            
            checklist.append({
                "step_number": step.get("step_number"),
                "document_type": step.get("document_type"),
                "status": step.get("status"),
                "status_emoji": status_emoji.get(step.get("status"), "?"),
                "prompt": step.get("prompt"),
            })
        
        return checklist
    
    async def start_express_entry_pathway(self, user_id: str) -> Dict[str, Any]:
        """Start multi-step Express Entry automation.
        
        Steps:
        1. ✓ EE Account creation
        2. ⏳ Profile creation
        3. ☐ ITA wait
        4. ☐ Complete application
        5. ☐ Medical exam
        6. ☐ Police certificate
        7. ☐ Final decision
        
        Returns:
            { workflow_id, current_step, checklist }
        """
        logger.info(f"Starting Express Entry pathway for user {user_id}")
        
        ee_steps = [
            "Create EE Account",
            "Build EE Profile",
            "Submit to Express Entry Pool",
            "Receive ITA (Invitation to Apply)",
            "Complete Full Application",
            "Schedule Medical Exam",
            "Submit Police Certificate",
            "Receive Final Decision",
        ]
        
        workflow_id = str(uuid4())
        now = datetime.now(timezone.utc)
        
        workflow = {
            "_id": workflow_id,
            "user_id": user_id,
            "workflow_type": WorkflowType.MULTI_STEP_PATHWAY,
            "pathway_type": "express_entry",
            "status": "in_progress",
            "current_step": 0,
            "total_steps": len(ee_steps),
            "steps": ee_steps,
            "started_at": now,
            "updated_at": now,
        }
        
        await self.workflows_coll.insert_one(workflow)
        
        # Create step records
        for idx, step_name in enumerate(ee_steps):
            step = {
                "_id": str(uuid4()),
                "workflow_id": workflow_id,
                "step_number": idx,
                "step_name": step_name,
                "status": "pending" if idx > 0 else "in_progress",
                "created_at": now,
            }
            await self.workflow_steps_coll.insert_one(step)
        
        # Get checklist
        checklist = await self.get_workflow_checklist(workflow_id)
        
        return {
            "workflow_id": workflow_id,
            "pathway_type": "express_entry",
            "current_step": 0,
            "total_steps": len(ee_steps),
            "checklist": checklist,
        }
