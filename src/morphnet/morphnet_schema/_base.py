from __future__ import annotations

from enum import IntEnum
from typing import Any, ClassVar, Self, get_args, get_origin

from google.protobuf.message import Message as ProtoMessage
from pydantic import BaseModel, ConfigDict


class ProtoModel(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
    )

    _proto_type: ClassVar[type[ProtoMessage]]

    def to_proto(self) -> ProtoMessage:
        kwargs: dict[str, Any] = {}
        proto_field_names = {
            fd.name for fd in self._proto_type.DESCRIPTOR.fields
        }
        for field_name, field_info in type(self).model_fields.items():
            value = getattr(self, field_name)
            if value is None:
                continue
            proto_field_name = field_info.alias or field_name
            if proto_field_name not in proto_field_names:
                continue
            kwargs[proto_field_name] = _to_proto_value(value)
        return self._proto_type(**kwargs)

    def to_proto_bytes(self) -> bytes:
        return self.to_proto().SerializeToString()

    @classmethod
    def from_proto_bytes(cls, data: bytes) -> Self:
        proto_msg = cls._proto_type.FromString(data)
        return cls.from_proto(proto_msg)

    def to_json(self, **kwargs: Any) -> str:
        return self.model_dump_json(**kwargs)

    @classmethod
    def from_json(cls, json_str: str) -> Self:
        return cls.model_validate_json(json_str)

    def to_yaml(self, **kwargs: Any) -> str:
        from pydantic_yaml import to_yaml_str

        return to_yaml_str(self, **kwargs)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> Self:
        from pydantic_yaml import parse_yaml_raw_as

        return parse_yaml_raw_as(cls, yaml_str)

    @classmethod
    def from_proto(cls, proto_msg: ProtoMessage) -> Self:
        kwargs: dict[str, Any] = {}
        field_alias_map = _build_alias_map(cls)

        descriptor = type(proto_msg).DESCRIPTOR
        for field_descriptor in descriptor.fields:  # ty: ignore[unresolved-attribute]
            proto_field_name = field_descriptor.name
            python_field_name = field_alias_map.get(proto_field_name, proto_field_name)
            if python_field_name not in cls.model_fields:
                continue

            field_info = cls.model_fields[python_field_name]
            annotation = field_info.annotation

            is_repeated = field_descriptor.is_repeated
            is_message = field_descriptor.message_type is not None
            is_map = (
                is_repeated
                and is_message
                and field_descriptor.message_type.GetOptions().map_entry
            )

            if is_map:
                raw_map = getattr(proto_msg, proto_field_name)
                value_model_cls = _resolve_dict_value_type(annotation)
                if value_model_cls is not None:
                    kwargs[python_field_name] = {
                        k: value_model_cls.from_proto(v) for k, v in raw_map.items()
                    }
                else:
                    kwargs[python_field_name] = dict(raw_map)

            elif is_repeated and is_message:
                raw = getattr(proto_msg, proto_field_name)
                nested_cls = _resolve_list_item_type(annotation)
                if nested_cls is not None:
                    kwargs[python_field_name] = [
                        nested_cls.from_proto(item) for item in raw
                    ]
                else:
                    kwargs[python_field_name] = list(raw)

            elif is_repeated:
                raw = getattr(proto_msg, proto_field_name)
                kwargs[python_field_name] = list(raw)

            elif is_message:
                if not proto_msg.HasField(proto_field_name):
                    continue
                raw = getattr(proto_msg, proto_field_name)
                nested_cls = _resolve_proto_model_type(annotation)
                if nested_cls is not None:
                    kwargs[python_field_name] = nested_cls.from_proto(raw)
                else:
                    kwargs[python_field_name] = raw

            else:
                raw = getattr(proto_msg, proto_field_name)
                oneof = field_descriptor.containing_oneof
                if oneof is not None:
                    if proto_msg.HasField(proto_field_name):
                        enum_cls = _resolve_enum_type(annotation)
                        kwargs[python_field_name] = (
                            enum_cls(raw) if enum_cls is not None else raw
                        )
                else:
                    enum_cls = _resolve_enum_type(annotation)
                    if enum_cls is not None:
                        kwargs[python_field_name] = enum_cls(raw)
                    elif raw != field_descriptor.default_value:
                        kwargs[python_field_name] = raw

        return cls(**kwargs)


def _build_alias_map(cls: type[ProtoModel]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for field_name, field_info in cls.model_fields.items():
        alias = field_info.alias
        if alias and alias != field_name:
            mapping[alias] = field_name
        else:
            mapping[field_name] = field_name
    return mapping


def _to_proto_value(value: Any) -> Any:
    if isinstance(value, ProtoModel):
        return value.to_proto()
    if isinstance(value, list):
        return [_to_proto_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_proto_value(val) for key, val in value.items()}
    if isinstance(value, IntEnum):
        return int(value)
    return value


def _resolve_proto_model_type(annotation: Any) -> type[ProtoModel] | None:
    for arg in _flatten_union_args(annotation):
        if isinstance(arg, type) and issubclass(arg, ProtoModel):
            return arg
    return None


def _resolve_list_item_type(annotation: Any) -> type[ProtoModel] | None:
    for arg in _flatten_union_args(annotation):
        origin = get_origin(arg)
        if origin is list:
            inner_args = get_args(arg)
            if inner_args:
                return _resolve_proto_model_type(inner_args[0])
    return None


def _resolve_dict_value_type(annotation: Any) -> type[ProtoModel] | None:
    for arg in _flatten_union_args(annotation):
        origin = get_origin(arg)
        if origin is dict:
            inner_args = get_args(arg)
            if len(inner_args) >= 2:
                return _resolve_proto_model_type(inner_args[1])
    return None


def _resolve_enum_type(annotation: Any) -> type[IntEnum] | None:
    for arg in _flatten_union_args(annotation):
        if isinstance(arg, type) and issubclass(arg, IntEnum):
            return arg
    return None


def _flatten_union_args(annotation: Any) -> list[Any]:
    origin = get_origin(annotation)
    if origin is type(int | str):
        return list(get_args(annotation))
    return [annotation]
