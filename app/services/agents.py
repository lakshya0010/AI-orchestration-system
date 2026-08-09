from app.services.llm import call_llm

async def run_planner(goal:str)->str:
    prompt = f"""You are a planning agent. Break this goal into a numbered list of concrete steps.
Goal: {goal}
Return only the numbered list."""
    return await call_llm(prompt)

async def run_executor(step:str, context: str = "")->str:
    prompt = f"""You are an executor agent. Complete this specific step.
Step: {step}
Context so far: {context}
Return only your result for this step."""
    return await call_llm(prompt)

async def run_critic(step:str, output:str)->str:
    prompt = f"""You are a critic agent. Judge if this output actually completes the step.
Step: {step}
Output: {output}
Reply with exactly one word: APPROVE or REJECT, followed by a one-line reason."""
    return await call_llm(prompt)


