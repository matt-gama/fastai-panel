import requests
import random

import string

from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from app.crypto import *
import os

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from app.crypto import *
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash


load_dotenv()

# Configuração do aplicativo
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# Inicialização do banco de dados
db = SQLAlchemy()
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

class Users(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String, nullable=False)
    lastname = db.Column(db.String, nullable=True)
    email = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    photo_url = db.Column(db.String, nullable=True)
    phone = db.Column(db.String, nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now())


class IA(db.Model):
    __tablename__ = 'ias'
    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String, nullable=False)
    phone_number = db.Column(db.String, nullable=False)
    token_ia = db.Column(db.String, nullable=False)
    status = db.Column(db.Boolean, default=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now())

    # Relacionamentos
    prompts = relationship("Prompt", back_populates="ia", cascade="all, delete-orphan")
    ia_config = relationship("IAConfig", back_populates="ia", uselist=False, cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="ia", uselist=False, cascade="all, delete-orphan")
    
    @property
    def active_prompt(self):
        active = [p for p in self.prompts if p.is_active]
        return active[0] if active else None

class Prompt(db.Model):
    __tablename__ = 'prompts'
    id = db.Column(db.Integer, primary_key=True, index=True)
    ia_id = db.Column(db.Integer, db.ForeignKey('ias.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    prompt_text = db.Column(db.String, nullable=False)
    is_active = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now())

    ia = relationship("IA", back_populates="prompts")

class IAConfig(db.Model):
    __tablename__ = 'ia_config'
    id = db.Column(db.Integer, primary_key=True, index=True)
    ia_id = db.Column(db.Integer, db.ForeignKey('ias.id'), nullable=False)
    channel = db.Column(db.String, nullable=False)
    ai_api = db.Column(db.String, nullable=False)
    encrypted_credentials = db.Column(db.String, nullable=False)

    probabilidade_audio =  db.Column( db.Integer)
    audio_config =  db.Column(db.String, nullable=False)

    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now())

    ia = relationship("IA", back_populates="ia_config")

    @property
    def credentials(self):
        """
        Retorna as credenciais já descriptografadas.
        """
        if isinstance(self.encrypted_credentials, str):
            return decrypt_data(self.encrypted_credentials)
        else:

            return self.encrypted_credentials

    @property
    def credentials_elevenlabs(self):
        """
        Retorna as credenciais já descriptografadas.
        """
        if isinstance(self.audio_config, str):
            return decrypt_data(self.audio_config)
        else:
            return self.audio_config

class Lead(db.Model):
    __tablename__ = 'leads'
    id = db.Column(db.Integer, primary_key=True, index=True)
    ia_id = db.Column(db.Integer, db.ForeignKey('ias.id'), nullable=False)
    name = db.Column(db.String, nullable=True)
    phone = db.Column(db.String, nullable=True, unique=True)
    unique_token = db.Column(db.String, nullable=True, unique=True)
    bloqueado = db.Column(db.Boolean, default=True)
    message = db.Column(db.JSON, nullable=False)
    resume = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now())

    ia = relationship("IA", back_populates="leads")

# Protect all existing routes with 
@app.route('/')
@login_required
def index():
    id_user = current_user.id
    ias = IA.query.filter_by(user_id=id_user).all()
    ia_list = []
    for ia in ias:
        config_data = []
        if ia.ia_config:
            config_data = [{
                "id": ia.ia_config.id,
                "channel": ia.ia_config.channel,
                "ai_api": ia.ia_config.ai_api,
                "probabilidade_audio": ia.ia_config.probabilidade_audio,
                "credentials": ia.ia_config.credentials,
                "audio_config": ia.ia_config.credentials_elevenlabs
                }]
            
        ia_info = {
            'id': ia.id,
            'name': ia.name,
            'phone_number': ia.phone_number,
            'status': ia.status,
            'configs': config_data,
            'prompts': [{'id': ia.active_prompt.id, 'text': ia.active_prompt.prompt_text, 'is_active': ia.active_prompt.is_active}] if ia.active_prompt else []
        }
        ia_list.append(ia_info)

    return render_template('index.html', ias=ia_list, host_evo=os.getenv("HOST_API", ""), api_key=os.getenv("API_KEY", ""))

