import logging
import os
import json

from dotenv import load_dotenv
from livekit.agents import (
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    WorkerOptions,
    cli,
    metrics,
)
from livekit.plugins import openai
from livekit.plugins import noise_cancellation, silero
from agents.CaseAgent import CaseAgent

logger = logging.getLogger("agent")

load_dotenv(".env.local")


def get_case() -> dict:
    """Sample case phases - in production, this would come from your case generation service"""
    return {
        "case_and_framework": {
            "Q": "Your client is a major retail chain experiencing declining profits over the past 2 years. The CEO has asked you to identify the root causes and develop recommendations. How would you structure your analysis?",
            "R": [
                "Is the framework MECE (Mutually Exclusive, Collectively Exhaustive)?",
                "Does it cover key profit drivers (revenue and costs)?", 
                "Shows structured thinking and logical flow?",
                "Includes external factors (market, competition)?"
            ]
        },
        "market_analysis": {
            "Q": "Based on the case information, what external market factors could be contributing to the profit decline? Walk me through your analysis.",
            "R": [
                "Identifies relevant market trends and dynamics",
                "Uses case facts appropriately to support analysis",
                "Shows analytical thinking and business judgment",
                "Considers multiple external factors systematically"
            ]
        },
        "calculation": {
            "Q": "The client is considering a 10% price increase across all products. If current annual revenue is $500M with 5% margins, calculate the impact on annual profit assuming demand decreases by 8%.",
            "R": [
                "Sets up the calculation correctly with clear assumptions",
                "Shows work step-by-step with proper units",
                "Arrives at the correct or nearly correct answer",
                "Performs sanity check on the result"
            ]
        },
        "strategy_question": {
            "Q": "Given your analysis, what are the top 3 strategic recommendations you would make to the CEO? Prioritize them and explain your reasoning.",
            "R": [
                "Provides clear, actionable recommendations",
                "Prioritizes recommendations with sound logic",
                "Connects recommendations to earlier analysis",
                "Shows strategic thinking and business acumen"
            ]
        },
        "conclusion": {
            "Q": "Please summarize your overall assessment and provide your final recommendation with implementation timeline.",
            "R": [
                "Starts with clear headline answer/recommendation",
                "Supports conclusion with 2-3 key points from analysis",
                "Addresses potential risks and next steps",
                "Shows executive-level communication skills"
            ]
        }
    }


def get_agent_configuration():
    """Get agent configuration from environment variables or defaults"""
    return {
        "case_id": os.getenv("CASE_ID", "retail_case_001"),
        "vs_dir": os.getenv("VECTOR_STORE_DIR", "./vector_store"),
        "case_data": get_case()
    }
    
def get_config_from_room_metadata(ctx: JobContext) -> dict:
    """Extract configuration from room metadata"""
    try:
        # Access room metadata
        existing_participants = list(ctx.room.remote_participants.values())
        if existing_participants:
            participant = existing_participants[0]
            metadata = json.loads(participant.metadata)

            # Extract uploadResult from metadata
            upload_result = metadata.get("uploadResult", {})
            
            if upload_result:
                config = {
                    "case_id": upload_result.get("case_id", os.getenv("CASE_ID", "retail_case_001")),
                    "vs_dir": upload_result.get("vs_dir", os.getenv("VECTOR_STORE_DIR", "./vector_store")),
                    "case_data": upload_result.get("case_data", get_case())
                }
                logger.info(f"Using config from upload result: case_id={config['case_id']}")
                return config
            else:
                logger.info("No uploadResult in metadata, using default configuration")
                return get_agent_configuration()
                
        else:
            logger.info("No room metadata found, using default configuration")
            return get_agent_configuration()
            
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse room metadata: {e}")
        return get_agent_configuration()
    except Exception as e:
        logger.error(f"Error extracting config from metadata: {e}")
        return get_agent_configuration()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx: JobContext):
    
    # Join the room and connect to the user
    await ctx.connect()
    
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Get agent configuration
    # Retrieve config from ctx in the future
    config = get_config_from_room_metadata(ctx)
    logger.info(f"Agent configuration: {config}")

    # Initialize the case agent
    try:
        case_agent = CaseAgent(
            case_id=config["case_id"],
            vs_dir=config["vs_dir"], 
            case_data=config["case_data"]
        )
        logger.info(f"Initialized CaseAgent with case_id: {config['case_id']}")
    except Exception as e:
        logger.error(f"Failed to initialize CaseAgent: {e}")
        logger.error(f"CaseAgent constructor received: case_id={config['case_id']}, vs_dir={config['vs_dir']}")
        logger.error(f"case_data structure: {config['case_data']}")
        # Don't continue if CaseAgent fails to initialize
        raise e

    # Set up a voice AI with OpenAI Realtime API
    session = AgentSession(
        llm=openai.realtime.RealtimeModel(voice="marin"),
    )

    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    # Start the session with the case interview agent
    await session.start(
        agent=case_agent,
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))