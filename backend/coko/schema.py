"""GraphQL schema for Coko project."""

import graphene
from graphql_jwt.decorators import login_required

# Import schemas from each service when they are created
# from auth_service.schema import AuthQuery, AuthMutation
# from catalog_service.schema import CatalogQuery, CatalogMutation
# from reading_service.schema import ReadingQuery, ReadingMutation
# from recommendation_service.schema import RecommendationQuery


class Query(graphene.ObjectType):
    """Root Query for GraphQL API."""
    
    # Health check query
    health = graphene.String()
    
    def resolve_health(self, info):
        """Simple health check for GraphQL endpoint."""
        return "GraphQL endpoint is healthy"
    
    # Add service queries here when schemas are implemented
    # auth = graphene.Field(AuthQuery)
    # catalog = graphene.Field(CatalogQuery)
    # reading = graphene.Field(ReadingQuery)
    # recommendations = graphene.Field(RecommendationQuery)


class Mutation(graphene.ObjectType):
    """Root Mutation for GraphQL API."""
    
    # Add service mutations here when schemas are implemented
    # auth = graphene.Field(AuthMutation)
    # catalog = graphene.Field(CatalogMutation)
    # reading = graphene.Field(ReadingMutation)
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)