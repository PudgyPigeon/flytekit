import logging
import typing
from collections import namedtuple

import grpc

from flytekit.clients.auth.authenticator import Authenticator


class _ClientCallDetails(
    namedtuple("_ClientCallDetails", ("method", "timeout", "metadata", "credentials")),
    grpc.ClientCallDetails,
):
    """
    Wrapper class for initializing a new ClientCallDetails instance.
    We cannot make this of type - NamedTuple because, NamedTuple has a metaclass of type NamedTupleMeta and both
    the metaclasses conflict
    """

    pass


class AuthUnaryInterceptor(grpc.UnaryUnaryClientInterceptor, grpc.UnaryStreamClientInterceptor):
    """
    This Interceptor can be used to automatically add Auth Metadata for every call - lazily in case authentication
    is needed.
    """

    def __init__(self, authenticator: Authenticator):
        self._authenticator = authenticator

    def _call_details_with_auth_metadata(self, client_call_details: grpc.ClientCallDetails) -> grpc.ClientCallDetails:
        """
        Returns new ClientCallDetails with metadata added.
        """
        metadata = None
        logging.warning("METADATA IS NONE - THIS IS CALL DETAILS WITH AUTH METADATA")
        auth_metadata = self._authenticator.fetch_grpc_call_auth_metadata()
        logging.warning(auth_metadata)
        if auth_metadata:
            metadata = []
            logging.warning("THIS IS BEFORE EXTENDING METADATA")
            logging.warning(client_call_details.metadata)
            if client_call_details.metadata:
                logging.warning("THIS IS CLIENTCALLDETAILS.METADATA")
                logging.warning(client_call_details)
                metadata.extend(list(client_call_details.metadata))
            metadata.append(auth_metadata)
        logging.warning(metadata)
        return _ClientCallDetails(
            client_call_details.method,
            client_call_details.timeout,
            metadata,
            client_call_details.credentials,
        )

    def intercept_unary_unary(
        self,
        continuation: typing.Callable,
        client_call_details: grpc.ClientCallDetails,
        request: typing.Any,
    ):
        """
        Intercepts unary calls and adds auth metadata if available. On Unauthenticated, resets the token and refreshes
        and then retries with the new token
        """
        updated_call_details = self._call_details_with_auth_metadata(client_call_details)
        fut: grpc.Future = continuation(updated_call_details, request)
        e = fut.exception()
        if e:
            if e.code() == grpc.StatusCode.UNAUTHENTICATED:
                logging.warning("CALLING FROM INTERCEPT UNARY UNARY")
                self._authenticator.refresh_credentials()
                updated_call_details = self._call_details_with_auth_metadata(client_call_details)
                logging.warning("AFTER UPDATE CALLING DETAILS")
                return continuation(updated_call_details, request)
        return fut

    def intercept_unary_stream(self, continuation, client_call_details, request):
        """
        Handles a stream call and adds authentication metadata if needed
        """
        updated_call_details = self._call_details_with_auth_metadata(client_call_details)
        c: grpc.Call = continuation(updated_call_details, request)
        if c.code() == grpc.StatusCode.UNAUTHENTICATED:
            self._authenticator.refresh_credentials()
            updated_call_details = self._call_details_with_auth_metadata(client_call_details)
            return continuation(updated_call_details, request)
        return c
