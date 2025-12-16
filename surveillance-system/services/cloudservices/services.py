import ContextVariable_pb2

import cv2
import uvicorn

import numpy as np

from fastapi import FastAPI, Request, HTTPException, Response

import json
import os
import random
import base64
import time
import hashlib

local_random = random.Random(os.getpid())

app = FastAPI()

# Decide whether protobuf should be used (optional environment variable)
proto = "PROTO" not in os.environ or os.environ["PROTO"].lower() in ["true", "t", "1"]


# For logging detection times
def log_hash(data: bytes):
    # Compute a consistent hash
    sha256 = hashlib.sha256()
    sha256.update(data)
    hash = sha256.hexdigest()

    # Acquire the current timestamp in milliseconds
    timestamp = time.time_ns() / 1_000_000.0
    log_entry = f"{hash},{timestamp}\n"

    # Append to log file
    with open("/tmp/log_analysis.csv", "a") as log_file:
        log_file.write(log_entry)


@app.post("/analyze")
async def detect(request: Request):
    time_start = time.time_ns() / 1_000_000.0

    if proto:
        # Read the raw request body
        body = await request.body()

        # Parse the protobuf message
        context_variables = ContextVariable_pb2.ContextVariables()
        context_variables.ParseFromString(body)

        # Extract the image from the protobuf message
        image_bytes = None
        for context_variable in context_variables.data:
            if context_variable.name == "image":
                image_bytes = context_variable.value.bytes
                break
    else:
        # Parse the request variables
        context_variables = await request.json()

        # Get the image from the request json
        if "image" in context_variables:
            image_bytes = base64.b64decode(context_variables["image"].encode("utf-8"))

    if image_bytes is None:
        raise HTTPException(status_code=400, detail="No image provided in the request")

    # Read the image
    np_arr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if image is None:
        raise HTTPException(status_code=400, detail="Failed to decode the image")

    is_threat = local_random.random() < (1.0 / 5.0)

    # Prepare output data
    if proto:
        # Create response protobuf message
        response_context_variables = ContextVariable_pb2.ContextVariables()
        threats_context_variable = ContextVariable_pb2.ContextVariable(
            name="hasThreat",
            value=ContextVariable_pb2.Value(bool=is_threat),
        )
        response_context_variables.data.append(threats_context_variable)

        # Serialize the response to protobuf format
        response = response_context_variables.SerializeToString()
        media_type = "application/x-protobuf"
    else:
        response = json.dumps({"hasThreat": is_threat})
        media_type = "application/json"

    time_end = time.time_ns() / 1_000_000.0

    with open("/tmp/time_analysis.csv", "a") as log_file:
        log_file.write(f"{time_end - time_start}\n")

    # Log data
    log_hash(image_bytes)

    # Return the protobuf response
    return Response(content=response, media_type=media_type)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
