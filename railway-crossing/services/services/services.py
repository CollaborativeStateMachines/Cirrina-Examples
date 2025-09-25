from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from starlette.responses import Response
from starlette.status import HTTP_200_OK

import time

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
def gate_down(request: Request):
    # Retrieve the sender ID
    id = request.headers.get("Cirrina-Sender-ID")

    # Create the gate status if not seen before
    if id not in gate_statuses:
        gate_statuses[id] = GateStatus(status="up", last=time.time())

    # Update its state
    gate_statuses[id].status = "down"

    return Response(status_code=HTTP_200_OK)


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
async def light_on(request: Request):
    # Retrieve the sender ID
    id = request.headers.get("Cirrina-Sender-ID")

    # Create the gate status if not seen before
    if id not in light_statuses:
        light_statuses[id] = LightStatus(status="off", last=time.time())

    # Update its state
    light_statuses[id].status = "on"

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


@app.post("/bell/on")
async def bell_on(request: Request):
    # Retrieve the sender ID
    id = request.headers.get("Cirrina-Sender-ID")

    # Create the gate status if not seen before
    if id not in bell_statuses:
        bell_statuses[id] = BellStatus(status="off", last=time.time())

    # Update its state
    bell_statuses[id].status = "on"

    return Response(status_code=HTTP_200_OK)


@app.post("/bell/off")
async def bell_off(request: Request):
    # Retrieve the sender ID
    id = request.headers.get("Cirrina-Sender-ID")

    # Create the gate status if not seen before
    if id not in bell_statuses:
        bell_statuses[id] = BellStatus(status="off", last=time.time())

    # Update its state
    bell_statuses[id].status = "off"

    return Response(status_code=HTTP_200_OK)
