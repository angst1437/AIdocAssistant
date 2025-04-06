from flask import Blueprint, request, jsonify, current_app, abort
from flask_login import login_required, current_user
from web.app import db
from web.app.models import DocumentBlock, Recommendation, LogEntry
from web.app.services.ai_clients import get_ai_client
from web.app.utils.decorators import log_activity

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/analyze', methods=['POST'])
@login_required
@log_activity(level='INFO', message='AI analysis requested')
def analyze_text():
    data = request.get_json()
    
    if not data or 'text' not in data or 'block_id' not in data:
        abort(400, description="Missing required fields")
    
    text = data['text']
    block_id = data['block_id']
    provider = data.get('provider', 'yandex')
    check_type = data.get('check_type')
    
    # Verify the block belongs to the current user
    block = DocumentBlock.query.get_or_404(block_id)
    if block.document.user_id != current_user.id:
        abort(403)
    
    try:
        # Get the appropriate AI client
        ai_client = get_ai_client(provider)
        
        # Analyze the text
        recommendations = ai_client.analyze_text(text, check_type)
        
        # Save recommendations to database
        saved_recommendations = []
        for rec in recommendations:
            recommendation = Recommendation(
                block_id=block_id,
                start_char=rec.get('start_char', 0),
                end_char=rec.get('end_char', 0),
                original_text=rec.get('original_text', ''),
                suggestion=rec.get('suggestion', ''),
                explanation=rec.get('explanation', ''),
                type_of_error=rec.get('type_of_error', 'unknown'),
                ai_provider=provider,
                status='pending'
            )
            db.session.add(recommendation)
            saved_recommendations.append({
                'id': None,  # Will be updated after commit
                'start_char': recommendation.start_char,
                'end_char': recommendation.end_char,
                'original_text': recommendation.original_text,
                'suggestion': recommendation.suggestion,
                'explanation': recommendation.explanation,
                'type_of_error': recommendation.type_of_error,
                'ai_provider': recommendation.ai_provider,
                'status': recommendation.status
            })
        
        db.session.commit()
        
        # Update IDs after commit
        for i, rec in enumerate(saved_recommendations):
            rec['id'] = recommendations[i].id
        
        return jsonify(saved_recommendations)
        
    except Exception as e:
        # Log the error
        error_log = LogEntry(
            level='ERROR',
            message=f"AI analysis error: {str(e)}",
            user_id=current_user.id,
            request_url=request.path,
            ip_address=request.remote_addr
        )
        db.session.add(error_log)
        db.session.commit()
        
        current_app.logger.error(f"AI analysis error: {str(e)}")
        return jsonify({'error': str(e)}), 500

