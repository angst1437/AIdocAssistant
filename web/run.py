from app import create_app, db
from app.models import User, DocumentApp, DocumentBlock, Recommendation, ErrorReport, LogEntry
from app.init_templates import init_templates

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'User': User, 
        'Document': DocumentApp,
        'DocumentBlock': DocumentBlock,
        'Recommendation': Recommendation,
        'ErrorReport': ErrorReport,
        'LogEntry': LogEntry
    }

if __name__ == '__main__':
    with app.app_context():
        # Инициализация шаблонов при запуске
        init_templates()
    app.run(debug=True)