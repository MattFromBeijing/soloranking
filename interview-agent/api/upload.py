from flask import Blueprint, request, jsonify
from services.RAGService import RAGService
from services.ExtractorService import ExtractorService
from services.LLMExtractorService import LLMExtractorService
import os

upload_bp = Blueprint('upload', __name__)

# Initialize services
rag_service = RAGService("./vector_store")
extractor_service = ExtractorService()
llm_extractor_service = LLMExtractorService()

@upload_bp.route('/upload-pdf', methods=['POST'])
def upload_pdf():
    """Upload and process PDF case study using keyword-based extraction"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    case_id = request.form.get('case_id', f'case_{int(__import__("time").time())}')
    
    if file.filename == '' or not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Invalid PDF file'}), 400
    
    try:
        # Read PDF content
        pdf_content = file.read()
        
        print(f"Read PDF content, size: {len(pdf_content)} bytes")
        
        # Create Case object using ExtractorService
        case = extractor_service.create_case_from_pdf(case_id, pdf_content)
        
        print(f"Extracted case from PDF")
        
        # Create vector embeddings using RAGService
        chunks_created = rag_service.create_from_pdf(case_id, pdf_content)

        print(f"Created RAG vector store from PDF")
        
        return jsonify({
            'case_id': case_id,
            'vs_dir': os.getenv("VECTOR_STORE_DIR", "./vector_store"),
            'case_data': case.to_dict(),  # Convert to dictionary for JSON serialization
        })
        
    except Exception as e:
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@upload_bp.route('/upload-pdf-llm', methods=['POST'])
def upload_pdf_llm():
    """Upload and process PDF case study using LLM-based extraction"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    case_id = request.form.get('case_id', f'case_{int(__import__("time").time())}')
    
    if file.filename == '' or not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Invalid PDF file'}), 400
    
    try:
        # Read PDF content
        pdf_content = file.read()
        
        print(f"Read PDF content, size: {len(pdf_content)} bytes")
        
        # Create Case object using LLMExtractorService
        case = llm_extractor_service.create_case_from_pdf(case_id, pdf_content)
        
        print(f"Extracted case from PDF using LLM")
        
        # Create vector embeddings using RAGService
        chunks_created = rag_service.create_from_pdf(case_id, pdf_content)

        print(f"Created RAG vector store from PDF")

        # Get case info for response
        return jsonify({
            'case_id': case_id,
            'vs_dir': os.getenv("VECTOR_STORE_DIR", "./vector_store"),
            'case_data': case.to_dict(),  # Convert to dictionary for JSON serialization
        })
        
    except Exception as e:
        return jsonify({'error': f'LLM processing failed: {str(e)}'}), 500