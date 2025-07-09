# mlops/api/main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import mlflow
import numpy as np
import os

# --- Security Configuration ---
# This should be a long, random string. Load from environment variables in production.
SECRET_KEY = os.environ.get("SECRET_KEY", "a_very_secret_key_for_dev")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- Mock User Database ---
# In a real application, this would be a real database.
fake_users_db = {
    "testuser": {
        "username": "testuser",
        "full_name": "Test User",
        "email": "test@example.com",
        "hashed_password": pwd_context.hash("secret"), # Hashed password for 'secret'
        "disabled": False,
    }
}

# --- Pydantic Models ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

class PredictionInput(BaseModel):
    features: list[list[float]]

# --- Security Helper Functions ---
def get_user(db, username: str):
    if username in db:
        return User(**db[username])

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_active_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None or user.disabled:
        raise credentials_exception
    return user

# --- FastAPI Application ---
app = FastAPI(title="Secure Autonomous Vehicle Classifier API")

# --- Model Loading (same as before) ---
RUN_ID = os.environ.get("MLFLOW_RUN_ID", "<YOUR_RUN_ID>")
model = None
try:
    logged_model_uri = f'runs:/{RUN_ID}/model'
    model = mlflow.pyfunc.load_model(logged_model_uri)
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

# --- API Endpoints ---
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Endpoint to get an access token."""
    user = get_user(fake_users_db, form_data.username)
    if not user or not pwd_context.verify(form_data.password, fake_users_db[user.username]['hashed_password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/")
def read_root():
    return {"status": "ok", "message": "MLOps API is running."}

@app.post("/predict")
async def predict(
    input_data: PredictionInput,
    current_user: User = Depends(get_current_active_user) # This dependency protects the endpoint
):
    """Endpoint to get predictions. Requires authentication."""
    if model is None:
        raise HTTPException(status_code=503, detail="Model is not available.")
    
    try:
        features_array = np.array(input_data.features)
        predictions = model.predict(features_array)
        return {"predictions": predictions.tolist(), "predicted_by": current_user.username}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error during prediction: {str(e)}")
