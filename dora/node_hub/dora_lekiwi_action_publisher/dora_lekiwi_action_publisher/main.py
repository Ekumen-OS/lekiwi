"""TODO: Add docstring."""

import os

import pyarrow as pa

from dora import Node  # type: ignore


def main() -> None:
    """TODO: Add docstring."""
    node = Node()

    # Process environment variables
    LEKIWI_ACTION = os.getenv(
        "LEKIWI_ACTION", "[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]"
    )
    if not LEKIWI_ACTION:
        raise ValueError("LEKIWI_ACTION environment variable is not set.")
    # Convert to a list of floats
    action_to_send = [float(x) for x in LEKIWI_ACTION.strip("[]").strip(" ").split(",")]
    print(f"Action to send: {action_to_send}")

    for event in node:
        if event["type"] == "INPUT":
            if event["id"] == "tick":
                metadata = event["metadata"]
                metadata["primitive"] = "series"
                node.send_output(
                    output_id="actions",
                    data=pa.array(action_to_send),
                    metadata=metadata,
                )


if __name__ == "__main__":
    main()
