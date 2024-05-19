import serial
import time
import pyodbc
from flask import Flask, render_template, jsonify
from threading import Thread

app = Flask('app')
# Add this block of code
app.config['STATIC_FOLDER'] = 'templates'
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Initialize serial communication
ser = serial.Serial('COM4', 9600)

# Database connection string
conn_str = (
    r'DRIVER={ODBC Driver 17 for SQL Server};'
    r'SERVER=localhost;'
    r'DATABASE=SensorData;'
    r'Trusted_Connection=yes;'
)

# Create a connection object
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# Sensor thresholds
sensor_thresholds = {
    'soundValue': 700,
    'raw_light': 100,
    'temperature': 50.0,
    'humidity': 100.0,
    'pressure': 150000.0,
    'x_accel': 10.0,
    'y_accel': 10.0,
    'z_accel': 10.0
}

# SQL insert statement
insert_stmt = '''
    INSERT INTO SD (sound, light, temp, humidity, pressure, x_accel, y_accel, z_accel)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
'''

# Initialize sensor data
sensor_data = {
    'soundValue': 0,
    'raw_light': 0,
    'temperature': 0.0,
    'humidity': 0.0,
    'pressure': 0.0,
    'x_accel': 0.0,
    'y_accel': 0.0,
    'z_accel': 0.0
}

@app.route('/')
def index():
    return render_template('dashboard.html', sensor_data=sensor_data, thresholds=sensor_thresholds)

@app.route('/<path:path>')
def send_static(path):
    return send_from_directory('templates', path)

@app.route('/data')
def data():
    return jsonify(sensor_data)

def collect_data():
    global sensor_data
    while True:
        ser.write(b'collect_data')
        data = ser.readline().decode().strip().split(',')
        
        # Check if we received the correct number of data points
        if len(data) == 8:
            sensor_data = {
                'soundValue': int(data[0]),
                'raw_light': int(data[1]),
                'temperature': float(data[2]),
                'humidity': float(data[3]),
                'pressure': float(data[4]),
                'x_accel': float(data[5]),
                'y_accel': float(data[6]),
                'z_accel': float(data[7])
            }

            # Log any thresholds exceeded
            for sensor, threshold in sensor_thresholds.items():
                if sensor_data[sensor] > threshold:
                    print(f'Error: {sensor} sensor value {sensor_data[sensor]} exceeds threshold {threshold}')

            print('Sensor values:')
            for sensor, value in sensor_data.items():
                print(f'{sensor}: {value}')
            print()

            # Insert data into the database
            try:
                cursor.execute(insert_stmt, tuple(sensor_data.values()))
                conn.commit()
            except pyodbc.Error as err:
                print(f'Error: {err}')
        else:
            print(f"Received unexpected data format: {data}")

        time.sleep(0.5)

# Start the data collection in a separate thread
data_thread = Thread(target=collect_data)
data_thread.start()

if __name__ == '__main__':
    app.run(debug=True)

# Close the cursor and connection objects when the app stops
cursor.close()
conn.close()
