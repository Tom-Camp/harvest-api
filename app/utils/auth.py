from fastapi_users.authentication import BearerTransport

from app.utils.config import settings

# from app.models.users import AccessToken

SECRET = settings.user_secret

bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


# async def get_access_token_db(session: AsyncSession = Depends(get_async_session)):
#     yield SQLAlchemyAccessTokenDatabase(session, AccessToken)
#
#
# def get_database_strategy(
#     access_token_db: AccessTokenDatabase[AccessToken] = Depends(get_access_token_db),
# ) -> DatabaseStrategy:
#     return DatabaseStrategy(access_token_db, lifetime_seconds=3600)
#
#
# def get_jwt_strategy() -> JWTStrategy:
#     return JWTStrategy(secret=SECRET, lifetime_seconds=3600)
#
#
# auth_backend = AuthenticationBackend(
#     name="jwt",
#     transport=bearer_transport,
#     get_strategy=get_jwt_strategy,
# )
