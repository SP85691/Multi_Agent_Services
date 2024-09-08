from sqlalchemy.orm import Session
from models.AgentsModels import Agent
from schemas.AgentSchemas import AgentCreate, AgentUpdate
from datetime import datetime
import uuid

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

