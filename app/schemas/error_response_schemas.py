# -----------------------------------
# COMMON RESPONSE SCHEMAS
# -----------------------------------
standard_responses = {
    200: {"description": "Request successful"},
    201: {"description": "Resource created successfully"},
    400: {"description": "Bad request – invalid input or missing fields"},
    401: {"description": "Unauthorized – invalid or missing authentication"},
    403: {"description": "Forbidden – insufficient permissions"},
    404: {"description": "Resource not found"},
    409: {"description": "Conflict – resource already exists"},
    422: {"description": "Validation error – incorrect data format"},
    500: {"description": "Internal server error"},
}
