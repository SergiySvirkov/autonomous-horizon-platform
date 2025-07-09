# data_analytics/consumers/realtime_analyzer.py

import json
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable

# --- Configuration ---
KAFKA_BROKER = 'localhost:9092'
KAFKA_TOPIC = 'vehicle-telemetry'
CONSUMER_GROUP_ID = 'realtime-analytics-group' # Allows multiple instances to share the load

# --- Alerting Thresholds ---
LOW_BATTERY_THRESHOLD = 0.20 # Alert if battery is below 20%
HIGH_SPEED_THRESHOLD_SHUTTLE = 90 # km/h
HIGH_SPEED_THRESHOLD_EVTOL = 300 # km/h

def create_kafka_consumer(broker_url, topic, group_id):
    """Creates and returns a Kafka consumer."""
    try:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=broker_url,
            auto_offset_reset='earliest', # Start reading from the beginning of the topic
            group_id=group_id,
            # Deserialize JSON messages from UTF-8 bytes
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            # Use a client ID for easier tracking
            client_id='realtime-analyzer-1'
        )
        print(f"Successfully connected to Kafka and subscribed to topic '{topic}'")
        return consumer
    except NoBrokersAvailable:
        print(f"Error: Could not connect to any Kafka brokers at {broker_url}.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def analyze_telemetry(data):
    """Performs simple analysis on a single telemetry message."""
    vehicle_id = data.get('vehicle_id', 'N/A')
    vehicle_type = data.get('vehicle_type', 'unknown')
    
    # 1. Check for low battery
    battery_level = data.get('battery_level')
    if battery_level is not None and battery_level < LOW_BATTERY_THRESHOLD:
        print(f"  [ALERT] LOW BATTERY! Vehicle: {vehicle_id}, Level: {battery_level:.2f}")

    # 2. Check for high speed
    speed = data.get('speed_kmh')
    if speed is not None:
        if vehicle_type == 'shuttle' and speed > HIGH_SPEED_THRESHOLD_SHUTTLE:
            print(f"  [ALERT] HIGH SPEED! Shuttle: {vehicle_id}, Speed: {speed:.1f} km/h")
        elif vehicle_type == 'eVTOL' and speed > HIGH_SPEED_THRESHOLD_EVTOL:
            print(f"  [ALERT] HIGH SPEED! eVTOL: {vehicle_id}, Speed: {speed:.1f} km/h")
            
    # In the future, this function could:
    # - Push alerts to a dedicated alerting system (e.g., PagerDuty)
    # - Store anomalous events in a database for later review
    # - Trigger an MLOps pipeline to retrain a model if data drift is detected

def main():
    """Main function to run the consumer loop."""
    consumer = create_kafka_consumer(KAFKA_BROKER, KAFKA_TOPIC, CONSUMER_GROUP_ID)
    if not consumer:
        return

    print("Starting real-time analyzer. Waiting for messages...")
    
    try:
        for message in consumer:
            # message object contains topic, partition, offset, key, value, etc.
            telemetry_data = message.value
            print(f"Received: ID={telemetry_data.get('vehicle_id')}, "
                  f"Lat={telemetry_data.get('latitude')}, Lon={telemetry_data.get('longitude')}")
            
            # Perform analysis on the received data
            analyze_telemetry(telemetry_data)
            
    except KeyboardInterrupt:
        print("\nAnalyzer stopped by user.")
    finally:
        if consumer:
            print("Closing Kafka consumer...")
            consumer.close()
            print("Consumer closed.")

if __name__ == "__main__":
    main()
