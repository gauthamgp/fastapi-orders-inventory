from fastapi import FastAPI ,  Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel , StrictInt


class Item(BaseModel):
    a: StrictInt
    b: StrictInt

class Result(BaseModel):
    result: int 

class User(BaseModel):
    name: str
    age: int


app= FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    # Bonus: friendlier error when a/b aren’t integers
    errs = []
    for e in exc.errors():
        field = e.get("loc", ["value"])[-1]
        errs.append({"field": field, "message": "must be an integer"})
    return JSONResponse(status_code=422, content={"detail": errs})

@app.get("/")
def hello():
    return "Hello, World!"

@app.post("/add",response_model=Result)
def add(payload: Item):
    return {"result": payload.a + payload.b}

@app.post("/subtract",response_model=Result)
def subract(payload: Item):
    return {"result": payload.a - payload.b}

@app.post("/multiply",response_model=Result)
def multiply(payload: Item):
    return {"result": payload.a * payload.b}

## PUT and DELETE methods demonstration
user_db = {
    1: {"name": "gauthamgp", "age": 28},
    2: {"name": "suraj", "age": 25},
    3: {"name": "anurag", "age": 17}
}


@app.put("/user/{user_id}")
def user_update(user_id:int, user_details: User):
    if user_id in user_db:
        user_db[user_id] = user_details.dict()
        return {"message": "User updated",  "user": user_db[user_id]}
    else:
        return {"message": "User not found"}
    

@app.delete("/user/{user_id}")
def delete_user(user_id: int):
    if user_id in user_db:
        del user_db[user_id]
        return {"message": "User deleted"}
    else:
        return {"message": "User not found"}