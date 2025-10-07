from fastapi import FastAPI, Request
from starlette.responses import Response
from starlette.status import HTTP_200_OK
import ContextVariable_pb2

app = FastAPI()

@app.post("/calcFib")
async def calcFib(request: Request):
    # Retrieve context variables from request
    body = await request.body()
    context_variables = ContextVariable_pb2.ContextVariables()
    context_variables.ParseFromString(body)

    fib1 = None
    fib2 = None

    # Extract values for fib1 and fib2
    for context_variable in context_variables.data:
        if context_variable.name == "fib1":
            fib1 = context_variable.value.integer
        if context_variable.name == "fib2":
            fib2 = context_variable.value.integer
    
    if fib1 is None or fib2 is None:
        return Response("Missing fib1 or fib2 in request", status_code=400)

    # Calculate next fib number
    new_fib1 = fib1 + fib2
    new_fib2 = fib1

    # Send max number if it is over threshold
    if new_fib1 > 2000000000:
        new_fib1 = 1000000001

    print(f"Received ({fib1}, {fib2}). Sending back ({new_fib1}, {new_fib2})")

    # Add both numbers to response
    response_vars = ContextVariable_pb2.ContextVariables()
    result_var_1 = ContextVariable_pb2.ContextVariable(
        name="fib1",
        value=ContextVariable_pb2.Value(integer=new_fib1)
    )
    response_vars.data.append(result_var_1)
    result_var_2 = ContextVariable_pb2.ContextVariable(
        name="fib2",
        value=ContextVariable_pb2.Value(integer=new_fib2)
    )
    response_vars.data.append(result_var_2)

    # Send response
    response_body = response_vars.SerializeToString()
    return Response(content=response_body, status_code=HTTP_200_OK, media_type="application/x-protobuf")

@app.post("/state1")
def handle_state1(request: Request):
    print("In State 1!")

@app.post("/state2")
def handle_state2(request: Request):
    print("In State 2!")
