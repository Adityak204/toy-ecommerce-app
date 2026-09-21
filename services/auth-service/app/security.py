import os
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext


JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "RS256")
JWT_KID = os.getenv("JWT_KID", "auth-key-1")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

PRIVATE_KEY_PATH = os.getenv("PRIVATE_KEY_PATH", "/app/keys/private_key.pem") # ./keys/private_key.pem
PUBLIC_KEY_PATH = os.getenv("PUBLIC_KEY_PATH", "/app/keys/public_key.pem") # ./keys/public_key.pem

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash the given password."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify the given password matches the hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def _read_key(path: str) -> str:
    with open(path, "r") as key_file:
        return key_file.read()


def create_access_token(subject:str) -> str:
    """Sign a JWT for the given subject (user email) with the private key."""
    private_key = _read_key(PRIVATE_KEY_PATH)
    expire = datetime.now(tz=timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    claims = {"sub": subject, "exp": expire}
    return jwt.encode(claims, private_key, algorithm=JWT_ALGORITHM, headers={"kid": JWT_KID})


def get_jwks() -> dict:
    """Build the JWKS response from the public key."""
    public_key = _read_key(PUBLIC_KEY_PATH)
    jwt_dict = jwt.construct(public_key, JWT_ALGORITHM).to_dict()
    jwt_dict["kid"] = JWT_KID
    jwt_dict["use"] = "sig"
    jwt_dict["alg"] = JWT_ALGORITHM
    return jwt_dict


# if __name__ == "__main__":
#     print(create_access_token("test@example.com"))