# backend/app/agent/agent_loop.py
from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
import asyncio, httpx, json, re

from backend.app.config import get_settings
from backend.app.agents.tools import (
    WeatherArgs, SoilArgs, MarketArgs, SatelliteArgs, RagArgs,            # + RagArgs
    tool_weather, tool_soil, tool_market,  tool_satellite, tool_rag,     # + tool_rag
    TOOL_DESCRIPTIONS, SATELLITE_ENABLED
)


# ---------------- Gemini caller (plain text, no MIME tricks) ----------------
async def _gemini_text_call(prompt: str, *, timeout: float = 15.0) -> str:
    s = get_settings()
    model = "gemini-2.5-flash"  # per request
    endpoint = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent"
    params = {"key": s.gemini_api_key}
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "topP": 0.9,
            "maxOutputTokens": 512
        }
    }
    async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
        r = await client.post(endpoint, params=params, json=payload)
        r.raise_for_status()
        data = r.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        raise RuntimeError(f"planner LLM unexpected schema: {e}")

# --------------- Loose JSON extraction (fence or brace-scan) ----------------
def _extract_json_loose(text: str) -> dict:
    if not text:
        raise ValueError("empty planner response")
    # ```json ... ```
    fence = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fence:
        return json.loads(fence.group(1))

    # brace-scan first top-level object
    start = text.find("{")
    while start != -1:
        depth = 0
        for i in range(start, len(text)):
            ch = text[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start:i+1]
                    try:
                        return json.loads(candidate)
                    except Exception:
                        break  # move to next {
        start = text.find("{", start + 1)

    raise ValueError("no JSON object found in planner response")

# ----------------------------- Agent data model -----------------------------
class AgentState(BaseModel):
    question: str
    target_language: str = "en"
    lat: float | None = None
    lon: float | None = None
    district: str | None = None
    commodity: str | None = None
    mandi: str | None = None

    # NEW
    preferred_commodities: list[str] | None = None
    preferred_mandi: str | None = None

    steps: List[Dict[str, Any]] = []
    final_answer: str | None = None
    error: str | None = None
    max_steps: int = 3                     # keep responses quick

# ------------------------------ Planner prompt ------------------------------
def planner_prompt(state: AgentState) -> str:
    hints = []
    if state.lat is not None and state.lon is not None:
        hints.append(f"coords=({state.lat},{state.lon})")
    if state.district: hints.append(f"district={state.district}")
    if state.commodity: hints.append(f"commodity={state.commodity}")
    if state.mandi: hints.append(f"mandi={state.mandi}")
    if state.preferred_commodities: hints.append(f"preferred={state.preferred_commodities[:5]}")
    if state.preferred_mandi: hints.append(f"default_mandi={state.preferred_mandi}")

    tools = {k: v for k, v in TOOL_DESCRIPTIONS.items()
             if (k != "satellite" or SATELLITE_ENABLED)}

    return f"""You are KrishiMitra, a farm advisor agent.
Question: {state.question}
Context hints: {", ".join(hints) if hints else "none"}

Available tools (choose only if useful):
{json.dumps(tools, ensure_ascii=False)}

Return STRICT JSON ONLY as ONE of:
{{"action":"final","answer":"..."}}
or
{{"action":"tool","name":"weather|soil|market|recos|rag{"|satellite" if SATELLITE_ENABLED else ""}","args":{{...}}}}
or
{{"action":"tools","calls":[{{"name":"weather","args":{{"lat":...,"lon":...}}}}, ...]}}

Guidelines:
- Prefer the farmer's preferred commodities and default mandi when using market/forecast.
- Use lat/lon for weather/soil/recos/satellite; district (+optional mandi) for market.
- Keep toolset minimal; avoid redundant calls.
JSON only—no explanations.
"""

# ----------------------------- Execute one step -----------------------------
async def _run_tool(name: str, args: dict) -> Dict[str, Any] | List[Dict[str, Any]]:
    try:
        if name == "weather":
            return await tool_weather(WeatherArgs(**args))
        elif name == "soil":
            return await tool_soil(SoilArgs(**args))
        elif name == "market":
            return await tool_market(MarketArgs(**args))
        # elif name == "recos":
        #     return await tool_recos(RecosArgs(**args))
        elif name == "satellite" and SATELLITE_ENABLED:
            return await tool_satellite(SatelliteArgs(**args))
        elif name == "rag":
            return await tool_rag(RagArgs(**args))
        else:
            return {"error": "unknown_or_disabled_tool"}
    except Exception as e:
        return {"error": str(e)}