@app.route('/create-ia', methods=['GET', 'POST'])
@login_required
def create_ia():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            phone_number = request.form.get('phone_number')
            channel = request.form.get('channel')
            ia_used = request.form.get('ia_used')
            apikey = request.form.get('apikey')
            model = request.form.get('model')
            token_ia=generate_token()
            new_ia = IA(
                name=name,
                phone_number=phone_number,
                token_ia=token_ia,
                user_id = current_user.id,
                status=True
            )
            
            db.session.add(new_ia)
            db.session.commit()
            data = {
                "api_key": apikey,
                "api_secret": "openai",
                "ai_model":model
            }
            ia_config = IAConfig(
                ia_id=new_ia.id,
                channel=channel,
                ai_api= ia_used,
                probabilidade_audio=0,
                encrypted_credentials=encrypt_data(data)
            )
            
            db.session.add(ia_config)
            db.session.commit()


            host = os.getenv("HOST_API")
            api_key = os.getenv("API_KEY")
            url_webhook = os.getenv("URL_WEBHOOK", "")

            url = f"{host}/instance/create"

            payload = {
                    "instanceName": f"{name}_{current_user.id}",
                    "integration": "WHATSAPP-BAILEYS",
                    "groupsIgnore": True,
                    "readMessages": False,
                    "webhook": {
                            "url": url_webhook,
                            "byEvents": False,
                            "base64": True,
                            "headers": {
                                "autorization": "Bearer TOKEN",
                                "Content-Type": "application/json"
                            },
                            "events": ["MESSAGES_UPSERT"]
                        }
                }

            headers = {
                "apikey": api_key,
                "Content-Type": "application/json"
            }

            response = requests.request("POST", url, json=payload, headers=headers)
            if response.status_code in [200, 201]:
                print("INSTANCIA CRIADA COM SUCESSO")

        except Exception as ex:
            print(ex)


    return redirect(url_for('index'))

@app.route('/edit-ia/<int:id_ia>', methods=['GET', 'POST'])
@login_required
def edit_ia(id_ia):
    if request.method == 'POST':
        ia = IA.query.filter_by(id=id_ia).first()
        if not ia:
            return redirect(url_for('index'))
        
        phone_number = request.form.get('phone_number').strip().replace(' ', '').replace('-', '').replace('+', '')
        status = request.form.get('status')

        apikey = request.form.get('apikey')
        model = request.form.get('model')
        eleven_voice_id = request.form.get('eleven_voice_id')
        eleven_api_key = request.form.get('eleven_api_key')
        probabilidade_audio = request.form.get('probabilidade_audio')

        ia.phone_number = phone_number
        ia.status = True if status == 'True' else False 

         # Se não existe config, cria!
        if ia.ia_config is None:
            ia.ia_config = IAConfig(ia_id=ia.id)

        if apikey:
            apikey = apikey.strip()
        if model:
            model = model.strip()
        
        data = {
            "api_key": apikey,
            "api_secret": "openai",
            "ai_model":model
        }   

        data_elevenlabs = {
            "api_key_elevenlabs":eleven_api_key,
            "audio_id":eleven_voice_id
        }
        encrypted_data = encrypt_data(data)
        encrypted_data_eleven = encrypt_data(data_elevenlabs)
        
        ia.ia_config.probabilidade_audio = int(probabilidade_audio)
        ia.ia_config.encrypted_credentials = encrypted_data
        ia.ia_config.audio_config = encrypted_data_eleven
        
        db.session.commit()
        
    return redirect(url_for('index'))

@app.route('/delete-ia/<int:id_ia>', methods=['GET', 'POST'])
@login_required
def delete_ia(id_ia):
    if request.method == 'POST':
        try:
            ia = IA.query.filter_by(id=id_ia).first()
            if not ia:
                return redirect(url_for('index'))
            
            db.session.delete(ia)
            db.session.commit()

            host = os.getenv("HOST_API")
            api_key = os.getenv("API_KEY")

            url = f"{host}instance/delete/{ia.name}_{current_user.id}"

            headers = {"apikey": api_key}

            response = requests.request("DELETE", url, headers=headers)

            if response:
                print("INSTANCIA DELETADA COM SUCESSO")

        except Exception as ex:
            print(ex)
        
    return redirect(url_for('index'))

@app.route('/get-prompts-ia', methods=['GET'])
@login_required
def get_prompts_ia():
    id_user = current_user.id
    ias = IA.query.filter_by(user_id=id_user).all()
    prompts = Prompt.query.filter_by(user_id=id_user).all()
    prompts_list = []
    for prompt in prompts:
        prompt_dict = {
            'id': prompt.id,
            'ia_name': prompt.ia.name,
            'ia_id': prompt.ia.id,
            'text': prompt.prompt_text,
            'status': prompt.is_active,
            'created_at': prompt.created_at.strftime('%d-%m-%Y %H:%M:%S'),
            'updated_at': prompt.updated_at.strftime('%d-%m-%Y %H:%M:%S'),
        }
        prompts_list.append(prompt_dict)
    unique_ias = [{"id":ia.id, "ia_name": ia.name} for ia in ias]
    return render_template('prompt.html', prompts=prompts_list, unique_ias=unique_ias)

@app.route('/new-prompt/<int:id_ia>', methods=['GET', 'POST'])
@login_required
def new_prompt(id_ia):
    id_user = current_user.id

    if request.method == 'POST':
        
        new_prompt_text = request.form.get("text")
        status = request.form.get("status")
        
        new_prompt = Prompt(
            prompt_text=new_prompt_text,
            is_active=True if status == 'True' else False,
            ia_id=id_ia,
            user_id=id_user
        )
        
        db.session.add(new_prompt)
        db.session.commit()
        
    return redirect(url_for('get_prompts_ia'))

