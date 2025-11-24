from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from starlette.responses import Response
from starlette.status import HTTP_200_OK
import datetime
import ContextVariable_pb2
import Event_pb2
import logging
import time, asyncio
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.trace import SpanContext, TraceFlags

app = FastAPI()


class GateStatus(BaseModel):
    status: str
    last: float


class LightStatus(BaseModel):
    status: str
    last: float


class BellStatus(BaseModel):
    status: str
    last: float


gate_statuses = {}
light_statuses = {}
bell_statuses = {}
resource = Resource(attributes={SERVICE_NAME: "railway-consumer"})
trace_provider = TracerProvider(resource=resource)
span_exporter = OTLPSpanExporter()
span_processor = BatchSpanProcessor(span_exporter)
trace_provider.add_span_processor(span_processor)
trace.set_tracer_provider(trace_provider)

tracer = trace.get_tracer(__name__)

from fastapi.responses import HTMLResponse


@app.get("/status", response_class=HTMLResponse)
def visualize_status():
    html = """
    <html>
    <head>
        <title>Crossing Status</title>
        <meta http-equiv="refresh" content="1">
        <style>
            table { border-collapse: collapse; font-family: Arial, sans-serif; }
            th, td { border: 1px solid black; padding: 8px; text-align: center; }
            th { background-color: #eee; }
        </style>
    </head>
    <body>
        <h1>Railway Crossing Status</h1>
        <table>
            <tr><th>ID</th><th>Type</th><th>Status</th></tr>
    """

    # Show gate statuses
    for id, g in gate_statuses.items():
        gate_color = "green" if g.status == "up" else "red"
        html += f"<tr><td>{id}</td><td>Gate</td><td style='background-color:{gate_color}'>{g.status}</td></tr>"

    # Show light statuses
    for id, l in light_statuses.items():
        light_color = "yellow" if l.status == "on" else "gray"
        html += f"<tr><td>{id}</td><td>Light</td><td style='background-color:{light_color}'>{l.status}</td></tr>"

    # Show bell statuses
    for id, b in bell_statuses.items():
        bell_color = "orange" if b.status == "on" else "gray"
        html += f"<tr><td>{id}</td><td>Bell</td><td style='background-color:{bell_color}'>{b.status}</td></tr>"

    html += """
        </table>
    </body>
    </html>
    """

    return HTMLResponse(content=html)


@app.post("/gate/down")
async def gate_down(request: Request, background_tasks: BackgroundTasks):
    # Read the raw request body
    body = await request.body()

    # Parse the protobuf message
    context_variables = ContextVariable_pb2.ContextVariables()
    context_variables.ParseFromString(body)

    # Extract the approachingSpeed value
    approaching_speed = None
    for context_variable in context_variables.data:
        if context_variable.name == "approachingSpeed":
            approaching_speed = context_variable.value.double
            break

    if approaching_speed is None:
        return {"error": "approachingSpeed not found in context variables"}

    seconds_until_arrival = 1000 / approaching_speed
    seconds_to_close = seconds_until_arrival - 15 if seconds_until_arrival > 15 else seconds_until_arrival

    # Retrieve the sender ID
    id = request.headers.get("Cirrina-Sender-ID")

    # Create the gate status if not seen before
    if id not in gate_statuses:
        gate_statuses[id] = GateStatus(status="up", last=time.time())

    # Update its state 15 seconds before projected arrival
    background_tasks.add_task(set_gate_down_in, id, seconds_to_close)

    response_vars = ContextVariable_pb2.ContextVariables()
    response_vars.data.add(
        name="downDelay", value=ContextVariable_pb2.Value(double=seconds_to_close)
    )
    # Serialize response
    response_body = response_vars.SerializeToString()
    return Response(
        content=response_body, media_type="application/x-protobuf", status_code=200
    )


@app.post("/gate/up")
def gate_up(request: Request):
    # Retrieve the sender ID
    id = request.headers.get("Cirrina-Sender-ID")

    # Create the gate status if not seen before
    if id not in gate_statuses:
        gate_statuses[id] = GateStatus(status="up", last=time.time())

    # Update its state
    gate_statuses[id].status = "up"

    return Response(status_code=HTTP_200_OK)


