from app import create_app, db
from app.models import User, Document, DocumentBlock, Recommendation, ErrorReport, LogEntry

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'User': User, 
        'Document': Document, 
        'DocumentBlock': DocumentBlock,
        'Recommendation': Recommendation,
        'ErrorReport': ErrorReport,
        'LogEntry': LogEntry
    }

if __name__ == '__main__':
    app.run(debug=True)