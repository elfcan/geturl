from flask import Flask, render_template, redirect, url_for, request, session, flash
import os
import config
import wget
import shutil
from pathlib import Path
import subprocess
import zipfile
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt


app = Flask(__name__)
app._static_folder = config.CONFIG['staticFolder']
NEW_FOLDER = config.CONFIG['newDownloadFolder']
DOWNLOAD_FOLDER = config.CONFIG['downloadFolder']
NEW_URL = config.CONFIG['newDownloadUrl']
DB_URL = 'postgresql+psycopg2://{user}:{pw}@{url}/{db}'.format(user='geturl',pw='123qwe123',url='localhost:5432',db='geturl')

app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class User(db.Model):
	__tablename__ = "users"
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(120), unique=True)
	password = db.Column(db.String(120))

	def __init__(self, username, password):
		self.username = username
		self.password = bcrypt.generate_password_hash(password)

	def __repr__(self):
		return '<Username %r>' % self.username
		return '<Password %r>' % self.password

	def is_correct_password(self, plaintext):
		return bcrypt.check_password_hash(self.password, plaintext)

@app.route('/register', methods=['GET'])
def register():
	return render_template('register.html')

@app.route('/register', methods=['POST'])
def register_post():
	username = request.form['username']
	password = request.form['password']
	if not db.session.query(User).filter(User.username == username).count():
		user = User(username, password)
		db.session.add(user)
		db.session.commit()
		flash("you have successfully registered, please login")
		return redirect(url_for('login'))

@app.route('/login', methods=['GET'])
def login():
	return render_template("login.html")

@app.route('/login', methods=['POST'])
def login_post():
	global username
	username = request.form['username']
	password = request.form['password']
	user = User.query.filter_by(username=username).first()
	if user == None:
		flash("you don't have an account please register")
		return login()
	elif user.is_correct_password(password):
		session['logged_in'] = True
		global directory
		directory = NEW_FOLDER + username
		if not os.path.isdir(directory):
			os.mkdir(directory)
		return redirect(url_for("new_url"))
	else:
		flash("wrong password")
		return login()

@app.route('/', methods=['GET'])
def get_url():
	if not session.get('logged_in'):
		return redirect(url_for("login"))
	else:
		return redirect(url_for("new_url"))

@app.route("/new_url", methods=['GET'])
def new_url():
	return render_template("new_url.html")


@app.route("/new_url", methods=['POST'])
def new_url_post():
	global fileExists
	global output
	fileExists = False
	text = request.form['text']
	global file
	working_directory = os.getcwd()
	os.chdir(DOWNLOAD_FOLDER)
	file = wget.download(text)
	if request.form.getlist('zip') == [u'Zip']:
		zipfile.ZipFile(file + '.zip', mode='w').write(file)
		os.remove(file)
		file = file + ".zip"
	check_file = Path(NEW_FOLDER + username + "/" + file)
	if check_file.is_file():
		fileExists = True
		return redirect(url_for("reload"))
	else:
		shutil.move(DOWNLOAD_FOLDER + "/" + file, NEW_FOLDER + username + "/" + file)
	output = NEW_URL + username + "/" + file
	os.chdir(working_directory)
	return redirect(url_for("new_url_result", output=output))

@app.route("/new_url_result", methods=['GET'])
def new_url_result():
	return render_template("new_url_result.html", output=output)

@app.route("/reload", methods=['GET'])
def reload():
	return render_template("reload_file.html")

@app.route("/reload", methods=['POST'])
def reload_post():
	global output
	check_file = Path(NEW_FOLDER + username + "/" + file)
	# choice = request.form.getlist('no')
	if request.form.getlist('yes') == [u'Yes']:
		os.remove(str(check_file))
		shutil.move(DOWNLOAD_FOLDER + "/" + file, NEW_FOLDER + username + "/" + file)
	else:
		os.remove(DOWNLOAD_FOLDER + "/" + file)
	output = NEW_URL + username + "/" + file
	return redirect(url_for("new_url_result", output=output))

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