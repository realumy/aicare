from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from anthropic import Anthropic
import xml.etree.ElementTree as ET
from typing import List, Optional, Dict
import json
import os
from datetime import datetime
from prompts import generate_summary_and_questions  # Keep your original import

# Database Configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./medical_qa.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, bind=engine)
Base = declarative_base()


# Database Models
class MedicalQA(Base):
    __tablename__ = "medical_qa"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String, index=True)
    focus = Column(String, index=True)
    source = Column(String)
    question_id = Column(String, unique=True)
    question_type = Column(String, index=True)
    question = Column(Text)
    answer = Column(Text)


class PatientData(Base):
    __tablename__ = "patient_data"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(String, index=True)
    data = Column(Text)


# Pydantic Models
class TextData(BaseModel):
    text: str


# Your original file handling functions
def _dump_patient_data(data):
    with open("patient.db", "a+") as fp:
        fp.write(f"{data}\n")


def _load_patient_data():
    with open("patient.db", "r") as fp:
        return fp.read()


def _reset_patient_data():
    with open("patient.db", "w") as fp:
        return fp.write("")

class MCPContext(BaseModel):
    relevant_qa: List[Dict]
    patient_history: str

# XML Processing
class XMLProcessor:
    @staticmethod
    def parse_medquad_xml(xml_content: str, db: Session) -> bool:
        try:
            root = ET.fromstring(xml_content)

            doc_id = root.attrib.get('id', '')
            source = root.attrib.get('source', '')
            focus = root.find('Focus').text if root.find('Focus') is not None else ''

            qa_pairs = root.find('QAPairs')
            if qa_pairs is not None:
                for qa_pair in qa_pairs.findall('QAPair'):
                    question_elem = qa_pair.find('Question')
                    answer_elem = qa_pair.find('Answer')

                    if question_elem is not None and answer_elem is not None:
                        qa_entry = MedicalQA(
                            document_id=doc_id,
                            focus=focus,
                            source=source,
                            question_id=question_elem.attrib.get('qid', ''),
                            question_type=question_elem.attrib.get('qtype', ''),
                            question=question_elem.text,
                            answer=answer_elem.text
                        )
                        db.add(qa_entry)

            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise Exception(f"Error processing XML: {str(e)}")


# MCP Handler
class MCPHandler:
    def __init__(self, db: Session):
        self.db = db
        self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    async def get_relevant_context(self, query: str, limit: int = 5) -> MCPContext:
        # Get relevant QA pairs
        qa_results = (
            self.db.query(MedicalQA)
            .filter(
                or_(
                    MedicalQA.question.like(f"%{query}%"),
                    MedicalQA.answer.like(f"%{query}%"),
                    MedicalQA.focus.like(f"%{query}%")
                )
            )
            .limit(limit)
            .all()
        )

        # Get recent patient history
        patient_history = (
            self.db.query(PatientData)
            .order_by(PatientData.timestamp.desc())
            .limit(5)
            .all()
        )

        return MCPContext(
            relevant_qa=[{
                "question": qa.question,
                "answer": qa.answer,
                "type": qa.question_type,
                "focus": qa.focus
            } for qa in qa_results],
            patient_history="\n".join([entry.data for entry in patient_history])
        )

    async def generate_response(self, query: str, context: MCPContext) -> str:
        messages = [
            {
                "role": "system",
                "content": f"""You are a medical AI assistant with access to a verified medical knowledge base. 
                Use the following context to inform your responses:

                Medical Knowledge Context:
                {json.dumps(context.relevant_qa, indent=2)}

                Recent Patient History:
                {context.patient_history}

                Only use this information to provide accurate medical information and always recommend consulting with healthcare professionals for specific medical advice."""
            },
            {
                "role": "user",
                "content": query
            }
        ]

        response = self.anthropic.messages.create(
            model="claude-3-sonnet-20240229",
            messages=messages,
            max_tokens=1000
        )

        return response.content[0].text


# FastAPI App
app = FastAPI()


# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_mcp_handler(db: Session = Depends(get_db)):
    return MCPHandler(db)


# Initialize database
@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)


# Your original endpoints
@app.get("/", response_class=HTMLResponse)
async def index():
    return "<h2>It works!</h2>"


@app.post("/send-text")
async def send_text(data: TextData):
    try:
        _dump_patient_data(data)
        return JSONResponse(content={"status": "OK"}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=400)


@app.post("/reset")
async def reset():
    try:
        _reset_patient_data()
        return JSONResponse(content={"status": "OK"}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=400)


@app.get("/summary-and-questions")
async def get_summary_and_question(data: TextData):
    try:
        _dump_patient_data(data)
        patient_data = _load_patient_data()

        summary, questions = generate_summary_and_questions(patient_data)
        response = {"summary": summary, "questions": questions}

        return JSONResponse(content=response, status_code=200)
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=400)


# New endpoints for MedQuAD and MCP integration
@app.post("/import-medquad")
async def import_medquad(
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    try:
        content = await file.read()
        xml_content = content.decode('utf-8')

        processor = XMLProcessor()
        processor.parse_medquad_xml(xml_content, db)

        return JSONResponse(
            content={"message": "Successfully imported MedQuAD data"},
            status_code=200
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/patient-data")
async def add_patient_data(
        data: TextData,
        db: Session = Depends(get_db)
):
    try:
        # Store in both file and database for backward compatibility
        _dump_patient_data(data.text)

        new_entry = PatientData(
            timestamp=datetime.now().isoformat(),
            data=data.text
        )
        db.add(new_entry)
        db.commit()

        return JSONResponse(content={"status": "OK"}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/query")
async def query_medical_knowledge(
        query: str,
        mcp_handler: MCPHandler = Depends(get_mcp_handler)
):
    try:
        context = await mcp_handler.get_relevant_context(query)
        response = await mcp_handler.generate_response(query, context)

        return JSONResponse(
            content={
                "response": response,
                "context": context.dict()
            },
            status_code=200
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/search-qa")
async def search_qa(
        query: str,
        question_type: Optional[str] = None,
        db: Session = Depends(get_db)
):
    try:
        db_query = db.query(MedicalQA)

        if question_type:
            db_query = db_query.filter(MedicalQA.question_type == question_type)

        results = db_query.filter(
            or_(
                MedicalQA.question.like(f"%{query}%"),
                MedicalQA.answer.like(f"%{query}%"),
                MedicalQA.focus.like(f"%{query}%")
            )
        ).limit(10).all()

        return JSONResponse(
            content={
                "results": [
                    {
                        "question_id": r.question_id,
                        "question_type": r.question_type,
                        "question": r.question,
                        "answer": r.answer,
                        "focus": r.focus,
                        "source": r.source
                    }
                    for r in results
                ]
            },
            status_code=200
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))