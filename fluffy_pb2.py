# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: fluffy.proto
# Protobuf Python Version: 5.27.2
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    27,
    2,
    '',
    'fluffy.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0c\x66luffy.proto\x12\x06\x66luffy\"*\n\x08\x46ileData\x12\x10\n\x08\x66ileName\x18\x01 \x01(\t\x12\x0c\n\x04\x64\x61ta\x18\x02 \x01(\x0c\"\x1c\n\x08\x46ileInfo\x12\x10\n\x08\x66ileName\x18\x01 \x01(\t\"#\n\x0fRequestFileList\x12\x10\n\x08isClient\x18\x01 \x01(\x08\" \n\x08\x46ileList\x12\x14\n\x0clstFileNames\x18\x01 \x03(\t2\xee\x01\n\x13\x44\x61taTransferService\x12\x32\n\nUploadFile\x12\x10.fluffy.FileData\x1a\x10.fluffy.FileInfo(\x01\x12\x34\n\x0c\x44ownloadFile\x12\x10.fluffy.FileInfo\x1a\x10.fluffy.FileData0\x01\x12\x35\n\rReplicateFile\x12\x10.fluffy.FileData\x1a\x10.fluffy.FileInfo(\x01\x12\x36\n\tListFiles\x12\x17.fluffy.RequestFileList\x1a\x10.fluffy.FileListB\x04H\x01P\x01\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'fluffy_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  _globals['DESCRIPTOR']._loaded_options = None
  _globals['DESCRIPTOR']._serialized_options = b'H\001P\001'
  _globals['_FILEDATA']._serialized_start=24
  _globals['_FILEDATA']._serialized_end=66
  _globals['_FILEINFO']._serialized_start=68
  _globals['_FILEINFO']._serialized_end=96
  _globals['_REQUESTFILELIST']._serialized_start=98
  _globals['_REQUESTFILELIST']._serialized_end=133
  _globals['_FILELIST']._serialized_start=135
  _globals['_FILELIST']._serialized_end=167
  _globals['_DATATRANSFERSERVICE']._serialized_start=170
  _globals['_DATATRANSFERSERVICE']._serialized_end=408
# @@protoc_insertion_point(module_scope)