@app.route('/edit-prompt/<int:id_prompt>', methods=['GET', 'POST'])
@login_required
def edit_prompt(id_prompt):
    if request.method == 'POST':
        promtp = Prompt.query.filter_by(id=id_prompt).first()
        if not promtp:
            return redirect(url_for('get_prompts_ia'))
        
        new_prompt = request.form.get("text")
        status = request.form.get("status")
        
        promtp.prompt_text = new_prompt
        promtp.is_active = True if status == 'True' else False
        db.session.commit()
        
    return redirect(url_for('get_prompts_ia'))

@app.route('/delete-prompt/<int:id_prompt>', methods=['GET', 'POST'])
@login_required
def delete_prompt(id_prompt):
    if request.method == 'POST':
        promtp = Prompt.query.filter_by(id=id_prompt).first()
        if not promtp:
            return redirect(url_for('get_prompts_ia'))
        
        db.session.delete(promtp)
        db.session.commit()
        
    return redirect(url_for('get_prompts_ia'))


@app.route('/delete-lead/<int:id_lead>', methods=['GET', 'POST'])
@login_required
def delete_lead(id_lead):
    if request.method == 'POST':
        lead = Lead.query.filter_by(id=id_lead).first()
        if not lead:
            return redirect(url_for('get_leads_ia'))
        
        db.session.delete(lead)
        db.session.commit()
        
    return redirect(url_for('get_leads_ia', ia_id = lead.ia_id))

@app.route('/update-lead/<int:id_lead>', methods=['GET', 'POST'])
@login_required
def update_lead(id_lead):
    if request.method == 'POST':
        lead = Lead.query.filter_by(id=id_lead).first()
        if not lead:
            return redirect(url_for('get_leads_ia'))
        
        bloqueado = lead.bloqueado
        if bloqueado == True:
            lead.bloqueado = False
        else:
            lead.bloqueado = True

        db.session.commit()
        
    return redirect(url_for('get_leads_ia', ia_id = lead.ia_id))


@app.route('/get-leads-ia/<int:ia_id>', methods=['GET', 'POST'])
@login_required
def get_leads_ia(ia_id):
    page = request.args.get('page', 1, type=int)
    per_page = 1000  # Number of items per page
    leads = Lead.query.filter_by(ia_id=ia_id).order_by(Lead.updated_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    leads_list = []
    lead_id = int(request.args.get("lead_id", 0))
    selected_lead = {}
    for lead in leads:
        lead_dict = {
            'id': lead.id,
            'ia_name': lead.ia.name,
            'unique_token': lead.unique_token,
            'bloqueado': lead.bloqueado,
            'ia_id': lead.ia.id,
            'name': lead.name,
            'phone': lead.phone,
            'message': lead.message,
            'resume': lead.resume,
            'created_at': lead.created_at.strftime('%d-%m-%Y %H:%M:%S'),
            'updated_at': lead.updated_at.strftime('%d-%m-%Y %H:%M:%S'),
        }
        if lead_id == lead.id:
            selected_lead = lead_dict
            
        leads_list.append(lead_dict)
    
    
    return render_template('lead.html', leads=leads_list, selected_lead= selected_lead)

@app.route('/get-infos-lead/<int:ia_lead>', methods=['GET', 'POST'])
@login_required
def get_info_lead(ia_lead):
    lead = Lead.query.filter_by(id=ia_lead).first()
    leads_list = []

    lead_dict = {
        'id': lead.id,
        'ia_name': lead.ia.name,
        'ia_id': lead.ia.id,
        'name': lead.name,
        'phone': lead.phone,
        'message': lead.message,
        'resume': lead.resume,
        'created_at': lead.created_at.strftime('%d-%m-%Y %H:%M:%S'),
        'updated_at': lead.updated_at.strftime('%d-%m-%Y %H:%M:%S'),
    }
    leads_list.append(lead_dict)

    return render_template('lead.html', selected_lead=lead_dict)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = Users.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        
        return render_template('login.html', error="Invalid credentials")
    
    return render_template('login.html')

# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         name = request.form.get('name')
#         lastname = request.form.get('lastname')
#         email = request.form.get('email')
#         password = request.form.get('password')
        
#         user_exists = Users.query.filter_by(email=email).first()
#         if user_exists:
#             return render_template('register.html', error="Email already registered")
        
#         hashed_password = generate_password_hash(password, method='sha256')
#         new_user = Users(
#             name=name,
#             lastname=lastname,
#             email=email,
#             password=hashed_password
#         )
        
#         db.session.add(new_user)
#         db.session.commit()
        
#         return redirect(url_for('login'))
    
#     return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

def generate_token(length=6):
    """
    Generate a random token with specified length containing letters and numbers
    """
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# Executar o aplicativo
if __name__ == '__main__':
    #db.create_all()  # Cria as tabelas no banco de dados
    app.run(debug=True)
