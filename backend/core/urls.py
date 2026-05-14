from django.urls import path
from . import endpoints


urlpatterns = [
    # meta
    path("api/meta/ping/", endpoints.meta.ping, name="api-ping"),
    path("api/meta/tags/", endpoints.meta.tags_json, name="tags-json"),

    # rekomendacje
    path("api/recommendations/", endpoints.recommendations.recommendations_json, name="api-recommendations"),
    path("api/recommendations/default", endpoints.default_recommendations.get_default_recommendations, name ="api-default-recommendations"),

    # auth
    path("api/auth/token/", endpoints.authentication.generate_token, name="generate-token"),
    path("api/auth/token/refresh/", endpoints.authentication.token_refresh, name="token-refresh"),
    path("api/auth/logout/", endpoints.authentication.logout, name="logout"),

    # admin dashboard
    path("api/admin/me/", endpoints.admin_dashboard.me, name="me"),
    path("api/admin/tables/", endpoints.admin_dashboard.get_tables, name="get-tables"),
    path("api/admin/tables/data/", endpoints.admin_dashboard.get_table_data, name="get-table-data"),
    path("api/admin/tables/modify/", endpoints.admin_dashboard.modify_table_data, name="modify-table-data"),
    path("api/admin/film-tags/", endpoints.admin_dashboard.film_tags, name="film-tags"),
]