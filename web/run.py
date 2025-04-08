from web.app import create_app, db
from web.app.models import User, DocumentApp, DocumentSectionContent, TextRecommendation, ErrorReport, LogEntry

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'User': User, 
        'Document': DocumentApp,
        'DocumentBlock': DocumentSectionContent,
        'Recommendation': TextRecommendation,
        'ErrorReport': ErrorReport,
        'LogEntry': LogEntry
    }

if __name__ == '__main__':
    with app.app_context():
        app.run(debug=True)