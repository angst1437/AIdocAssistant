from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort, send_file
from flask_login import login_required, current_user
from web.app import db
from web.app.models import Document, DocumentBlock, Recommendation
from web.app.utils.decorators import log_activity
from datetime import datetime

documents_bp = Blueprint('documents', __name__)

@documents_bp.route('/')
@login_required
def index():
    documents = Document.query.filter_by(user_id=current_user.id).order_by(Document.updated_at.desc()).all()
    return render_template('documents/index.html', title='My Documents', documents=documents)

@documents_bp.route('/create', methods=['GET', 'POST'])
@login_required
@log_activity(level='INFO', message='Document created')
def create():
    if request.method == 'POST':
        title = request.form.get('title', 'Untitled Document')
        document = Document(title=title, user_id=current_user.id)
        db.session.add(document)
        db.session.commit()
        
        # Create initial empty block
        block = DocumentBlock(
            document_id=document.id,
            block_type='paragraph',
            content='',
            order=1
        )
        db.session.add(block)
        db.session.commit()
        
        return redirect(url_for('documents.edit', document_id=document.id))
    
    return render_template('documents/create.html', title='New Document')

@documents_bp.route('/<int:document_id>/edit')
@login_required
def edit(document_id):
    document = Document.query.get_or_404(document_id)
    
    # Check if the current user is the owner
    if document.user_id != current_user.id:
        abort(403)
    
    blocks = document.blocks.order_by(DocumentBlock.order).all()
    return render_template('documents/editor.html', title=document.title, document=document, blocks=blocks)

@documents_bp.route('/<int:document_id>/update', methods=['POST'])
@login_required
@log_activity(level='INFO', message='Document updated')
def update(document_id):
    document = Document.query.get_or_404(document_id)
    
    # Check if the current user is the owner
    if document.user_id != current_user.id:
        abort(403)
    
    title = request.form.get('title')
    if title:
        document.title = title
        document.updated_at = datetime.utcnow()
        db.session.commit()
    
    return jsonify({'success': True})

@documents_bp.route('/<int:document_id>/delete', methods=['POST'])
@login_required
@log_activity(level='INFO', message='Document deleted')
def delete(document_id):
    document = Document.query.get_or_404(document_id)
    
    # Check if the current user is the owner
    if document.user_id != current_user.id:
        abort(403)
    
    db.session.delete(document)
    db.session.commit()
    
    flash('Document deleted successfully', 'success')
    return redirect(url_for('documents.index'))

@documents_bp.route('/blocks/<int:block_id>', methods=['GET'])
@login_required
def get_block(block_id):
    block = DocumentBlock.query.get_or_404(block_id)
    
    # Check if the current user is the owner of the document
    if block.document.user_id != current_user.id:
        abort(403)
    
    return jsonify({
        'id': block.id,
        'document_id': block.document_id,
        'block_type': block.block_type,
        'content': block.content,
        'order': block.order
    })

@documents_bp.route('/blocks/<int:block_id>', methods=['PUT'])
@login_required
@log_activity(level='INFO', message='Block updated')
def update_block(block_id):
    block = DocumentBlock.query.get_or_404(block_id)
    
    # Check if the current user is the owner of the document
    if block.document.user_id != current_user.id:
        abort(403)
    
    data = request.get_json()
    
    if 'content' in data:
        block.content = data['content']
    
    if 'block_type' in data:
        block.block_type = data['block_type']
    
    if 'order' in data:
        block.order = data['order']
    
    block.updated_at = datetime.utcnow()
    block.document.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'success': True})

@documents_bp.route('/documents/<int:document_id>/blocks', methods=['POST'])
@login_required
@log_activity(level='INFO', message='Block created')
def create_block(document_id):
    document = Document.query.get_or_404(document_id)
    
    # Check if the current user is the owner
    if document.user_id != current_user.id:
        abort(403)
    
    data = request.get_json()
    
    # Get the highest order value
    max_order = db.session.query(db.func.max(DocumentBlock.order)).filter_by(document_id=document_id).scalar() or 0
    
    block = DocumentBlock(
        document_id=document_id,
        block_type=data.get('block_type', 'paragraph'),
        content=data.get('content', ''),
        order=max_order + 1
    )
    
    db.session.add(block)
    db.session.commit()
    
    return jsonify({
        'id': block.id,
        'document_id': block.document_id,
        'block_type': block.block_type,
        'content': block.content,
        'order': block.order
    })

@documents_bp.route('/blocks/<int:block_id>', methods=['DELETE'])
@login_required
@log_activity(level='INFO', message='Block deleted')
def delete_block(block_id):
    block = DocumentBlock.query.get_or_404(block_id)
    
    # Check if the current user is the owner of the document
    if block.document.user_id != current_user.id:
        abort(403)
    
    document_id = block.document_id
    
    db.session.delete(block)
    
    # Update order of remaining blocks
    blocks = DocumentBlock.query.filter_by(document_id=document_id).filter(DocumentBlock.order > block.order).all()
    for b in blocks:
        b.order -= 1
    
    db.session.commit()
    
    return jsonify({'success': True})

@documents_bp.route('/blocks/<int:block_id>/recommendations', methods=['GET'])
@login_required
def get_recommendations(block_id):
    block = DocumentBlock.query.get_or_404(block_id)
    
    # Check if the current user is the owner of the document
    if block.document.user_id != current_user.id:
        abort(403)
    
    recommendations = block.recommendations.all()
    
    result = []
    for rec in recommendations:
        result.append({
            'id': rec.id,
            'start_char': rec.start_char,
            'end_char': rec.end_char,
            'original_text': rec.original_text,
            'suggestion': rec.suggestion,
            'explanation': rec.explanation,
            'type_of_error': rec.type_of_error,
            'ai_provider': rec.ai_provider,
            'status': rec.status
        })
    
    return jsonify(result)

@documents_bp.route('/recommendations/<int:recommendation_id>', methods=['PUT'])
@login_required
@log_activity(level='INFO', message='Recommendation status updated')
def update_recommendation(recommendation_id):
    recommendation = Recommendation.query.get_or_404(recommendation_id)
    
    # Check if the current user is the owner of the document
    if recommendation.block.document.user_id != current_user.id:
        abort(403)
    
    data = request.get_json()
    
    if 'status' in data:
        recommendation.status = data['status']
    
    db.session.commit()
    
    return jsonify({'success': True})

@documents_bp.route('/<int:document_id>/export/<format>', methods=['GET'])
@login_required
@log_activity(level='INFO', message='Document exported')
def export_document(document_id, format):
    from web.app.services.export_service import export_to_docx, export_to_pdf
    
    document = Document.query.get_or_404(document_id)
    
    # Check if the current user is the owner
    if document.user_id != current_user.id:
        abort(403)
    
    if format == 'docx':
        file_path = export_to_docx(document_id)
        return send_file(file_path, as_attachment=True, download_name=f"{document.title}.docx")
    elif format == 'pdf':
        file_path = export_to_pdf(document_id)
        return send_file(file_path, as_attachment=True, download_name=f"{document.title}.pdf")
    else:
        abort(400, description="Unsupported format")

