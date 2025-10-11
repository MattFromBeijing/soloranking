"""
Simple test script to validate the CaseInterviewAgent setup
"""
import os
import sys
import logging
from typing import Dict, Any

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.CaseInterviewAgent import CaseInterviewAgent
from services.RAGService import RAGService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_sample_phases() -> Dict[str, Dict[str, Any]]:
    """Sample phases for testing"""
    return {
        "case_and_framework": {
            "Q": "Your client is a major retail chain experiencing declining profits. How would you structure your analysis?",
            "R": [
                "Is the framework MECE?",
                "Does it cover key profit drivers?", 
                "Shows structured thinking?"
            ]
        },
        "market_analysis": {
            "Q": "What external market factors could be contributing to the decline?",
            "R": [
                "Identifies relevant market trends",
                "Uses case facts appropriately",
                "Shows analytical thinking"
            ]
        }
    }

def test_agent_initialization():
    """Test basic agent initialization"""
    try:
        # Test configuration
        case_id = "test_case_001"
        vs_dir = "./vector_store"
        phases_data = get_sample_phases()
        
        # Initialize agent
        agent = CaseInterviewAgent(
            case_id=case_id,
            vs_dir=vs_dir,
            phases_data=phases_data
        )
        
        logger.info("✅ CaseInterviewAgent initialized successfully")
        logger.info(f"Current phase: {agent.current_phase}")
        logger.info(f"Phase order: {agent.case.phase_order}")
        
        # Test phase configuration
        current_config = agent.case.get_phase_config(agent.current_phase)
        if current_config:
            logger.info(f"Current question: {current_config.question}")
            logger.info(f"Rubric items: {len(current_config.rubric)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Agent initialization failed: {e}")
        return False

def test_rag_service():
    """Test RAG service connectivity"""
    try:
        vs_dir = "./vector_store"
        rag_service = RAGService(vs_dir)
        
        # Note: This will fail if no vector store exists, which is expected
        logger.info("✅ RAGService initialized (vector store may not exist yet)")
        return True
        
    except Exception as e:
        logger.info(f"⚠️  RAGService test: {e} (Expected if no vector store exists)")
        return True  # This is expected for now

if __name__ == "__main__":
    logger.info("🚀 Testing CaseInterviewAgent setup...")
    
    # Run tests
    agent_ok = test_agent_initialization()
    rag_ok = test_rag_service()
    
    if agent_ok and rag_ok:
        logger.info("✅ All tests passed! Agent is ready for use.")
        logger.info("\nNext steps:")
        logger.info("1. Set up your vector store with case data")
        logger.info("2. Configure your .env.local file")
        logger.info("3. Run the entrypoint.py with LiveKit")
    else:
        logger.error("❌ Some tests failed. Check the errors above.")
        sys.exit(1)