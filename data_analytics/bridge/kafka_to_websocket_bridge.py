# data_analytics/bridge/kafka_to_websocket_bridge.py

import asyncio
import json
import websockets
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
import threading

# --- Configuration ---
KAFKA_BROKER = 'localhost:9092'
KAFKA_TOPIC = 'vehicle-telemetry'
WEBSOCKET_HOST = 'localhost'
WEBSOCKET_PORT = 8765

# A set to keep track of all connected WebSocket clients
CONNECTED_CLIENTS = set()

def kafka_consumer_thread():
    """
    This function runs in a separate thread to consume messages from Kafka
    and broadcast them to all connected WebSocket clients.
    """
    try:
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BROKER,
            auto_offset_reset='latest', # We only care about the most recent data
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        print("Kafka Consumer thread started, listening for messages...")
    except NoBrokersAvailable:
        print(f"Error: Could not connect to Kafka broker at {KAFKA_BROKER}. Exiting thread.")
        return
    
    for message in consumer:
        telemetry_data = message.value
        print(f"Kafka -> Bridge: Received data for {telemetry_data.get('vehicle_id')}")
        
        # The actual broadcast is handled by the main asyncio loop
        # to ensure thread safety with websockets.
        asyncio.run_coroutine_threadsafe(
            broadcast(json.dumps(telemetry_data)), 
            asyncio.get_event_loop()
        )

async def broadcast(message):
    """
    Broadcasts a message to all currently connected clients.
    """
    if CONNECTED_CLIENTS:
        # Create a list of tasks to send the message to all clients concurrently
        tasks = [client.send(message) for client in CONNECTED_CLIENTS]
        await asyncio.gather(*tasks)
        print(f"Bridge -> WebSocket: Broadcasted message to {len(CONNECTED_CLIENTS)} client(s).")

async def handler(websocket, path):
    """
    Handles new WebSocket connections. Registers the client and keeps the connection open.
    """
    print(f"Client connected from {websocket.remote_address}")
    CONNECTED_CLIENTS.add(websocket)
    try:
        # Keep the connection alive by waiting for messages (we don't expect any)
        # The connection will close if the client disconnects.
        async for message in websocket:
            # This part is for messages from client to server, which we don't use here.
            print(f"Received message from client (unexpected): {message}")
            pass
    except websockets.exceptions.ConnectionClosed:
        print(f"Client disconnected from {websocket.remote_address}")
    finally:
        # Unregister the client upon disconnection
        CONNECTED_CLIENTS.remove(websocket)

async def main():
    """
    Main async function to start the WebSocket server.
    """
    # Start the Kafka consumer in a background daemon thread
    # This allows the asyncio event loop to run without being blocked by the Kafka consumer
    kafka_thread = threading.Thread(target=kafka_consumer_thread, daemon=True)
    kafka_thread.start()
    
    # Start the WebSocket server
    server = await websockets.serve(handler, WEBSOCKET_HOST, WEBSOCKET_PORT)
    print(f"WebSocket server started at ws://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}")
    
    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
