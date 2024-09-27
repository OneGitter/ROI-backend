# from distutils.log import debug
from fileinput import filename
import pandas as pd
from flask import *
import os
import json
from werkzeug.utils import secure_filename
from flask_cors import CORS
from data_generation import summarised_data_generation
from openai_api import generate_insights_json, user_history

app = Flask(__name__)

app.config.from_pyfile('settings.py')
CORS(app)


api_key = app.config.get("API_KEY")

UPLOAD_FOLDER = os.path.join('datasets')
TEST_FOLDER = os.path.join('testing')
 
# Define allowed files
ALLOWED_EXTENSIONS = {'csv'}
 
 
# Configure upload file path flask
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TEST_FOLDER'] = TEST_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16*1024*1024

@app.route('/') 
def index():
    return render_template('index.html')

@app.route('/test', methods=['POST'])
def testing():
    try:
        f = request.files.get('file')
        file_name = secure_filename(f.filename)
        f.save(os.path.join(app.config['TEST_FOLDER'],
                            file_name))
        return jsonify({'message': 'Data received successfully'}),200
    except Exception as e:
        return jsonify({'error': 'No data provided','details':e}), 400

@app.route('/generate-insights',methods=['POST'])
def generate_insights():
    data = request.json
    generate_insights_json(api_key,f'./improved_datasets/{data['filename']}.csv',f'./json/{data['filename']}.json',user_history)

    json_data = {}

    df = pd.read_csv(f'./improved_datasets/{data['filename']}.csv')
    df.drop(columns=['converted_user_journey','non_converted_user_journey','to_state','from_state'],inplace=True)

    with open(f'./json/{data['filename']}.json', 'r') as f:
        dataj = json.load(f)
        json_data = dataj
        # json_data['insights'] = json_data['insights'][9:-6]
        json_data['insights'] = json_data['insights'].replace("\n","")
        json_data['insights'] = json_data['insights'].replace(" ","")
        json_data['insights'] = json.loads(json_data['insights'])
        json_data['data'] = df.to_json(orient="records")
    
    with open(f'./json/{data['filename']}master.json', 'w') as json_file:
                json.dump(json_data, json_file, indent=4)
    print(json_data)

    return jsonify(json_data)



@app.route('/generate-master-table',methods=['POST'])
def generate_master_table():
    data = request.json
    print(data)
    print(data['filename'])
    df = pd.read_csv(f'./testing/{data['filename']}.csv')
    summarised_data_generation(df,f'{data['filename']}.csv')

    return jsonify({'message':'master table created'}),200


@app.route('/submit-csv', methods=['POST'])
def handle_csv():
    f = request.files.get('file')
 
        # Extracting uploaded file name
    data_filename = secure_filename(f.filename)

    f.save(os.path.join(app.config['UPLOAD_FOLDER'],
                            data_filename))
    
    return jsonify({'message':'data received succesfully'}),200



if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
