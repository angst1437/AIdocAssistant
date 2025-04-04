from flask import Flask, render_template, request, send_file, jsonify
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

    # Получаем json после отправки с формы
    data = request.get_json()

    # Заполняем шаблон титульного листа и создаём документ
    title = datatypes.TitleData(
        university_info=list(filter(lambda elem: elem.strip() != "",data.get("university-info").split('\n'))),
        work_type=data.get('work-type'),
        subject=data.get('work-subject'),
        theme=data.get('work-theme'),
        author=data.get('fullname'),
        group=data.get('group'),
        educator=data.get('educator'),
        city=data.get('city'),
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
        as_attachment=False,
        download_name='generated_document.docx',
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )

@app.route('/editor')
def editor():
    return render_template('editor.html')

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
        
        return f"File processed successfully {file.filename}", 200
    except Exception as e:
        return f"Error processing file: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)