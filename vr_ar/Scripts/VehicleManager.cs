// vr_ar/Scripts/VehicleManager.cs

using UnityEngine;
using System.Collections.Generic;
using System.Collections.Concurrent; // For thread-safe collections
using WebSocketSharp; // You need to add the WebSocket-sharp library to your project

// This class matches the JSON structure from our Python simulator
[System.Serializable]
public class VehicleData
{
    public string vehicle_id;
    public string vehicle_type;
    public double latitude;
    public double longitude;
    public float speed_kmh;
}

// This class holds the processed data ready for the main thread
public class VehicleState
{
    public string ID;
    public Vector3 TargetPosition;
    public Quaternion TargetRotation;
}

public class VehicleManager : MonoBehaviour
{
    [Tooltip("The prefab to use for spawning new vehicles.")]
    public GameObject VehiclePrefab;
    
    [Tooltip("The WebSocket server address.")]
    public string ServerAddress = "ws://localhost:8765";

    private WebSocket ws;
    private readonly ConcurrentQueue<string> receivedMessages = new ConcurrentQueue<string>();
    
    // Dictionary to keep track of spawned vehicles using their ID
    private Dictionary<string, GameObject> vehicleInstances = new Dictionary<string, GameObject>();
    private Dictionary<string, VehicleState> vehicleStates = new Dictionary<string, VehicleState>();
    
    // --- GPS to World Coordinate Conversion ---
    // Center of our map in GPS coordinates (e.g., Kyiv)
    private const float ReferenceLatitude = 50.4501f;
    // Earth radius in meters
    private const float EarthRadius = 6378137f;
    // Scale factor to make the movement visible in the scene
    private const float MapScale = 50f;

    void Start()
    {
        ConnectToServer();
    }

    void Update()
    {
        // Process messages from the queue on the main thread
        while (receivedMessages.TryDequeue(out string message))
        {
            ProcessMessage(message);
        }

        // Update vehicle positions and rotations smoothly
        foreach (var state in vehicleStates.Values)
        {
            if (vehicleInstances.TryGetValue(state.ID, out GameObject vehicle))
            {
                // Smoothly move the vehicle towards its target position
                vehicle.transform.position = Vector3.Lerp(vehicle.transform.position, state.TargetPosition, Time.deltaTime * 2.0f);
                // Smoothly rotate the vehicle to face its direction of movement
                vehicle.transform.rotation = Quaternion.Slerp(vehicle.transform.rotation, state.TargetRotation, Time.deltaTime * 5.0f);
            }
        }
    }

    private void ConnectToServer()
    {
        Debug.Log($"Connecting to WebSocket server at {ServerAddress}...");
        ws = new WebSocket(ServerAddress);

        // This event is fired when a message is received. It runs on a background thread.
        ws.OnMessage += (sender, e) =>
        {
            // We can't use Unity API here. Just queue the data for the main thread.
            receivedMessages.Enqueue(e.Data);
        };

        ws.OnOpen += (sender, e) => Debug.Log("WebSocket connection opened.");
        ws.OnError += (sender, e) => Debug.LogError($"WebSocket Error: {e.Message}");
        ws.OnClose += (sender, e) => Debug.LogWarning($"WebSocket connection closed: {e.Reason}");

        ws.ConnectAsync();
    }

    private void ProcessMessage(string jsonMessage)
    {
        try
        {
            VehicleData data = JsonUtility.FromJson<VehicleData>(jsonMessage);
            if (data == null || string.IsNullOrEmpty(data.vehicle_id)) return;

            // Convert GPS to local world coordinates
            Vector3 worldPosition = ConvertGpsToLocal(data.latitude, data.longitude);

            if (!vehicleStates.ContainsKey(data.vehicle_id))
            {
                // If this is a new vehicle, spawn it
                SpawnVehicle(data.vehicle_id, worldPosition);
            }
            
            // Update the state for this vehicle
            VehicleState currentState = vehicleStates[data.vehicle_id];
            
            // Calculate rotation to look towards the new position
            Vector3 direction = worldPosition - currentState.TargetPosition;
            Quaternion rotation = Quaternion.identity;
            if (direction.sqrMagnitude > 0.01f) // Only rotate if there's movement
            {
                rotation = Quaternion.LookRotation(direction);
            }

            // Update the state
            currentState.TargetPosition = worldPosition;
            if (direction.sqrMagnitude > 0.01f)
            {
                currentState.TargetRotation = rotation;
            }
        }
        catch (System.Exception e)
        {
            Debug.LogError($"Failed to process message: {jsonMessage}. Error: {e.Message}");
        }
    }

    private void SpawnVehicle(string id, Vector3 initialPosition)
    {
        if (VehiclePrefab == null)
        {
            Debug.LogError("Vehicle Prefab is not set in the VehicleManager!");
            return;
        }
        
        Debug.Log($"Spawning new vehicle with ID: {id}");
        GameObject newVehicle = Instantiate(VehiclePrefab, initialPosition, Quaternion.identity);
        newVehicle.name = $"Vehicle_{id}";
        
        vehicleInstances[id] = newVehicle;
        vehicleStates[id] = new VehicleState { ID = id, TargetPosition = initialPosition, TargetRotation = Quaternion.identity };
    }

    // Converts GPS coordinates to local world coordinates using Mercator projection
    private Vector3 ConvertGpsToLocal(double latitude, double longitude)
    {
        // This is a simplified Mercator projection, suitable for small areas.
        float x = (float)(EarthRadius * (longitude * Mathf.Deg2Rad - ReferenceLatitude * Mathf.Deg2Rad) * MapScale);
        float z = (float)(EarthRadius * Mathf.Log(Mathf.Tan(Mathf.PI / 4 + (float)latitude * Mathf.Deg2Rad / 2)) * MapScale);
        
        // We use x and z, as y is typically the vertical axis in Unity.
        return new Vector3(x, 0, z);
    }

    void OnDestroy()
    {
        // Ensure the WebSocket connection is closed when the object is destroyed
        if (ws != null && ws.IsAlive)
        {
            Debug.Log("Closing WebSocket connection.");
            ws.Close();
        }
    }
}
