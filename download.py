from flask import Flask, render_template, redirect, url_for, request, session
from flask.ext.session import Session
import os
import config
import wget 
import shutil
from pathlib import Path
import subprocess

app = Flask(__name__)
app._static_folder = config.CONFIG['staticFolder']
NEW_FOLDER = config.CONFIG['newDownloadFolder']
DOWNLOAD_FOLDER = config.CONFIG['downloadFolder']
NEW_URL = config.CONFIG['newDownloadUrl']
app.config.from_object(__name__)
Session(app)

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     error = None
#     if request.method == 'POST':
#         if request.form['username'] != 'admin' or request.form['password'] != 'admin':
#             error = 'Invalid Credentials. Please try again.'
#         else:
#             return redirect(url_for('home'))
#     return render_template('login.html', error=error)

@app.route('/')
def get_url():
    return render_template('login.html')

@app.route("/result", methods=['GET', 'POST'])
def result():
	# error = None
	if request.method == 'POST':
		session['username'] = request.form['username']
		directory = NEW_FOLDER + username
		if not os.path.isdir(directory):
			os.mkdir(directory)
		files = os.listdir(directory)
	return render_template('result.html', files=files)


@app.route("/new_url", methods=['GET', 'POST'])
def new_url_result():
	fileExists = False
	if request.method == 'POST':
		text = request.form['text']
		file = wget.download(text)
		check_file = Path(NEW_FOLDER + session.get('username','not set') +file)
		if check_file.is_file():
			fileExists = True
			os.remove(file)
		else:
			shutil.move(DOWNLOAD_FOLDER + "/" + file, NEW_FOLDER + file)
		output = NEW_URL + file
		return render_template("new_url.html", output=output, fileExists=fileExists)


		# password = request.form['password']

		# if username != 'admin' or password != 'admin':
		# 	error = 'Invalid Credentials. Please try again.'
		# else:
		# 	return "Hello World"
	# return render_template('login.html', error=error)