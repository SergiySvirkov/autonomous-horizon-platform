# data_analytics/simulators/vehicle_telemetry.py

import json
import time
import random
import uuid
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

# --- Configuration ---
KAFKA_BROKER = 'localhost:9092'
KAFKA_TOPIC = 'vehicle-telemetry'
SIMULATION_INTERVAL_SECONDS = 2  # Time to wait between sending messages

# --- Vehicle Definitions ---
# We'll simulate multiple vehicles to make it more realistic.
VEHICLES = [
    {"id": "zoox-01", "type": "shuttle", "lat": 50.4501, "lon": 30.5234}, # Maidan Nezalezhnosti, Kyiv
    {"id": "zoox-02", "type": "shuttle", "lat": 50.4547, "lon": 30.5208}, # St. Michael's Square
    {"id": "evtol-01", "type": "eVTOL", "lat": 50.4438, "lon": 30.5163}   # Taras Shevchenko National University
]

def create_kafka_producer(broker_url):
    """Creates and returns a Kafka producer, handling connection errors."""
    try:
        producer = KafkaProducer(
            bootstrap_servers=broker_url,
            # Serialize values as JSON and encode to UTF-8
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            # Use a client ID for easier tracking in Kafka logs
            client_id='telemetry-simulator'
        )
        print(f"Successfully connected to Kafka broker at {broker_url}")
        return producer
    except NoBrokersAvailable:
        print(f"Error: Could not connect to any Kafka brokers at {broker_url}.")
        print("Please ensure Kafka is running and accessible.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while connecting to Kafka: {e}")
        return None

def simulate_vehicle_movement(vehicle):
    """Generates new telemetry data for a single vehicle."""
    # Simulate slight random movement
    vehicle['lat'] += (random.random() - 0.5) * 0.001
    vehicle['lon'] += (random.random() - 0.5) * 0.001

    # Generate telemetry data
    data = {
        "message_id": str(uuid.uuid4()), # Unique ID for each message
        "vehicle_id": vehicle['id'],
        "vehicle_type": vehicle['type'],
        "timestamp_utc": time.time(), # Use UTC timestamp
        "latitude": round(vehicle['lat'], 6),
        "longitude": round(vehicle['lon'], 6),
        "speed_kmh": random.uniform(20, 60) if vehicle['type'] == 'shuttle' else random.uniform(100, 250),
        "battery_level": round(random.uniform(0.15, 0.99), 2) # Include low battery scenarios
    }
    return data

def main():
    """Main function to run the simulation loop."""
    producer = create_kafka_producer(KAFKA_BROKER)
    if not producer:
        return # Exit if producer could not be created

    print(f"Starting telemetry simulation for {len(VEHICLES)} vehicles...")
    print(f"Sending data to Kafka topic: '{KAFKA_TOPIC}'")
    
    try:
        while True:
            # Choose a random vehicle to send data for
            vehicle_to_update = random.choice(VEHICLES)
            
            # Generate new data
            telemetry_data = simulate_vehicle_movement(vehicle_to_update)
            
            # Send data to Kafka
            producer.send(KAFKA_TOPIC, value=telemetry_data)
            
            print(f"Sent -> ID: {telemetry_data['vehicle_id']}, "
                  f"Speed: {telemetry_data['speed_kmh']:.1f} km/h, "
                  f"Battery: {telemetry_data['battery_level']:.2f}")
            
            # Wait for the next interval
            time.sleep(SIMULATION_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\nSimulation stopped by user.")
    finally:
        if producer:
            print("Flushing messages and closing producer...")
            producer.flush() # Ensure all messages are sent
            producer.close()
            print("Producer closed.")

if __name__ == "__main__":
    main()