@app.post("/light/on")
async def light_on(request: Request, background_tasks: BackgroundTasks):
    # Read the raw request body
    body = await request.body()

    # Parse the protobuf message
    context_variables = ContextVariable_pb2.ContextVariables()
    context_variables.ParseFromString(body)

    # Extract the approachingSpeed value
    approaching_speed = None
    for context_variable in context_variables.data:
        if context_variable.name == "approachingSpeed":
            approaching_speed = context_variable.value.double
            break

    seconds_until_arrival = 1000 / approaching_speed
    seconds_to_close = seconds_until_arrival - 15 if seconds_until_arrival > 15 else seconds_until_arrival
    # Retrieve the sender ID
    id = request.headers.get("Cirrina-Sender-ID")

    # Create the gate status if not seen before
    if id not in light_statuses:
        light_statuses[id] = LightStatus(status="off", last=time.time())

    # Update its state
    background_tasks.add_task(set_light_on_in, id, seconds_to_close)

    return Response(status_code=HTTP_200_OK)


@app.post("/light/off")
async def light_off(request: Request):
    # Retrieve the sender ID
    id = request.headers.get("Cirrina-Sender-ID")

    # Create the gate status if not seen before
    if id not in light_statuses:
        light_statuses[id] = LightStatus(status="off", last=time.time())

    # Update its state
    light_statuses[id].status = "off"

    return Response(status_code=HTTP_200_OK)


@app.post("/light/earlyWarning")
async def light_earlyWarning(request: Request):
    # Retrieve the sender ID
    id = request.headers.get("Cirrina-Sender-ID")

    # Create the gate status if not seen before
    if id not in light_statuses:
        light_statuses[id] = LightStatus(status="earlyWarning", last=time.time())

    # Update its state
    light_statuses[id].status = "earlyWarning"

    return Response(status_code=HTTP_200_OK)


@app.post("/bell/on")
async def bell_on(request: Request, background_tasks: BackgroundTasks):
    # Read the raw request body
    body = await request.body()

    # Parse the protobuf message
    context_variables = ContextVariable_pb2.ContextVariables()
    context_variables.ParseFromString(body)

    # Extract the approachingSpeed, traceId and spanId values
    approaching_speed = None
    for context_variable in context_variables.data:
        if context_variable.name == "approachingSpeed":
            approaching_speed = context_variable.value.double
            break
    seconds_until_arrival = 1000 / approaching_speed
    seconds_to_close = seconds_until_arrival - 15 if seconds_until_arrival > 15 else seconds_until_arrival

    # Retrieve the sender ID
    id = request.headers.get("Cirrina-Sender-ID")

    # Create the gate status if not seen before
    if id not in bell_statuses:
        bell_statuses[id] = BellStatus(status="off", last=time.time())

    # Update its state 15 seconds before projected arrival
    background_tasks.add_task(set_bell_on_in, id, seconds_to_close)

    return Response(status_code=HTTP_200_OK)


@app.post("/bell/off")
async def bell_off(request: Request):
    # Read the raw request body
    body = await request.body()

    # Parse the protobuf message
    context_variables = ContextVariable_pb2.ContextVariables()
    context_variables.ParseFromString(body)

    # Extract the approachingSpeed, traceId and spanId values
    traceId = spanId = parent_context = None
    for context_variable in context_variables.data:
        if context_variable.name == "traceId":
            traceId = context_variable.value.string
        elif context_variable.name == "spanId":
            spanId = context_variable.value.string

    if traceId and spanId:
        try:
            trace_id_int = int(traceId, 16)
            span_id_int = int(spanId, 16)

            span_ctx = SpanContext(
                trace_id=trace_id_int,
                span_id=span_id_int,
                is_remote=True,
                trace_flags=TraceFlags(0x01),
            )
            parent_context = trace.set_span_in_context(trace.NonRecordingSpan(span_ctx))
        except Exception as e:
            print("Failed to extract span")

    with tracer.start_as_current_span(
        "process_bell_invocation", context=parent_context
    ) as span:

        span.set_attribute("service", "bellOff")
        # Retrieve the sender ID
        id = request.headers.get("Cirrina-Sender-ID")

        # Create the gate status if not seen before
        if id not in bell_statuses:
            bell_statuses[id] = BellStatus(status="off", last=time.time())

        # Update its state
        bell_statuses[id].status = "off"

        return Response(status_code=HTTP_200_OK)


async def set_gate_down_in(id: str, delay: float):
    # Delay lowering of gate by given value
    if delay > 0:
        await asyncio.sleep(delay)

    # Update its state
    gate_statuses[id].status = "down"
    gate_statuses[id].last = time.time()


async def set_bell_on_in(id: str, delay: float):
    # Delay activation of bell by given value
    if delay > 0:
        await asyncio.sleep(delay)

    # Update its state
    bell_statuses[id].status = "on"
    bell_statuses[id].last = time.time()


async def set_light_on_in(id: str, delay: float):
    # Delay activation of lights by given value
    if delay > 0:
        await asyncio.sleep(delay)

    # Update its state
    light_statuses[id].status = "on"
    light_statuses[id].last = time.time()
