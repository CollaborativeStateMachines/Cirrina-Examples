import zenoh
import time
import asyncio
import Event_pb2
import uuid

async def main():

    with zenoh.open(zenoh.Config()) as session:
            evt = Event_pb2.Event(
                    topic="start",
                    channel=Event_pb2.Event.PERIPHERAL,
                    data=[],
                    target="",
                    source="",
                    id=str(uuid.uuid4()),
                    createdTime=int(time.time() * 1000),
                )
            start = time.time()
            session.put(
                "events/peripheral/start",
                evt.SerializeToString(),
                encoding=zenoh.Encoding.APPLICATION_PROTOBUF,
            )
            print(f"Published: {evt}")

            def listener(sample: zenoh.Sample):
                end = time.time()
                print(f"Done. Actual Duration: {end - start:.4f} seconds")

            session.declare_subscriber("events/mall/done", listener)
            while True:
                time.sleep(0.01)

if __name__ == "__main__":
    asyncio.run(main())