from marshmallow import Schema, fields


class TokenSchema(Schema):
    access_token = fields.Str(required=True)
    refresh_token = fields.Str(required=False)
    token_type = fields.Str(required=True)

