from flask import Blueprint, request, jsonify
from services.RAGService import RAGService
from services.ExtractorService import ExtractorService

upload_bp = Blueprint('upload', __name__)

# Initialize services
rag_service = RAGService("./vector_store")
extractor_service = ExtractorService()

@upload_bp.route('/upload-pdf', methods=['POST'])
def upload_pdf():
    """Upload and process PDF case study"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    case_id = request.form.get('case_id', f'case_{int(__import__("time").time())}')
    
    if file.filename == '' or not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Invalid PDF file'}), 400
    
    try:
        # Read PDF content
        pdf_content = file.read()
        
        # Create Case object using ExtractorService
        case = extractor_service.create_case_from_pdf(case_id, pdf_content)
        
        # Create vector embeddings using RAGService
        chunks_created = rag_service.create_from_pdf(case_id, pdf_content)
        
        # Get case info for response
        phases = list(case.phases.keys())
        description = getattr(case, 'case_description', 'No description available')
        
        return jsonify({
            'message': 'PDF processed successfully',
            'case_id': case_id,
            'case_data': case,
            'chunks_created': chunks_created,
            'phases_found': len(phases),
            'description_preview': description[:200] + '...' if len(description) > 200 else description
        })
        
    except Exception as e:
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500