import uuid
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.session import Session, SessionStatus
from app.models.agent_step import AgentStep, AgentRole, StepStatus
from app.services.agents import run_critic, run_executor, run_planner

MAX_REPLANS = 3

async def run_orchestrator(session_id: uuid.UUID):
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Session).where(Session.id == session_id))
            session = result.scalar_one()

            replan_count = 0
            step_number = 1

            while True:
                session.status = SessionStatus.PLANNING
                await db.commit()

                plan_text = await run_planner(session.goal)
                steps = [s.strip() for s in plan_text.split("\n") if s.strip()]

                await _save_step(db, session.id, AgentRole.PLANNER, step_number, {"goal":session.goal}, {"plan":plan_text})

                step_number+=1

                all_approved = True

                for step in steps:
                    session.status = SessionStatus.EXECUTING
                    await db.commit()

                    exec_output = await run_executor(step, session.goal)
                    await _save_step(db, session.id, AgentRole.EXECUTOR, step_number, {"step":step}, {"result":exec_output})
                    step_number+=1

                    session.status = SessionStatus.CRITIQUING
                    await db.commit()

                    verdict = await run_critic(step, exec_output)
                    approved = verdict.strip().upper().startswith("APPROVE")
                    await _save_step(db, session.id, AgentRole.CRITIC, step_number, {"step":step, "output":exec_output}, {"verdict":verdict})
                    step_number+=1

                    if not approved:
                        all_approved = False
                        break

                if all_approved:
                    session.status = SessionStatus.DONE
                    await db.commit()
                    return

                replan_count+=1
                if replan_count>MAX_REPLANS:
                    session.status = SessionStatus.FAILED
                    await db.commit()
                    return

                session.status = SessionStatus.REPLANNING
                await db.commit()
        except Exception as e:
            session.status = SessionStatus.FAILED
            await db.commit()
            await _save_step(
                db, session_id, AgentRole.CRITIC, 9999,
                {"error": "orchestration crashed"},
                {"exception": str(e)},
            )
            raise


async def _save_step(db, session_id, role, step_number, input_data, output_data):
    step = AgentStep(
        session_id=session_id,
        role=role,
        step_number=step_number,
        input=input_data,
        output=output_data,
        status=StepStatus.COMPLETED,
    )
    db.add(step)
    await db.commit()

            
