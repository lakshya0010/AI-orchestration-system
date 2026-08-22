from app.services.llm import call_llm

async def run_planner(goal:str)->str:
    prompt = f"""You are a planning agent. 
If the goal is missing critical information you need to proceed (budget, preferences, specifics), respond with exactly:
CLARIFY: <your question>

If the goal requires an action you cannot actually perform (e.g. real purchases, sending real emails, accessing external accounts) — you only have web search and reasoning available, no real-world transaction ability — respond with exactly:
OUT_OF_SCOPE: <explanation>

Otherwise, break the goal into a numbered list of concrete steps you CAN actually complete with reasoning and information only.
Goal: {goal}"""
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


