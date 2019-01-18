from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_mail import Mail
import os
import config
import wget
import shutil
from pathlib import Path
import zipfile
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from itsdangerous import URLSafeTimedSerializer
import smtplib, ssl


app = Flask(__name__)
app._static_folder = config.CONFIG['staticFolder']
NEW_FOLDER = config.CONFIG['newDownloadFolder']
DOWNLOAD_FOLDER = config.CONFIG['downloadFolder']
NEW_URL = config.CONFIG['newDownloadUrl']

POSTGRES_URL = config.CONFIG['postgresUrl']
POSTGRES_USER = config.CONFIG['postgresUser']
POSTGRES_PASS = config.CONFIG['postgresPass']
POSTGRES_DB = config.CONFIG['postgresDb']
DB_URL = 'postgresql+psycopg2://{user}:{pw}@{url}/{db}'.format(user=POSTGRES_USER,pw=POSTGRES_PASS,url=POSTGRES_URL,db=POSTGRES_DB)
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL

MAIL_SERVER = config.CONFIG['mailServer']
MAIL_PORT = config.CONFIG['mailPort']
MAIL_USERNAME = config.CONFIG['mailUsername']
MAIL_PASSWORD = config.CONFIG['mailPassword']
MAIL_USE_TLS = config.CONFIG['mailUseTls']
MAIL_USE_SSL = config.CONFIG['mailUseSsl']
MAIL_DEBUG = config.CONFIG['mailDebug']
MAIL_SUPPRESS_SEND = config.CONFIG['mailSuppress']

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
mail = Mail(app)

class User(db.Model):
	__tablename__ = "users"
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(120), unique=True)
	password = db.Column(db.String(120))
	email = db.Column(db.String(120), unique=True)

	def __init__(self, username, password, email):
		self.username = username
		self.password = bcrypt.generate_password_hash(password)
		self.email = email

	def __repr__(self):
		return '<Username %r>' % self.username

	def is_correct_password(self, plaintext):
		return bcrypt.check_password_hash(self.password, plaintext)


@app.route('/register', methods=['GET'])
def register():
	return render_template('register.html')


@app.route('/register', methods=['POST'])
def register_post():
	username = request.form['username']
	password = request.form['password']
	email = request.form['email']
	if not db.session.query(User).filter(User.username == username).count():
		if not db.session.query(User).filter(User.email == email).count():
			register_url_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
			register_url = url_for(
				'register_validation',
				token=register_url_serializer.dumps(email, salt='password-reset-salt'),
				username=register_url_serializer.dumps(username, salt='password-reset-salt'),
				password=register_url_serializer.dumps(password, salt='password-reset-salt'),
				_external=True)
			subject = "GetUrl registration mail"
			text = "Hello, to complete the registration please click on the link: " + register_url
			message = """From: %s\nTo: %s\nSubject: %s\n\n%s
			""" % (MAIL_USERNAME, ", ".join(email), subject, text)
			smtpObj = smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT)
			smtpObj.ehlo()
			smtpObj.login(MAIL_USERNAME, MAIL_PASSWORD)
			smtpObj.sendmail(MAIL_USERNAME, email, message)
			smtpObj.close()
			flash("Please check your email and click on the link to complete registration.")
			return redirect(url_for('register'))
		else:
			flash("This mail address already has an account.")
			return redirect(url_for('register'))
	else:
		if not db.session.query(User).filter(User.email == email).count():
			flash("This username is taken.")
			return redirect(url_for('register'))
		else:
			flash("You already have an account.")
			return redirect(url_for('register'))

@app.route('/register_validation', methods=['GET'])
def register_validation():
	if "token" not in request.args:
		return redirect(url_for('register'))
	try:
		token = request.args['token']
		username = request.args['username']
		password = request.args['password']
		register_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
		email = register_serializer.loads(token, salt='password-reset-salt', max_age=3600)
		username = register_serializer.loads(username, salt='password-reset-salt', max_age=3600)
		password = register_serializer.loads(password, salt='password-reset-salt', max_age=3600)
	except:
		flash("token is invalid")
		return redirect(url_for("register"))
	return render_template('register_validation.html', email=email, username=username, password=password)


@app.route('/register_validation', methods = ['POST'])
def register_validation_post():
	username = request.form['username']
	password = request.form['password']
	email = request.form['email']

	if not db.session.query(User).filter(User.username == username).count():
		user = User(username, password, email)
		db.session.add(user)
		db.session.commit()
		flash("You have successfully registered.")
		return redirect(url_for("login"))
	else:
		flash("You have already registered.")
		return redirect(url_for("login"))


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
		flash("You don't have an account, please register.")
		return login()
	elif user.is_correct_password(password):
		session['logged_in'] = True
		global directory
		directory = NEW_FOLDER + username
		if not os.path.isdir(directory):
			os.mkdir(directory)
		return redirect(url_for("new_url"))
	else:
		flash("Wrong password.")
		return login()


@app.route('/forgot', methods=['GET'])
def forgot():
	return render_template("forgot.html")


@app.route('/forgot', methods=['POST'])
def forgot_post():
	email = request.form['email']
	if not db.session.query(User).filter(User.email == email).count():
		flash("Mail is sent to this address if it's valid: "+ email)
		return forgot()
	else:
		password_reset_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
		password_reset_url = url_for(
			'reset',
			token=password_reset_serializer.dumps(email, salt='password-reset-salt'),
			_external=True)
		subject = "geturl forgot password mail"
		text = "Hello, if you forgot your password click on the link: " + password_reset_url

		message = """From: %s\nTo: %s\nSubject: %s\n\n%s
		""" % (MAIL_USERNAME, ", ".join(email), subject, text)
		smtpObj = smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT)
		smtpObj.ehlo()
		smtpObj.login(MAIL_USERNAME, MAIL_PASSWORD)
		smtpObj.sendmail(MAIL_USERNAME, email, message)
		smtpObj.close()
		flash("Mail is sent to this address if it's valid: "+ email)
		return forgot()

@app.route('/reset', methods=['GET'])
def reset():
	if "token" not in request.args:
		return redirect(url_for("login"))
	try:
		token = request.args['token']
		password_reset_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
		email = password_reset_serializer.loads(token, salt='password-reset-salt', max_age=3600)
	except:
		flash("token is invalid")
		return redirect(url_for("login"))


	return render_template("reset.html", email=email)

@app.route('/reset', methods =['POST'])
def reset_post():
	email = request.form['email']
	password = request.form['password']
	password = bcrypt.generate_password_hash(password)
	user = User.query.filter_by(email=email).first()
	user.email = email
	user.password = password
	db.session.commit()

	flash("You have successfully changed your password.")
	return redirect(url_for("login"))


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