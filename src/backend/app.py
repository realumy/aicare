from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import shutil

# Initialize FastAPI app
app = FastAPI()

# Define a Pydantic model for the text input
class TextData(BaseModel):
    text: str

# Endpoint to accept audio data
@app.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    try:
        # Save the uploaded audio file locally (you can process it as needed)
        with open(f"uploaded_{file.filename}", "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        return JSONResponse(content={"message": f"Audio file {file.filename} uploaded successfully!"}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=400)

# Endpoint to accept text data
@app.post("/send-text")
async def send_text(data: TextData):
    try:
        # Process text data (for now, just echoing the text)
        return JSONResponse(content={"received_text": data.text}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=400)



