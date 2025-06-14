# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings

import fileService_pb2 as fileService__pb2

GRPC_GENERATED_VERSION = '1.66.1'
GRPC_VERSION = grpc.__version__
_version_not_supported = False

try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True

if _version_not_supported:
    raise RuntimeError(
        f'The grpc package installed is at version {GRPC_VERSION},'
        + f' but the generated code in fileService_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
    )


class FileserviceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.UploadFile = channel.stream_unary(
                '/fileservice.Fileservice/UploadFile',
                request_serializer=fileService__pb2.FileData.SerializeToString,
                response_deserializer=fileService__pb2.ack.FromString,
                _registered_method=True)
        self.DownloadFile = channel.unary_stream(
                '/fileservice.Fileservice/DownloadFile',
                request_serializer=fileService__pb2.FileInfo.SerializeToString,
                response_deserializer=fileService__pb2.FileData.FromString,
                _registered_method=True)
        self.FileSearch = channel.unary_unary(
                '/fileservice.Fileservice/FileSearch',
                request_serializer=fileService__pb2.FileInfo.SerializeToString,
                response_deserializer=fileService__pb2.ack.FromString,
                _registered_method=True)
        self.ReplicateFile = channel.stream_unary(
                '/fileservice.Fileservice/ReplicateFile',
                request_serializer=fileService__pb2.FileData.SerializeToString,
                response_deserializer=fileService__pb2.ack.FromString,
                _registered_method=True)
        self.FileList = channel.unary_unary(
                '/fileservice.Fileservice/FileList',
                request_serializer=fileService__pb2.UserInfo.SerializeToString,
                response_deserializer=fileService__pb2.FileListResponse.FromString,
                _registered_method=True)
        self.FileDelete = channel.unary_unary(
                '/fileservice.Fileservice/FileDelete',
                request_serializer=fileService__pb2.FileInfo.SerializeToString,
                response_deserializer=fileService__pb2.ack.FromString,
                _registered_method=True)
        self.UpdateFile = channel.stream_unary(
                '/fileservice.Fileservice/UpdateFile',
                request_serializer=fileService__pb2.FileData.SerializeToString,
                response_deserializer=fileService__pb2.ack.FromString,
                _registered_method=True)
        self.getClusterStats = channel.unary_unary(
                '/fileservice.Fileservice/getClusterStats',
                request_serializer=fileService__pb2.Empty.SerializeToString,
                response_deserializer=fileService__pb2.ClusterStats.FromString,
                _registered_method=True)
        self.getLeaderInfo = channel.unary_unary(
                '/fileservice.Fileservice/getLeaderInfo',
                request_serializer=fileService__pb2.ClusterInfo.SerializeToString,
                response_deserializer=fileService__pb2.ack.FromString,
                _registered_method=True)
        self.MetaDataInfo = channel.unary_unary(
                '/fileservice.Fileservice/MetaDataInfo',
                request_serializer=fileService__pb2.MetaData.SerializeToString,
                response_deserializer=fileService__pb2.ack.FromString,
                _registered_method=True)


class FileserviceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def UploadFile(self, request_iterator, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def DownloadFile(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def FileSearch(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ReplicateFile(self, request_iterator, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def FileList(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def FileDelete(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def UpdateFile(self, request_iterator, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def getClusterStats(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def getLeaderInfo(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def MetaDataInfo(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_FileserviceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'UploadFile': grpc.stream_unary_rpc_method_handler(
                    servicer.UploadFile,
                    request_deserializer=fileService__pb2.FileData.FromString,
                    response_serializer=fileService__pb2.ack.SerializeToString,
            ),
            'DownloadFile': grpc.unary_stream_rpc_method_handler(
                    servicer.DownloadFile,
                    request_deserializer=fileService__pb2.FileInfo.FromString,
                    response_serializer=fileService__pb2.FileData.SerializeToString,
            ),
            'FileSearch': grpc.unary_unary_rpc_method_handler(
                    servicer.FileSearch,
                    request_deserializer=fileService__pb2.FileInfo.FromString,
                    response_serializer=fileService__pb2.ack.SerializeToString,
            ),
            'ReplicateFile': grpc.stream_unary_rpc_method_handler(
                    servicer.ReplicateFile,
                    request_deserializer=fileService__pb2.FileData.FromString,
                    response_serializer=fileService__pb2.ack.SerializeToString,
            ),
            'FileList': grpc.unary_unary_rpc_method_handler(
                    servicer.FileList,
                    request_deserializer=fileService__pb2.UserInfo.FromString,
                    response_serializer=fileService__pb2.FileListResponse.SerializeToString,
            ),
            'FileDelete': grpc.unary_unary_rpc_method_handler(
                    servicer.FileDelete,
                    request_deserializer=fileService__pb2.FileInfo.FromString,
                    response_serializer=fileService__pb2.ack.SerializeToString,
            ),
            'UpdateFile': grpc.stream_unary_rpc_method_handler(
                    servicer.UpdateFile,
                    request_deserializer=fileService__pb2.FileData.FromString,
                    response_serializer=fileService__pb2.ack.SerializeToString,
            ),
            'getClusterStats': grpc.unary_unary_rpc_method_handler(
                    servicer.getClusterStats,
                    request_deserializer=fileService__pb2.Empty.FromString,
                    response_serializer=fileService__pb2.ClusterStats.SerializeToString,
            ),
            'getLeaderInfo': grpc.unary_unary_rpc_method_handler(
                    servicer.getLeaderInfo,
                    request_deserializer=fileService__pb2.ClusterInfo.FromString,
                    response_serializer=fileService__pb2.ack.SerializeToString,
            ),
            'MetaDataInfo': grpc.unary_unary_rpc_method_handler(
                    servicer.MetaDataInfo,
                    request_deserializer=fileService__pb2.MetaData.FromString,
                    response_serializer=fileService__pb2.ack.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'fileservice.Fileservice', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('fileservice.Fileservice', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class Fileservice(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def UploadFile(request_iterator,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.stream_unary(
            request_iterator,
            target,
            '/fileservice.Fileservice/UploadFile',
            fileService__pb2.FileData.SerializeToString,
            fileService__pb2.ack.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def DownloadFile(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_stream(
            request,
            target,
            '/fileservice.Fileservice/DownloadFile',
            fileService__pb2.FileInfo.SerializeToString,
            fileService__pb2.FileData.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def FileSearch(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/fileservice.Fileservice/FileSearch',
            fileService__pb2.FileInfo.SerializeToString,
            fileService__pb2.ack.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def ReplicateFile(request_iterator,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.stream_unary(
            request_iterator,
            target,
            '/fileservice.Fileservice/ReplicateFile',
            fileService__pb2.FileData.SerializeToString,
            fileService__pb2.ack.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def FileList(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/fileservice.Fileservice/FileList',
            fileService__pb2.UserInfo.SerializeToString,
            fileService__pb2.FileListResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def FileDelete(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/fileservice.Fileservice/FileDelete',
            fileService__pb2.FileInfo.SerializeToString,
            fileService__pb2.ack.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def UpdateFile(request_iterator,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.stream_unary(
            request_iterator,
            target,
            '/fileservice.Fileservice/UpdateFile',
            fileService__pb2.FileData.SerializeToString,
            fileService__pb2.ack.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def getClusterStats(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/fileservice.Fileservice/getClusterStats',
            fileService__pb2.Empty.SerializeToString,
            fileService__pb2.ClusterStats.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def getLeaderInfo(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/fileservice.Fileservice/getLeaderInfo',
            fileService__pb2.ClusterInfo.SerializeToString,
            fileService__pb2.ack.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def MetaDataInfo(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/fileservice.Fileservice/MetaDataInfo',
            fileService__pb2.MetaData.SerializeToString,
            fileService__pb2.ack.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)
