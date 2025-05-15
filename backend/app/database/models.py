from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.service.crypto import decrypt_data

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    lastname = Column(String, nullable=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    photo_url = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relacionamento com IA (um usuário pode ter várias IAs)
    ias = relationship("IA", back_populates="user", cascade="all, delete", lazy="joined")


class IA(Base):
    __tablename__ = 'ias'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    token_ia = Column(String, nullable=False)
    status = Column(Boolean, default=True, nullable=False)
    
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relacionamentos
    prompts = relationship("Prompt", back_populates="ia")
    ia_config = relationship("IAConfig", back_populates="ia", uselist=False)
    leads = relationship("Lead", back_populates="ia", uselist=False)

    # Relacionamento com Usuário (uma IA pertence a um único usuário)
    user = relationship("User", back_populates="ias", lazy="joined")

    @property
    def active_prompt(self):
        active = [p for p in self.prompts if p.is_active]
        return active[0] if active else None
    

class IAConfig(Base):
    __tablename__ = 'ia_config'
    id = Column(Integer, primary_key=True, index=True)
    ia_id = Column(Integer, ForeignKey('ias.id'), nullable=False)
    channel = Column(String, nullable=False)
    ai_api = Column(String, nullable=False)
    # Armazena as credenciais criptografadas em formato JSON
    encrypted_credentials = Column(String, nullable=False)
    
    probabilidade_audio = Column(Integer)
    audio_config = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relacionamento com a IA correspondente
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

class Prompt(Base):
    __tablename__ = 'prompts'
    id = Column(Integer, primary_key=True, index=True)
    ia_id = Column(Integer, ForeignKey('ias.id'), nullable=False)
    prompt_text = Column(String, nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relacionamento inverso com IA
    ia = relationship("IA", back_populates="prompts")


class Lead(Base):
    __tablename__ = 'leads'
    id = Column(Integer, primary_key=True, index=True)
    ia_id = Column(Integer, ForeignKey('ias.id'), nullable=False)
    name = Column(String, nullable=True)
    phone = Column(String, nullable=True, unique=True)
    unique_token = Column(String, nullable=True, unique=True)
    # O campo 'message' armazenará uma lista de dicionários
    message = Column(MutableList.as_mutable(JSON), nullable=False)

    bloqueado = Column(Boolean, default=True)
    resume = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    ia = relationship("IA", back_populates="leads")