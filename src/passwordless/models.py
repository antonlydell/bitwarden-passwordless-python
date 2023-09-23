from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, TypeVar, Optional

T = TypeVar("T")


@dataclass
class CreateAlias:
    user_id: str
    aliases: List[str]
    hashing: bool = True


@dataclass
class Alias:
    user_id: str
    alias: str
    plaintext: str
    tenant: str


@dataclass
class ListResponse:
    values: List[T]


@dataclass
class UpdateAppsFeature:
    audit_logging_retention_period: int


@dataclass
class DeleteCredential:
    credential_id: str


@dataclass
class CredentialDescriptor:
    type: str
    """
    Base64 encoded credential descriptor id.
    """
    id: str
    transports: Optional[List[str]] = None


@dataclass
class Credential:
    descriptor: CredentialDescriptor
    """
    Base64 encoded public key.
    """
    public_key: str
    """
    Base64 encoded user handle.
    """
    user_handle: str
    signature_counter: int
    attestation_fmt: str
    created_at: datetime
    aa_guid: str
    last_user_at: datetime
    rp_id: str
    origin: str
    country: str
    device: str
    user_id: str


@dataclass
class RegisterToken:
    user_id: str
    username: str
    display_name: str
    attestation: str = 'none'
    authenticator_type: str = 'any'
    discoverable: bool = True
    user_verification: str = 'preferred'
    aliases: List[str] = field(default_factory=list)
    alias_hashing: bool = True
    expires_at: datetime = datetime.utcnow() + timedelta(minutes=2)


@dataclass
class RegisteredToken:
    token: str


@dataclass
class VerifySignIn:
    token: str


@dataclass
class VerifiedUser:
    success: bool
    user_id: str
    timestamp: datetime
    rp_id: str
    origin: str
    device: str
    country: str
    nickname: str
    """
    Base64 encoded credential id.
    """
    credential_id: str
    expires_at: datetime
    token_id: str
    type: str


@dataclass
class UserSummary:
    user_id: str
    alias_count: int
    aliases: List[str]
    credentials_count: int
    last_used_at: datetime


@dataclass
class DeleteUser:
    user_id: str
