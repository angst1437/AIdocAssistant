from flask import Flask, render_template, request, send_file
from docx import Document
from io import BytesIO
from logic import builder, partition, datatypes
from werkzeug.utils import secure_filename


app = Flask(__name__)


@app.route('/')
def choose():
    return render_template('choose.html')


@app.route('/form')
def form():
    return render_template('form.html')


@app.route('/generate', methods=['POST'])
def generate_doc():
    title = datatypes.TitleData(
        university_info=list(filter(lambda elem: elem.strip() != "",request.form.get('university-info').split('\n'))),
        work_type=request.form.get('work-type'),
        subject=request.form.get('work-subject'),
        theme=request.form.get('work-theme'),
        author=request.form.get('fullname'),
        group=request.form.get('group'),
        educator=request.form.get('educator'),
        city=request.form.get('city'),
    )


    doc_builder = builder.DocBuilder()

    # Добавляем содержимое
    doc_builder.title_builder(title)
    doc = doc_builder.get_doc()

    # Сохраняем в байтовый поток
    file_stream = BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)

    # Отправляем файл пользователю
    return send_file(
        file_stream,
        as_attachment=True,
        download_name='generated_document.docx',
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )

@app.route('/process_docx', methods=['POST'])
def process_docx():
    if 'file' not in request.files:
        return "No file uploaded", 400
    
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    
    if not (file and file.filename.endswith('.docx')):
        return "Invalid file type. Only .docx files are allowed", 400
    
    try:
        # Здесь должна быть логика обработки файла
        
        return "File processed successfully", 200
    except Exception as e:
        return f"Error processing file: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)