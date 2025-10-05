import uvicorn
from src.coach_feedback.graph.api import app

if __name__=='__main__':
    uvicorn.run(app, host='0.0.0.0', port=8001)
