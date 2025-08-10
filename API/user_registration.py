import uuid
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, StrictInt
import csv   


app = FastAPI()

class UserRegistration(BaseModel):
    username: str
    email: str
    password: str

class RegistrationResponse(BaseModel):
    message: str
    user_id: int


def generate_user_id():
    user_id=uuid.uuid4().int
    return user_id

def validate_email(email: str) -> bool:
    return "@" in email and "." in email

def validate_password(password: str) -> bool:
    return len(password) >= 8

@app.post("/register", response_model=RegistrationResponse)
def register_user(payload: UserRegistration):
    if not validate_email(payload.email):
        raise ValueError("Invalid email format.")
    if not validate_password(payload.password):
        raise ValueError("Password must be at least 8 characters long.")
    
    user_id = generate_user_id()
    # Here you would typically save the user to a database
    with open('users.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([user_id, payload.username, payload.email, payload.password])
    return RegistrationResponse(message="User registered successfully", user_id=user_id)


@app.get("/registered_users")
def get_registered_users():
    users = []
    try:
        with open('users.csv', mode='r') as file:
            reader = csv.reader(file)
            for row in reader:
                users.append({
                    "user_id": row[0],
                    "username": row[1],
                    "email": row[2]
                })
    except FileNotFoundError:
        return {"message": "No registered users found."}
    return users

@app.get("/get_user/{user_id}")
def get_user(user_id: int):
    try:
        with open('users.csv', mode='r') as file:
            reader = csv.reader(file)
            for row in reader:
                if int(row[0]) == user_id:
                    return {
                        "user_id": row[0],
                        "username": row[1],
                        "email": row[2]
                    }
    except FileNotFoundError:
        return {"message": "No registered users found."}
    return {"message": "User not found."}

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    errs = []
    for e in exc.errors():
        field = e.get("loc", ["value"])[-1]
        etype = e.get("type", "")
        if field in ("username", "email", "password"):
            msg = "field required" if etype == "missing" else "invalid value"
        else:
            msg = "invalid value"
        errs.append({"field": field, "message": msg})
    return JSONResponse(status_code=422, content={"detail": errs})