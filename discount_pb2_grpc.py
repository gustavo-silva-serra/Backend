# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import discount_pb2 as discount__pb2


class DiscountStub(object):
    """Service that return mocked discount percentage.
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.GetDiscount = channel.unary_unary(
                '/discount.Discount/GetDiscount',
                request_serializer=discount__pb2.GetDiscountRequest.SerializeToString,
                response_deserializer=discount__pb2.GetDiscountResponse.FromString,
                )


class DiscountServicer(object):
    """Service that return mocked discount percentage.
    """

    def GetDiscount(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_DiscountServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'GetDiscount': grpc.unary_unary_rpc_method_handler(
                    servicer.GetDiscount,
                    request_deserializer=discount__pb2.GetDiscountRequest.FromString,
                    response_serializer=discount__pb2.GetDiscountResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'discount.Discount', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Discount(object):
    """Service that return mocked discount percentage.
    """

    @staticmethod
    def GetDiscount(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/discount.Discount/GetDiscount',
            discount__pb2.GetDiscountRequest.SerializeToString,
            discount__pb2.GetDiscountResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)