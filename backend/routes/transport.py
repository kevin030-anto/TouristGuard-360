from flask import Blueprint, request, jsonify
import random
from datetime import datetime, timedelta

transport_bp = Blueprint('transport', __name__, url_prefix='/api/transport')

# Mock bus data
MOCK_BUSES = [
    {'id': 'B001', 'name': 'City Express', 'type': 'AC'},
    {'id': 'B002', 'name': 'Metro Liner', 'type': 'Non-AC'},
    {'id': 'B003', 'name': 'Rapid Transit', 'type': 'AC'},
    {'id': 'B004', 'name': 'Local Shuttle', 'type': 'Non-AC'},
    {'id': 'B005', 'name': 'Super Deluxe', 'type': 'AC'},
    {'id': 'B006', 'name': 'Standard Express', 'type': 'Non-AC'},
]

# Mock railway stations
MOCK_STATIONS = [
    'Central Station', 'North Terminal', 'South Junction', 'East Hub',
    'West Point', 'Airport Station', 'University Station', 'Harbor Station',
    'Downtown Station', 'Suburban Station', 'Industrial Station', 'Park Station'
]

# Mock train data
MOCK_TRAINS = [
    {'id': 'T001', 'name': 'Shinkansen Express', 'type': 'High-Speed'},
    {'id': 'T002', 'name': 'Regional Line', 'type': 'Regular'},
    {'id': 'T003', 'name': 'Intercity Fast', 'type': 'Express'},
    {'id': 'T004', 'name': 'Metro Rail', 'type': 'Local'},
    {'id': 'T005', 'name': 'Night Rider', 'type': 'Sleeper'},
    {'id': 'T006', 'name': 'Morning Star', 'type': 'Express'},
]


@transport_bp.route('/buses', methods=['GET'])
def search_buses():
    """Search for buses between two locations (mock data)."""
    from_loc = request.args.get('from', 'Current Location')
    to_loc = request.args.get('to', 'Unknown')

    if not to_loc or to_loc == 'Unknown':
        return jsonify({'error': 'Destination required'}), 400

    # Generate mock results
    num_results = random.randint(2, len(MOCK_BUSES))
    selected_buses = random.sample(MOCK_BUSES, num_results)

    results = []
    base_time = datetime.now().replace(minute=0, second=0, microsecond=0)
    
    for i, bus in enumerate(selected_buses):
        departure = base_time + timedelta(minutes=random.randint(10, 120))
        travel_minutes = random.randint(30, 180)
        arrival = departure + timedelta(minutes=travel_minutes)

        results.append({
            'id': bus['id'],
            'name': bus['name'],
            'type': bus['type'],
            'from': from_loc,
            'to': to_loc,
            'departure': departure.strftime('%H:%M'),
            'arrival': arrival.strftime('%H:%M'),
            'duration': f'{travel_minutes // 60}h {travel_minutes % 60}m',
            'fare': round(random.uniform(50, 500), 2),
            'available_seats': random.randint(5, 45),
            'route': f'{from_loc} → Stop {i+1} → Stop {i+2} → {to_loc}'
        })

    return jsonify({
        'from': from_loc,
        'to': to_loc,
        'count': len(results),
        'buses': sorted(results, key=lambda x: x['departure'])
    })


@transport_bp.route('/trains', methods=['GET'])
def search_trains():
    """Search for trains between two stations (mock data)."""
    from_station = request.args.get('from', '')
    to_station = request.args.get('to', '')
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))

    if not from_station or not to_station:
        return jsonify({'error': 'From and To stations required'}), 400

    # Generate mock results
    num_results = random.randint(2, len(MOCK_TRAINS))
    selected_trains = random.sample(MOCK_TRAINS, num_results)

    results = []
    base_time = datetime.now().replace(minute=0, second=0, microsecond=0)

    for i, train in enumerate(selected_trains):
        departure = base_time + timedelta(minutes=random.randint(15, 180))
        travel_minutes = random.randint(60, 480)
        arrival = departure + timedelta(minutes=travel_minutes)

        results.append({
            'id': train['id'],
            'name': train['name'],
            'type': train['type'],
            'from': from_station,
            'to': to_station,
            'date': date,
            'departure': departure.strftime('%H:%M'),
            'arrival': arrival.strftime('%H:%M'),
            'duration': f'{travel_minutes // 60}h {travel_minutes % 60}m',
            'fare': {
                'general': round(random.uniform(100, 800), 2),
                'sleeper': round(random.uniform(300, 1500), 2),
                'first_class': round(random.uniform(500, 3000), 2),
            },
            'availability': {
                'general': random.randint(0, 100),
                'sleeper': random.randint(0, 50),
                'first_class': random.randint(0, 20),
            }
        })

    return jsonify({
        'from': from_station,
        'to': to_station,
        'date': date,
        'count': len(results),
        'trains': sorted(results, key=lambda x: x['departure'])
    })


@transport_bp.route('/stations', methods=['GET'])
def get_stations():
    """Get list of available railway stations."""
    return jsonify({'stations': MOCK_STATIONS})
