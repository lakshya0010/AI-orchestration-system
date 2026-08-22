import uuid
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.session import Session, SessionStatus
from app.models.agent_step import AgentStep, AgentRole, StepStatus
from app.services.agents import run_critic, run_executor, run_planner
from app.services.embeddings import get_embedding
from app.models.memory_entry import MemoryEntry

MAX_REPLANS = 3

async def get_relevent_memory(db, query_text: str) ->str|None:
    query_embedding = await get_embedding(query_text)
    result = await db.execute(
        select(MemoryEntry, MemoryEntry.embedding.cosine_distance(query_embedding).label("distance"))
        .order_by("distance")
        .limit(1)
    )
    row = result.first()
    if row is None:
        return None
    match, distance = row
    if distance>0.6:
        return None
    
    return match.content



async def run_orchestrator(session_id: uuid.UUID) -> str|None:
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Session).where(Session.id == session_id))
            session = result.scalar_one()

            memory_context = await get_relevent_memory(db, session.goal)

            replan_count = 0
            step_number = 1
            feedback = None

            while True:
                session.status = SessionStatus.PLANNING
                await db.commit()

                plan_prompt = session.goal
                if memory_context:
                    plan_prompt = f"Relevant past context: {memory_context}\n\nGoal: {session.goal}"
                if feedback:
                    plan_prompt += (
                        f"\n\nYour previous plan was:\n{plan_text}\n\n"
                        f"Step '{rejected_step}' failed with reason: {rejected_feedback}\n"
                        f"Generate a new COMPLETE plan from the start that avoids this issue. "
                        f"Do not reference the previous plan — return only the new full numbered list."
                    )
                

                plan_text = await run_planner(plan_prompt)

                if plan_text.strip().startswith("CLARIFY:"):
                    question = plan_text.split("CLARIFY:", 1)[1].strip()
                    session.status = SessionStatus.AWAITING_INPUT
                    await db.commit()
                    await _save_step(db, session.id, AgentRole.PLANNER, step_number, {"prompt_sent":plan_prompt}, {"question": question})
                    return

                if plan_text.strip().startswith("OUT_OF_SCOPE:"):
                    reason = plan_text.split("OUT_OF_SCOPE:", 1)[1].strip()
                    session.status = SessionStatus.FAILED
                    await db.commit()
                    await _save_step(db, session.id, AgentRole.PLANNER, step_number, {"prompt_sent":plan_prompt}, {"reason":reason})
                    return
                    
                steps = [s.strip() for s in plan_text.split("\n") if s.strip()]

                await _save_step(db, session.id, AgentRole.PLANNER, step_number, {"prompt_sent":plan_prompt}, {"plan":plan_text})
                step_number+=1

                rejected_step = None
                rejected_feedback = None

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
                        rejected_step = step
                        rejected_feedback = verdict
                        break

                if rejected_step is None:
                    memory = MemoryEntry(
                        content = session.goal,
                        embedding =await get_embedding(session.goal),
                    )
                    db.add(memory)
                    session.status = SessionStatus.DONE
                    await db.commit()
                    return 

                replan_count+=1
                if replan_count>MAX_REPLANS:
                    session.status = SessionStatus.FAILED
                    await db.commit()
                    return

                feedback = f"Step '{rejected_step}' was rejected: {rejected_feedback}"
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

            
