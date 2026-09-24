import traceback

from src.agent.graph import build_graph_for_api
from src.db.database import SessionLocal
from src.db.models import Job

from src.utils.charts import normalize_generated_charts


def create_initial_state(
    job_id,
    saved_path,
    question,
    target_column,
):
    """
    Create the initial state required by
    the LangGraph AutoAnalyst workflow.
    """

    return {
        "question": question,
        "plan": [],
        "required_agents": [],

        "data_findings": "",
        "research_findings": "",

        "report": "",
        "critique": "",

        "approved": False,
        "revision_count": 0,

        "human_decision": "",
        "human_notes": "",

        "explanations": [],
        "generated_charts": [],

        "raw_path": str(saved_path),
        "clean_path": "",

        "target_col": target_column or "",
        "dataset_type": "",
        "id_cols": [],

        "needs_interpretability": True,

        "model_path": "",
        "model_name": "",
        "feature_importance": [],

        "job_id": job_id,

        "messages": [],
    }


def run_pipeline(
    job_id,
    saved_path,
    question,
    target_column,
):
    """
    Execute the AutoAnalyst LangGraph workflow
    for a specific job.
    """

    db = SessionLocal()

    try:
        # --------------------------------------------------
        # Get job
        # --------------------------------------------------

        job = (
            db.query(Job)
            .filter(Job.id == job_id)
            .first()
        )

        if not job:
            return

        # --------------------------------------------------
        # Mark job as running
        # --------------------------------------------------

        job.status = "running"
        job.error = None

        db.commit()

        # --------------------------------------------------
        # Build LangGraph workflow
        # --------------------------------------------------

        app_graph = build_graph_for_api()

        # --------------------------------------------------
        # Create initial state
        # --------------------------------------------------

        initial_state = create_initial_state(
            job_id=job_id,
            saved_path=saved_path,
            question=question,
            target_column=target_column,
        )

        # --------------------------------------------------
        # LangGraph configuration
        # --------------------------------------------------

        config = {
            "configurable": {
                "thread_id": job_id
            }
        }

        # --------------------------------------------------
        # Execute workflow
        # --------------------------------------------------

        final_state = app_graph.invoke(
            initial_state,
            config=config,
        )

        # --------------------------------------------------
        # Save results
        # --------------------------------------------------

        job.status = "awaiting_approval"

        job.report = final_state.get(
            "report",
            "",
        )

        job.critique = final_state.get(
            "critique",
            "",
        )

        job.approved_by_critic = (
            final_state.get(
                "approved",
                False,
            )
        )

        job.revision_count = str(
            final_state.get(
                "revision_count",
                0,
            )
        )

        job.dataset_type = final_state.get(
            "dataset_type",
            "",
        )

        job.model_name = final_state.get(
            "model_name",
            "",
        )

        job.explanations = final_state.get(
            "explanations",
            [],
        )

        job.generated_charts = (
            normalize_generated_charts(
                final_state.get(
                    "generated_charts",
                    [],
                )
            )
        )

        db.commit()

    except Exception as exc:

        # --------------------------------------------------
        # Mark job as failed
        # --------------------------------------------------

        job = (
            db.query(Job)
            .filter(Job.id == job_id)
            .first()
        )

        if job:
            job.status = "failed"
            job.error = str(exc)

            db.commit()

        traceback.print_exc()

    finally:
        db.close()