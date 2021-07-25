from marshmallow import Schema as BaseSchema
from marshmallow import SchemaOpts as BaseSchemaOpts
from marshmallow import fields, validate
from marshmallow_enum import EnumField

from .models import Corrected, Correction, CorrectionEdit, Play, PlayEdit, RecordedPlay


class SchemaOpts(BaseSchemaOpts):
    def __init__(self, meta, *args, **kwargs):
        super().__init__(meta, *args, **kwargs)

        self.model = getattr(meta, "model", None)


class Schema(BaseSchema):
    OPTIONS_CLASS = SchemaOpts

    def load(self, data, *, many: bool = None, **kwargs):
        all_loaded = super().load(data, many=many, **kwargs)
        many = self.many if many is None else bool(many)
        if many:
            return [self.opts.model(**loaded) for loaded in all_loaded]
        else:
            return self.opts.model(**all_loaded)


def field_str(**kwargs) -> fields.Str:
    kwargs.setdefault("validate", validate.Length(min=1))
    return fields.Str(required=True, **kwargs)


def field_int(**kwargs) -> fields.Int:
    kwargs.setdefault("validate", validate.Range(min=1))
    return fields.Int(required=True, strict=True, **kwargs)


class PlaySchema(Schema):
    class Meta:
        model = Play

    track_uri = field_str()
    title = field_str()
    artist = field_str()
    album = field_str(validate=None)
    orig_title = field_str()
    orig_artist = field_str()
    orig_album = field_str(validate=None)
    corrected = EnumField(Corrected, required=True, by_value=True)
    musicbrainz_id = fields.Str(required=True, allow_none=True)
    duration = field_int()
    played_at = field_int()
    submitted_at = field_int(allow_none=True)


class RecordedPlaySchema(PlaySchema):
    class Meta:
        model = RecordedPlay

    play_id = field_int()


class PlayEditSchema(Schema):
    class Meta:
        model = PlayEdit

    play_id = field_int()
    track_uri = field_str()
    title = field_str()
    artist = field_str()
    album = field_str(validate=None)
    save_correction = fields.Bool(required=True)
    update_all_unsubmitted = fields.Bool(required=True)


class CorrectionSchema(Schema):
    class Meta:
        model = Correction

    track_uri = field_str()
    title = field_str()
    artist = field_str()
    album = field_str(validate=None)


class CorrectionEditSchema(Schema):
    class Meta:
        model = CorrectionEdit

    track_uri = field_str()
    title = field_str()
    artist = field_str()
    album = field_str(validate=None)
    update_all_unsubmitted = fields.Bool(required=True)


play_schema = PlaySchema()
recorded_play_schema = RecordedPlaySchema()
play_edit_schema = PlayEditSchema()
correction_schema = CorrectionSchema()
correction_edit_schema = CorrectionEditSchema()
