
from flask import Flask, request, render_template
import wget
import subprocess
import config
import shutil

app = Flask(__name__)
app._static_folder = config.CONFIG['staticFolder']
DOWNLOAD_FOLDER = config.CONFIG['downloadFolder']

@app.route('/')
def get_url():
    return render_template('get_url.html')

@app.route("/", methods=['GET', 'POST'])
def result():	
	if request.method == 'POST':
		text = request.form['text']	
		file = wget.download(text)
		shutil.move(DOWNLOAD_FOLDER + "/" + file, "/var/www/html/" + file)
		output = "you can download the file from this url: localhost/" + file
		return render_template("result.html", output=output)
