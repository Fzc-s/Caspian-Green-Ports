from marshmallow import Schema, fields, validate, ValidationError

class PortSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    lat = fields.Float(required=True, validate=validate.Range(min=-90, max=90))
    lng = fields.Float(required=True, validate=validate.Range(min=-180, max=180))
    air_quality = fields.Float(required=True, validate=validate.Range(min=0))
    water_quality = fields.Float(required=True, validate=validate.Range(min=0))
    co2_emissions = fields.Float(required=True, validate=validate.Range(min=0))
    incidents = fields.Int(required=True, validate=validate.Range(min=0))
    green_score = fields.Float(dump_only=True)

class ReportSchema(Schema):
    id = fields.Int(dump_only=True)
    port_id = fields.Int(required=True)
    user_email = fields.Email(required=True)
    description = fields.Str(required=True, validate=validate.Length(min=1))
    timestamp = fields.DateTime(dump_only=True)

class LoginSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True)