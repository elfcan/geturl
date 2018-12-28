from flask import Flask, render_template, redirect, url_for, request
import os
import config
import wget 
import shutil
from pathlib import Path
import subprocess
import zipfile 

app = Flask(__name__)
app._static_folder = config.CONFIG['staticFolder']
NEW_FOLDER = config.CONFIG['newDownloadFolder']
DOWNLOAD_FOLDER = config.CONFIG['downloadFolder']
NEW_URL = config.CONFIG['newDownloadUrl']


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
	url_list = []
	if request.method == 'POST':
		global username
		username = request.form['username']
		directory = NEW_FOLDER + username
		if not os.path.isdir(directory):
			os.mkdir(directory)
		files = os.listdir(directory)
		for file in files:
			url = NEW_URL + username + "/" + file
			url_list.append(url)
	return render_template('result.html', files=files, url_list=url_list)


@app.route("/new_url", methods=['GET', 'POST'])
def new_url_result():
	global fileExists
	fileExists = False
	if request.method == 'POST':
		text = request.form['text']
		global file
		file = wget.download(text)
		if request.form.getlist('zip') == [u'Zip']:
			zipfile.ZipFile(file +'.zip', mode='w').write(file)
			os.remove(file)
			file = file + ".zip"
		check_file = Path(NEW_FOLDER + username + "/" + file)
		if check_file.is_file():
			fileExists = True
			return render_template("reload_file.html")
		else:
			shutil.move(DOWNLOAD_FOLDER + "/" + file, NEW_FOLDER + username + "/" + file)
		output = NEW_URL + username + "/" + file
		return render_template("new_url_result.html", output=output)

@app.route("/reload", methods=['GET', 'POST'])
def reload():
	if request.method == 'POST':
		check_file = Path(NEW_FOLDER + username + "/" + file)
		# choice = request.form.getlist('no')
		if request.form.getlist('no') == [u'No']:
			os.remove(file)
		elif request.form.getlist('yes') == [u'Yes']:
			os.remove(str(check_file))
			shutil.move(DOWNLOAD_FOLDER + "/" + file, NEW_FOLDER + username + "/" + file)
		output = NEW_URL + username + "/" + file
		return render_template("new_url_result.html", output=output)


if __name__ == '__main__':
	app.run()





















		# password = request.form['password']

		# if username != 'admin' or password != 'admin':
		# 	error = 'Invalid Credentials. Please try again.'
		# else:
		# 	return "Hello World"
	# return render_template('login.html', error=error)