async def execute_one(state: AgentState) -> AgentState:
    plan_text = await _gemini_text_call(planner_prompt(state), timeout=15.0)
    try:
        obj = _extract_json_loose(plan_text)
    except Exception as e:
        state.error = f"planner_parse_failed: {e}"
        return state

    if obj.get("action") == "final":
        state.final_answer = str(obj.get("answer") or "").strip()
        return state

    if obj.get("action") == "tool":
        name = obj.get("name")
        args = obj.get("args") or {}

        # 🔹 Auto-fill market args from prefs
        if name == "market":
            if "district" not in args and state.district:
                args["district"] = state.district
            if "mandi" not in args and state.preferred_mandi:
                args["mandi"] = state.preferred_mandi
            # If no commodity specified, run the first preferred (keeps payload small)
            # (Agent can also choose multiple via "tools" to fetch many.)
            if not args.get("commodity") and state.preferred_commodities:
                args["commodity"] = state.preferred_commodities[0]

        res = await _run_tool(name, args)
        state.steps.append({"tool": name, "args": args, "result": res})
        return state

    if obj.get("action") == "tools":
        calls = obj.get("calls") or []
        MAX_PARALLEL = 4
        sem = asyncio.Semaphore(MAX_PARALLEL)

        async def guarded(call: dict):
            async with sem:
                name = call.get("name")
                args = call.get("args") or {}
                # 🔹 Auto-fill for each market call in batch
                if name == "market":
                    if "district" not in args and state.district:
                        args["district"] = state.district
                    if "mandi" not in args and state.preferred_mandi:
                        args["mandi"] = state.preferred_mandi
                    if not args.get("commodity") and state.preferred_commodities:
                        # rotate through up to 5 preferred commodities if no commodity provided
                        # (optional) here we just pick the first; planner can create multiple calls explicitly
                        args["commodity"] = state.preferred_commodities[0]
                res = await _run_tool(name, args)
                return {"tool": name, "args": args, "result": res}

        results = await asyncio.gather(*(guarded(c) for c in calls))
        state.steps.extend(results)
        return state

    state.error = "planner_bad_action"
    return state


# ----------------------------- Finalization step ----------------------------
def _summarize_steps(steps: List[Dict[str, Any]]) -> str:
    parts = []
    for st in steps:
        name = st.get("tool"); res = st.get("result") or {}
        if name == "weather":
            cur = res.get("current") or {}
            daily_forecasts = res.get("daily") or []
            
            # --- List to hold all lines of the summary ---
            weather_lines = []
            
            # --- 1. Current Weather & 24h Summary ---
            temp_c = cur.get('temperature_c', 'N/A')
            wind_ms = cur.get('wind_speed_ms', 'N/A')
            humidity_pct = cur.get('humidity_pct', 'N/A')
            rain_mm_now = cur.get('rain_mm', 'N/A')
            next_24h_rain_mm = res.get('next24h_total_rain_mm', 'N/A')
            
            weather_lines.append(f"Weather Now: {temp_c}°C, {humidity_pct}% RH, {rain_mm_now}mm rain, {wind_ms} m/s wind.")
            weather_lines.append(f"Total rainfall expected (next 24h): {next_24h_rain_mm}mm")
        
            # --- 2. Daily Forecast Loop (All 7 days) ---
            if daily_forecasts:
                weather_lines.append("\n--- 7-Day Forecast ---")
                
                for i, day in enumerate(daily_forecasts):
                    # Get all data points from the daily object
                    date_str = day.get('date', 'N/A')
                    tmax_c = day.get('tmax_c', 'N/A')
                    tmin_c = day.get('tmin_c', 'N/A')
                    precip_mm = day.get('precip_mm', 'N/A')
                    humidity_mean_pct = day.get('humidity_mean_pct', 'N/A')
                    rain_mm = day.get('rain_mm', 'N/A')
                    rain_chance_pct = day.get('rain_chance_pct', 'N/A')
        
                    # Add a "Today" label for the first day for clarity
                    date_label = f"Today ({date_str})" if i == 0 else date_str
        
                    # Format each day's entry for readability
                    # Using newlines and indentation for a cleaner look
                    day_summary = [
                        f"{date_label}:",
                        f"  - Temp: {tmax_c}°C (Hi) / {tmin_c}°C (Lo)",
                        f"  - Rain: {rain_mm}mm ({rain_chance_pct}% chance)",
                        f"  - Total Precip: {precip_mm}mm",
                        f"  - Avg Humidity: {humidity_mean_pct}%"
                    ]
                    weather_lines.append("\n".join(day_summary))
            
            # --- 3. Append to parts ---
            # Join all lines with newlines to create one single, readable block
            parts.append("\n".join(weather_lines))
        elif name == "soil":
            top = res.get("topsoil") or {}
            parts.append(f"Soil pH {top.get('ph_h2o')}, SOC {top.get('soc_g_per_kg')} g/kg, N {top.get('nitrogen_g_per_kg')} g/kg")
        elif name == "market":
            rows = res if isinstance(res, list) else []
            if rows:
                parts.append("Market " + ", ".join(f"{r.get('commodity')} ₹{r.get('price')/100} per kg" for r in rows[:3]))
        elif name == "recos":
            rec = res if isinstance(res, list) else []
            if rec:
                parts.append("Top crops " + ", ".join(f"{r.get('crop')} {(r.get('probability',0)*100):.0f}%" for r in rec))
        elif name == "satellite":
            parts.append("Satellite indices fetched")
        elif name == "rag":
            hits = res if isinstance(res, list) else []
            if hits:
                titles = [h.get("title") or h.get("source") for h in hits[:3] if h]
                parts.append("RAG: " + ", ".join(t for t in titles if t))
    return "; ".join(parts) if parts else "no tool data"

