import zenoh
import time
import Event_pb2
import uuid

def main():
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

        session.declare_subscriber("events/sink/shutdown", listener)

        input("Press Enter to quit\n")

if __name__ == "__main__":
    main()