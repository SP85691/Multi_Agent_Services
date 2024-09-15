from sqlalchemy.orm import Session
from models.AgentsModels import Agent
from schemas.AgentSchemas import AgentCreate, AgentUpdate
from datetime import datetime
from dotenv import load_dotenv
import uuid
import time
import json
import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_community.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain.storage import LocalFileStore
from langchain.globals import set_llm_cache
from langchain_core.documents.base import Document
from langchain.embeddings import CacheBackedEmbeddings
from langchain_community.cache import SQLiteCache
load_dotenv()

# Global dictionary to store chains
chains_cache = {}

def create_agent(agent_data: AgentCreate, db: Session) -> Agent:
    new_agent = Agent(
        id=str(uuid.uuid4()),
        name=agent_data.name,
        session_id=agent_data.session_id,
        user_id=agent_data.user_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(new_agent)
    db.commit()
    db.refresh(new_agent)
    return new_agent

def get_agents_by_session(session_id: str, db: Session):
    return db.query(Agent).filter(Agent.session_id == session_id).all()

def get_agent_by_id(agent_id: str, db: Session) -> Agent:
    return db.query(Agent).filter(Agent.id == agent_id).first()

def update_agent(agent_id: str, agent_data: AgentUpdate, db: Session) -> Agent:
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if agent:
        agent.name = agent_data.name
        agent.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(agent)
        return agent
    return None

def delete_agent(agent_id: str, db: Session) -> bool:
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if agent:
        db.delete(agent)
        db.commit()
        return True
    return False

def preprocessor(docs: list):
    llm = ChatGroq(
        model = os.getenv("MODEL_NAME"),
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.4,
    )
    
    print(f"Length of docs: {len(docs)}")
    print(f"Docs: {docs}")
    
    print("Preprocessor called:")
    all_documents = []
    for file in docs:
        if file.endswith('.pdf'):
            loader = PyPDFLoader(file)
            print(f" - Loading PDF: {file}")
            all_documents.extend(loader.load())
        elif file.endswith('.docx') or file.endswith('.doc'):
            loader = Docx2txtLoader(file)
            print(f" - Loading DOCX: {file}")
            all_documents.extend(loader.load())
        elif file.endswith('.txt'):
            loader = TextLoader(file)
            print(f" - Loading TXT: {file}")
            all_documents.extend(loader.load())
        else:
            raise ValueError(f"Unsupported file type: {file}")
    
    print(f"Total documents loaded: {len(all_documents)}")
    
    # Split the documents into smaller chunks
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=10)
    documents = text_splitter.split_documents(all_documents)
    print(f"Total documents after splitting: {len(documents)}")
    
    embedding=HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    store = LocalFileStore("./doc_parser/")
    # Convert the document chunks to embedding and save them to the vector store
    cached_embedder = CacheBackedEmbeddings.from_bytes_store(embedding, store, namespace=embedding.model_name)
    vectordb = FAISS.from_documents(documents, embedding=cached_embedder)
    vectordb.save_local("./doc_parser/")
    
    print("Vector database saved locally.")
    message_history = ChatMessageHistory()

    # Memory for Conversational Context
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        output_key="answer",
        chat_memory=message_history,
        return_messages=True,
    )
    
    print("Memory created.")
    
    # Create Chain that uses the Chroma Vector Store
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm, 
        chain_type="stuff",
        retriever=vectordb.as_retriever(),
        memory=memory, 
        return_source_documents=False,
    )
    
    print("Chain created.")

    return chain

def run(docs: list):
    chain = preprocessor(docs)
    return chain

def prepare_rag_chain(agent_id: str, instructions: str, docs: list, db: Session):
    agent = get_agent_by_id(agent_id, db)
    if not agent:
        raise ValueError("Agent not found")
    
    # Process the instructions
    agent.prompt_template = instructions
    
    # If documents are provided, process them
    if docs:
        chain = run(docs)
        agent.document_paths = json.dumps(docs)
    else:
        # Create a simple chain without document processing
        llm = ChatGroq(
            model = os.getenv("MODEL_NAME"),
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.4,
        )
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            output_key="answer",
            return_messages=True,
        )
        chain = ConversationalRetrievalChain.from_llm(
            llm=llm, 
            chain_type="stuff",
            memory=memory, 
            return_source_documents=False,
        )
    
    db.commit()
    
    # Store the chain in the global cache
    chains_cache[agent_id] = chain
    
    print("Chain prepared.")
    return {"message": "Agent prepared successfully", "chain": chain}

