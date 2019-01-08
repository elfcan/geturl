from flask import Flask, render_template, redirect, url_for, request, session
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


@app.route('/')
def get_url():
   if not session.get('logged_in'):
      return render_template('login.html')
   else:
      return new_url()

@app.route("/new_url", methods=['GET', 'POST'])
def new_url():
	if request.method == 'POST':
		global username
		username = request.form['username']
		session['logged_in'] = True
		global directory
		directory = NEW_FOLDER + username
		if not os.path.isdir(directory):
			os.mkdir(directory)

	return render_template("new_url.html")

@app.route("/new_url_result", methods=['GET', 'POST'])
def new_url_result():
	global fileExists
	fileExists = False
	if request.method == 'POST':
		text = request.form['text']
		global file
		working_directory = os.getcwd()
		os.chdir(DOWNLOAD_FOLDER)
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
		os.chdir(working_directory)

@app.route("/reload", methods=['GET', 'POST'])
def reload():
	if request.method == 'POST':
		check_file = Path(NEW_FOLDER + username + "/" + file)
		# choice = request.form.getlist('no')
		if request.form.getlist('yes') == [u'Yes']:
			os.remove(str(check_file))
			shutil.move(DOWNLOAD_FOLDER + "/" + file, NEW_FOLDER + username + "/" + file)
		else:
			os.remove(file)
		output = NEW_URL + username + "/" + file
		return render_template("new_url_result.html", output=output)

@app.route("/result", methods=['GET', 'POST'])
def result():
	# error = None
	url_list = []
	files = os.listdir(directory)
	for file in files:
		url = NEW_URL + username + "/" + file
		url_list.append(url)
	return render_template('result.html', url_list=url_list)

@app.route("/logout")
def logout():
   session['logged_in'] = False
   return get_url()

if __name__ == '__main__':
	app.secret_key = os.urandom(12)
	app.run(debug=True,host='0.0.0.0', port=4000)