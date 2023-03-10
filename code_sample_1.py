from api.models import Vehicle, VehicleSpecs, Depot, Make, Model, Fuel, BusType, BodyType, BodySubtype, DriveType, AcUnit, Status
from api.lib.orm import save
from api.lib.db import conn, cursor

# A VehicleBuilder initializes with a single vehicle json response from FleetClient responses.
# When run, a Vehicle instance is built, saved to the database, and returned (if the data isn't already in database).
# Select vehicle data simultaneously saves to database as vehicle schema relations.

class VehicleBuilder:

    def __init__(self, response_vehicle):
        self.response_vehicle = response_vehicle

    # checks if vehicle exists in database
    # if vehicle is located in database, returns vehicle
    # if vehicle is not in database, saves select attributes for vehicle to database, calls add_vehicle_specs(), and returns Vehicle instance
    def run(self, conn, cursor):
        vehicle = Vehicle.find_by_fleetio_id(self.response_vehicle['id'], cursor)
        if vehicle:  
            vehicle.exists = True
            # update vehicle attributes in db if app updates database/builds vehicles in realtime?
        else:
            select_vehicle_attrs_dict = self.select_attributes_vehicle(conn, cursor)
            vehicle = Vehicle(**select_vehicle_attrs_dict)
            vehicle = save(vehicle, conn, cursor)
            vehicle.exists = False
            self.add_vehicle_specs(vehicle.id, conn, cursor)
        return vehicle

    # saves select attributes for vehicle specs to database and records vehicle foreign key
    def add_vehicle_specs(self, vehicle_id, conn, cursor):
        select_vehicle_specs_attrs_dict = self.select_attributes_vehicle_specs(vehicle_id, conn, cursor)
        vehicle_specs = VehicleSpecs(**select_vehicle_specs_attrs_dict)
        vehicle_specs = save(vehicle_specs, conn, cursor)
        vehicle_specs.exists = False

    # creates dictionary of selected vehicle attributes using vehicle json response
    # saves vehicle bus type, ac unit, depot, and status to database while recording foreign key indicators for vehicle
    def select_attributes_vehicle(self, conn, cursor):
        fleetio_id = self.response_vehicle.get('id')
        nycsbus_id = Vehicle.clean_nycsbus_id(self.response_vehicle.get('name'))
        year = self.check_int(self.response_vehicle.get('year'))  
        passenger_windows = self.check_int(self.response_vehicle.get('custom_fields', {}).get('passenger_windows'))
        back_wheels = self.check_int(self.response_vehicle.get('custom_fields', {}).get('count_back_wheels'))
        bus_type_id = BusType.find_or_create_id_by_name(self.response_vehicle.get('vehicle_type_name'), conn, cursor)
        ac_unit_id = AcUnit.find_or_create_id_by_name(self.response_vehicle.get('custom_fields', {}).get('ac_units'), conn, cursor)
        depot_id = Depot.find_or_create_id_by_name(self.response_vehicle.get('group_ancestry'), conn, cursor)
        status_id = Status.find_or_create_id_by_name(self.response_vehicle.get('vehicle_status_name'), conn, cursor)
        keys = ['fleetio_id', 'nycsbus_id', 'year', 'passenger_windows', 'back_wheels', 'bus_type_id', 'ac_unit_id', 'depot_id', 'status_id']
        values = [fleetio_id, nycsbus_id, year, passenger_windows, back_wheels, bus_type_id, ac_unit_id, depot_id, status_id]
        select_vehicle_attrs_dict = dict(zip(keys, values))
        return select_vehicle_attrs_dict

    # creates dictionary of selected vehicle specs attributes using vehicle json response
    # saves vehicle make, model, body type, body subtype, drive type, and fuel to database while recording foreign key indicators for vehicle specs
    def select_attributes_vehicle_specs(self, vehicle_id, conn, cursor):
        vehicle_id = vehicle_id
        vin = self.response_vehicle.get('vin')
        license_plate = self.response_vehicle.get('license_plate')
        odometer = self.check_int(self.response_vehicle.get('current_meter_value'))
        date_odometer = self.response_vehicle.get('current_meter_date')
        child_capacity = self.check_int(self.response_vehicle.get('custom_fields',{}).get('child_capacity'))
        adult_capacity = self.check_int(self.response_vehicle.get('custom_fields',{}).get('adult_capacity'))
        wheelchair_capacity = self.check_int(self.response_vehicle.get('custom_fields',{}).get('wheelchair_capacity'))
        make_id = Make.find_or_create_id_by_name(self.response_vehicle.get('make'), conn, cursor)
        model_id = Model.find_or_create_id_by_name(self.response_vehicle.get('model'), conn, cursor)
        body_type_id = BodyType.find_or_create_id_by_name(self.response_vehicle.get('specs', {}).get('body_type'), conn, cursor)
        body_subtype_id = BodySubtype.find_or_create_id_by_name(self.response_vehicle.get('specs', {}).get('body_subtype'), conn, cursor)
        drive_type_id = DriveType.find_or_create_id_by_name(self.response_vehicle.get('specs', {}).get('drive_type'), conn, cursor)
        fuel_id = Fuel.find_or_create_id_by_name(self.response_vehicle.get('fuel_type_name'), conn, cursor)
        keys = ['vehicle_id', 'vin', 'license_plate', 'odometer', 'date_odometer', 'child_capacity', 'adult_capacity', 'wheelchair_capacity', 'make_id', 'model_id', 'body_type_id', 'body_subtype_id', 'drive_type_id', 'fuel_id']
        values = [vehicle_id, vin, license_plate, odometer, date_odometer, child_capacity, adult_capacity, wheelchair_capacity, make_id, model_id, body_type_id, body_subtype_id, drive_type_id, fuel_id]
        select_vehicle_specs_attrs_dict = dict(zip(keys, values))
        return select_vehicle_specs_attrs_dict

    # for certain attributes, decimals can be rounded down and any data that can't be converted to an integer essentially indicates a null value
    # returns an integer if the value can be converted to an integer (i.e. a string integer or float decimal)
    # returns None if the value cannot be converted to an integer (i.e. text, empty string)
    def check_int(self, value):
        try:
            return int(value)
        except:
            return None