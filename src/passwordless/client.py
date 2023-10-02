from requests import Request, Response, Session
from typing import List
from abc import ABC, abstractmethod
import logging

from .config import PasswordlessOptions
from .errors import PasswordlessProblemDetails, PasswordlessError
from .models import ListResponse, CreateAlias, Alias, UpdateAppsFeature, DeleteCredential, Credential, \
    RegisterToken, RegisteredToken, VerifiedUser, VerifySignIn, DeleteUser, UserSummary
from .serialization import PasswordlessProblemDetailsSchema, UserSummaryListResponseSchema, \
    CreateAliasSchema, AliasListResponseSchema, UpdateAppsFeatureSchema, DeleteCredentialSchema, \
    CredentialListResponseSchema, RegisterTokenSchema, RegisteredTokenSchema, VerifySignInSchema, \
    VerifiedUserSchema, DeleteUserSchema


class PasswordlessApiClient:

    @abstractmethod
    def create_alias(self, create_alias: CreateAlias) -> None:
        pass

    @abstractmethod
    def get_aliases(self, user_id: str) -> List[Alias]:
        pass

    @abstractmethod
    def update_apps_feature(self, update_apps_feature: UpdateAppsFeature) -> None:
        pass

    @abstractmethod
    def delete_credential(self, delete_credential: DeleteCredential) -> None:
        pass

    @abstractmethod
    def get_credentials(self, user_id: str) -> List[Credential]:
        pass

    @abstractmethod
    def register_token(self, register_token: RegisterToken) -> RegisteredToken:
        pass

    @abstractmethod
    def sign_in(self, verify_sign_in: VerifySignIn) -> VerifiedUser:
        pass

    @abstractmethod
    def get_users(self) -> List[UserSummary]:
        pass

    @abstractmethod
    def delete_user(self, delete_user: DeleteUser) -> None:
        pass


def handle_response_error(response: Response):
    problem_details = None
    if 'Content-Type' in response.headers and response.headers['Content-Type'].startswith(
            'application/problem+json'):
        problem_details_schema = PasswordlessProblemDetailsSchema()
        problem_details = problem_details_schema.loads(response.text)

    if problem_details is None:
        logging.debug("Problem details fallback")

        problem_details = PasswordlessProblemDetails(
            type='https://docs.passwordless.dev/guide/errors.html',
            status=response.status_code,
            title='Unexpected error',
            detail=response.text)

    logging.debug("Problem details %s", problem_details)

    raise PasswordlessError(problem_details)


class PasswordlessApiClientImpl(PasswordlessApiClient, ABC):

    def __init__(self, options: PasswordlessOptions, session: Session):
        self.options = options
        self.session = session

    def create_alias(self, create_alias: CreateAlias) -> None:
        schema = CreateAliasSchema()
        request_data = schema.dumps(create_alias)

        request = self.post_request('/alias', request_data)

        self.send_request(request)

    def get_aliases(self, user_id: str) -> List[Alias]:
        request = self.get_request('/alias/list', {"userId": user_id})
        response_data = self.send_request(request)

        schema = AliasListResponseSchema()
        list_response: ListResponse = schema.loads(response_data)

        return list_response.values

    def update_apps_feature(self, update_apps_feature: UpdateAppsFeature) -> None:
        schema = UpdateAppsFeatureSchema()
        request_data = schema.dumps(update_apps_feature)

        request = self.post_request('/apps/features', request_data)

        self.send_request(request)

    def delete_credential(self, delete_credential: DeleteCredential) -> None:
        schema = DeleteCredentialSchema()
        request_data = schema.dumps(delete_credential)

        request = self.post_request('/credentials/delete', request_data)

        self.send_request(request)

    def get_credentials(self, user_id: str) -> List[Credential]:
        request = self.get_request('/credentials/list', {"userId": user_id})
        response_data = self.send_request(request)

        schema = CredentialListResponseSchema()
        list_response: ListResponse = schema.loads(response_data)

        return list_response.values

    def register_token(self, register_token: RegisterToken) -> RegisteredToken:
        request_schema = RegisterTokenSchema()
        request_data = request_schema.dumps(register_token)

        request = self.post_request('/register/token', request_data)

        response_data = self.send_request(request)

        response_schema = RegisteredTokenSchema()
        return response_schema.loads(response_data)

    def sign_in(self, verify_sign_in: VerifySignIn) -> VerifiedUser:
        request_schema = VerifySignInSchema()
        request_data = request_schema.dumps(verify_sign_in)

        request = self.post_request('/signin/verify', request_data)

        response_data = self.send_request(request)

        response_schema = VerifiedUserSchema()
        return response_schema.loads(response_data)

    def get_users(self) -> List[UserSummary]:
        request = self.get_request('/users/list')
        response_data = self.send_request(request)

        schema = UserSummaryListResponseSchema()
        list_response: ListResponse = schema.loads(response_data)

        return list_response.values

    def delete_user(self, delete_user: DeleteUser) -> None:
        schema = DeleteUserSchema()
        request_data = schema.dumps(delete_user)

        request = self.post_request('/users/delete', request_data)

        self.send_request(request)

    def get_request(self, path: str, query_params=None) -> Request:
        if query_params is None:
            query_params = {}

        url = self.build_url(path)
        headers = self.build_headers()

        return Request(method='GET', url=url, headers=headers, params=query_params)

    def post_request(self, path: str, data: str) -> Request:
        url = self.build_url(path)
        headers = self.build_headers(post=True)

        return Request(method='POST', url=url, headers=headers, data=data)

    def send_request(self, request: Request) -> str:

        logging.debug('Sending request method %s url %s headers %s params %s data %s',
                      request.method, request.url, request.headers, request.params, request.data)

        prepped_request = self.session.prepare_request(request)

        response = self.session.send(prepped_request, allow_redirects=True, timeout=30)

        logging.debug('Response code %s headers %s data %s',
                      response.status_code, response.headers, response.text)

        if response.status_code >= 400:
            handle_response_error(response)

        return response.text

    def build_url(self, path: str):
        return self.options.api_url + path

    def build_headers(self, post: bool = False):
        headers = {
            'ApiSecret': self.options.api_secret
        }
        if post:
            headers['Content-Type'] = 'application/json; charset=UTF-8'
        return headers


class PasswordlessApiClientBuilder:

    def __init__(self, options: PasswordlessOptions, session: Session = None):
        self.options = options
        if session is None:
            session = Session()
        self.session = session

    def build(self) -> PasswordlessApiClient:
        return PasswordlessApiClientImpl(self.options, self.session)

# def handle_response(response):
#     if response.status_code >= 200 and response.status_code < 300:
#         return response.json()
#     else:
#         raise PasswordlessError(response.json()['message'])