async def _finalize_answer(state: AgentState) -> str:
    # Use your existing prose caller (from crop_recommendation)
    from backend.app.services.crop_recommendation import _gemini_call as gemini_call
    context = _summarize_steps(state.steps)
    prompt = f"""You are KrishiMitra. The user asked: {state.question}
Use these tool results: {context}
Answer concisely in {state.target_language}. If some data is missing, state assumptions briefly."""
    # run in thread as it's sync httpx in your service
    return await asyncio.wait_for(asyncio.to_thread(gemini_call, prompt), timeout=25.0)

# ------------------------------- Public API --------------------------------
async def run_agent_once(
    question: str,
    *,
    target_language: str = "en",
    lat: float | None = None, lon: float | None = None,
    district: str | None = None, commodity: str | None = None, mandi: str | None = None,
    preferred_commodities: list[str] | None = None,   # NEW
    preferred_mandi: str | None = None,               # NEW
    max_steps: int = 3,
) -> Dict[str, Any]:
    state = AgentState(
        question=question, target_language=target_language,
        lat=lat, lon=lon, district=district, commodity=commodity, mandi=mandi,
        preferred_commodities=preferred_commodities, preferred_mandi=preferred_mandi,  # NEW
        max_steps=max_steps,
    )

    for _ in range(state.max_steps):
        state = await execute_one(state)
        if state.error:
            # graceful fallback: summarize whatever we have (if any), otherwise message
            if state.steps:
                try:
                    ans = await _finalize_answer(state)
                    return {"answer": ans, "used_steps": state.steps, "error": None}
                except Exception:
                    pass
            return {"answer": "Sorry, I couldn't complete the task.", "used_steps": state.steps, "error": state.error}
        if state.final_answer:
            return {"answer": state.final_answer, "used_steps": state.steps, "error": None}

        # After at least one tool step, try to finalize
        if state.steps:
            try:
                ans = await _finalize_answer(state)
                return {"answer": ans, "used_steps": state.steps, "error": None}
            except Exception as e:
                state.error = f"final_llm_failed: {e}"
                return {"answer": "Sorry, I couldn't complete the task.", "used_steps": state.steps, "error": state.error}

    # safety net
    if state.steps:
        try:
            ans = await _finalize_answer(state)
            return {"answer": ans, "used_steps": state.steps, "error": None}
        except Exception as e:
            return {"answer": "Sorry, I couldn't complete the task.", "used_steps": state.steps, "error": f"final_llm_failed: {e}"}

    return {"answer": "Sorry, I couldn't complete the task.", "used_steps": [], "error": "no_steps"}
