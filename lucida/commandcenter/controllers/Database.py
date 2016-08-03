import hashlib, uuid
from pymongo import MongoClient
from base64 import b64encode
from Utilities import log
import os
import Config


class Database(object):
	# Name of the algorithm to use for password encryption.
	ENCRYPT_ALGORITHM = 'sha512'
	
	# Constructor.
	def __init__(self):
		if os.environ.get('MONGO_PORT_27017_TCP_ADDR'):
			log('MongoDB: ' + os.environ.get('MONGO_PORT_27017_TCP_ADDR'))
			self.db = MongoClient(os.environ.get('MONGO_PORT_27017_TCP_ADDR'),
				27017).lucida
		else:
			log('MongoDB: localhost')
			self.db = MongoClient().lucida
		self.users = self.db.users
	
	# Returns the image collection of the user.
	def get_image_collection(self, username):
		images_collection = 'images_' + username
		return self.db[images_collection]
	
	# Returns the text collection of the user.
	def get_text_collection(self, username):
		text_collection = 'text_' + username
		return self.db[text_collection]
	
	# Adds a new user.
	def add_user(self, username, firstname, lastname, password, email):
		salt = uuid.uuid4().hex # thwart rainbow attack
		hashed_password = self.hash_password(self.ENCRYPT_ALGORITHM,
			salt, password)
		self.users.insert_one({'username' : username,
			'firstname': firstname, 'lastname': lastname,
			'password': hashed_password, 'email': email})
	
	# Returns true if password of the user is correct
	def check_password(self, username, input_password):
		correct_password_in_db = (self.users.find_one
			({'username': username}))['password']
		salt = correct_password_in_db.split('$')[1]
		generated_password = self.hash_password(self.ENCRYPT_ALGORITHM,
			salt, input_password)
		return correct_password_in_db == generated_password
	
	# Generates a hashed password from the raw password.
	def hash_password(self, algorithm, salt, password):
		m = hashlib.new(algorithm)
		password = password.encode('utf-8')
		s = salt + password
		m.update(s)
		password_hash = m.hexdigest()
		return "$".join([algorithm, salt, password_hash])
	
	#Returns true if the username already exists.
	def username_exists(self, username):
		return not self.users.find_one({'username': username}) is None
	
	# Adds the uploaded image.
	def add_image(self, username, image_data, label):
		if not self.get_image_collection(username).find_one(
			{'label': label}) is None:
			raise RuntimeError('Image ' + label + ' already exists')
		self.get_image_collection(username).insert_one(
			{'label': label, 'data': b64encode(image_data)}) # encoded
		
	# Deletes the specified image.
	def delete_image(self, username, label):
		self.get_image_collection(username).remove({'label': label})
		
	# Returns all the images by username.
	def get_images(self, username):
		log('Retrieving all images from images_' + username)
		# Notice image['data'] was encoded using Base64.
		return [image for image in self.get_image_collection(username).find()]
	
	# Checks whether the user can add one more image.
	def check_add_image(self, username):
		if self.get_image_collection(username).count() >= \
			Config.MAX_DOC_NUM_PER_USER:
			raise RuntimeError('Sorry. You can only add ' + 
				str(Config.MAX_DOC_NUM_PER_USER) + \
				' images at most')
	# Returns the number of images by username.
	def count_images(self, username):
		log('Retrieving the number of images from images_' + username)
		return self.get_image_collection(username).count()
	
	# Adds the knowledge text.
	def add_text(self, username, text_type, text_data, text_id):
		self.get_text_collection(username).insert_one(
			{'type': text_type, 'text_data': text_data,
			 'text_id': text_id})
		
	# Deletes the knowledge text.
	def delete_text(self, username, text_id):
		self.get_text_collection(username).delete_one(
			{'text_id': text_id})
		
	# Returns the knowledge text by username.
	def get_text(self, username):
		log('Retrieving text from text_' + username)
		return [text for text in self.get_text_collection(username).find()]
	
	# Checks whether the user can add one more piece of text.
	def check_add_text(self, username):
		if self.get_text_collection(username).count() >= \
			Config.MAX_DOC_NUM_PER_USER:
			raise RuntimeError('Sorry. You can only add ' + 
				str(Config.MAX_DOC_NUM_PER_USER) + \
				' pieces of text at most')

database = Database()
	