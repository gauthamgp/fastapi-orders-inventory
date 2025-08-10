from enum import Enum
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, StrictInt


class Operation(str, Enum):
    add = "add"
    subtract = "subtract"
    multiply = "multiply"
    divide = "divide"

class CalculatorIn(BaseModel):
    a: StrictInt
    b: StrictInt
    operation: Operation

class CalculatorOut(BaseModel):
    result: float


app = FastAPI()

@app.get("/")
def hello():
    return "Hello, World!"

@app.post("/calculator", response_model=CalculatorOut)
def calculate(payload: CalculatorIn):
    a,b, operation = payload.a, payload.b, payload.operation
    if operation == Operation.add:
        result= a + b
    elif operation == Operation.subtract:
        result=  a - b
    elif operation == Operation.multiply:
        result=  a * b
    elif operation == Operation.divide:
        if b == 0:
            raise ValueError("Division by zero is not allowed.")
        result=  a / b
    else:
        raise ValueError("Invalid operation.")
    return {"result": float(result)}

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    errs = []
    for e in exc.errors():
        field = e.get("loc", ["value"])[-1]
        etype = e.get("type", "")
        if field in ("a", "b"):
            msg = "must be an integer" if etype != "missing" else "field required"
        elif field == "operation":
            msg = "must be one of: add, subtract, multiply, divide"
        else:
            msg = "invalid value"
        errs.append({"field": field, "message": msg})
    return JSONResponse(status_code=422, content={"detail": errs})