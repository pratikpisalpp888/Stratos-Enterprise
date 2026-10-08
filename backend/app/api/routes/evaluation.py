import json
import logging
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException
from app.evaluation.run_rag_evaluation import run_full_rag_evaluation
from app.evaluation.rbac_security_suite import run_rbac_security_suite
from app.evaluation.red_team_suite import run_red_team_suite

logger = logging.getLogger("app.api.routes.evaluation")

router = APIRouter(prefix="/evaluation", tags=["Evaluation Suite"])

REPORTS_DIR = Path(__file__).parent.parent.parent / "evaluation" / "reports"

@router.post("/run-full-suite")
def run_full_evaluation_suite():
    """
    Runs the complete 3-part evaluation pipeline:
    1. RAG Quality (Golden Dataset + Groq LLM-as-Judge)
    2. RBAC Security Matrix (50 combinations vs Independent Oracle)
    3. Automated Red-Teaming (15 adversarial attack vectors)
    """
    try:
        logger.info("Starting Full System Evaluation Suite...")
        
        # 1. RAG Quality Evaluation
        rag_res = run_full_rag_evaluation()
        
        # 2. RBAC Security Matrix Evaluation
        rbac_res = run_rbac_security_suite()
        
        # 3. Automated Red-Teaming
        red_team_res = run_red_team_suite()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report = {
            "timestamp": datetime.now().isoformat(),
            "rag_quality_evaluation": rag_res,
            "rbac_security_evaluation": rbac_res,
            "red_team_evaluation": red_team_res
        }

        # Save timestamped report to JSON
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        report_file = REPORTS_DIR / f"evaluation_report_{timestamp}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Full Evaluation Suite Completed! Report saved to {report_file}")
        return report

    except Exception as e:
        logger.error(f"Error running evaluation suite: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/latest-report")
def get_latest_evaluation_report():
    """
    Returns the most recently saved evaluation report JSON.
    """
    try:
        if not REPORTS_DIR.exists():
            raise HTTPException(status_code=404, detail="No evaluation reports found.")
            
        report_files = sorted(REPORTS_DIR.glob("evaluation_report_*.json"), reverse=True)
        if not report_files:
            raise HTTPException(status_code=404, detail="No evaluation reports found.")

        with open(report_files[0], "r", encoding="utf-8") as f:
            data = json.load(f)
            
        return data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
