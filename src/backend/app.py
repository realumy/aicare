from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
import shutil
from prompts import generate_summary_and_questions

# Initialize FastAPI app
app = FastAPI()

# Define a Pydantic model for the text input
class TextData(BaseModel):
    text: str


def _dump_patient_data(data):
    with open("patient.db", "a+") as fp:
        fp.write(f"{data}\n")

def _load_patient_data():
    with open("patient.db", "r") as fp:
        return fp.read()
    

def _reset_patient_data():
    with open("patient.db", "w") as fp:
        return fp.write("")

@app.get("/", response_class=HTMLResponse)
async def index():
    return "<h2>It works!</h2>"


# Endpoint to accept text data
@app.post("/send-text")
async def send_text(data: TextData):
    try:

        _dump_patient_data(data)
        # Process text data (for now, just echoing the text)
        return JSONResponse(content={"status": "OK"}, status_code=200)
    
        
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=400)


@app.post("/reset")
async def reset():
    try:
        _reset_patient_data(data)
        # Process text data (for now, just echoing the text)
        return JSONResponse(content={"status": "OK"}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=400)



@app.get("/summary-and-questions")
async def get_summary_and_question(data: TextData):

    try:
        _dump_patient_data(data)
        patient_data = _load_patient_data()
       
        summary, questions = generate_summary_and_questions(patient_data)
        response = {"summary" : summary, "questions" : questions}

        return JSONResponse(content=response, status_code=200)

    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=400)





