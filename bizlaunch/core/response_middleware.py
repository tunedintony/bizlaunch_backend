import copy
import json

from typing import Any, Dict, Optional

from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.response import Response
from urllib.parse import parse_qs, urlparse


class ApiResponseMiddleware(MiddlewareMixin):
    """
    Middleware to standardize API responses across the application.

    Standard Response Format:
    {
        "status": 200,
        "success": true,
        "message": "Success",
        "data": { ... }
    }

    Paginated Response Format:
    {
        "status": 200,
        "success": true,
        "message": "Success",
        "data": [...],
        "pagination": {
            "count": 100,
            "page_size": 5,
            "current_page": 1,
            "next": "...",
            "previous": "..."
        }
    }

    Error Response Format:
    {
        "status": 400,
        "success": false,
        "message": "error message here",
        "data": { ... }  # Original error data
    }
    """

    def __init__(self, get_response):
        super().__init__(get_response)
        # Define standard response keys
        self.default_response_keys = {
            "status",
            "success",
            "message",
            "data",
            "pagination",
            "detail",
            "non_field_errors",
        }
        # Define paths that should be skipped
        self.skip_paths = ("/swagger", "/redoc", "/admin", "/static", "/media")
        # Standard status messages
        self.status_messages = {
            200: _("Success"),
            201: _("Created Successfully"),
            204: _("Deleted Successfully"),
            400: _("Bad Request"),
            401: _("Unauthorized"),
            403: _("Permission Denied"),
            404: _("Not Found"),
            405: _("Method Not Allowed"),
            500: _("Internal Server Error"),
        }

    def should_process_response(self, request) -> bool:
        """
        Determine if the response should be processed based on the request path.
        Returns:
            bool: True if response should be processed, False otherwise
        """
        # Get the base path without query parameters
        path = request.path_info.lower().split("?")[0].rstrip("/")

        # Skip if not an API request
        if not path.startswith("/api"):
            return False

        # Skip documentation and other excluded paths
        if any(path.startswith(skip_path.lower().rstrip("/")) for skip_path in self.skip_paths):
            return False

        return True

    def get_default_message(self, status_code: int) -> str:
        """
        Get default message for status code.
        Args:
            status_code (int): HTTP status code
        Returns:
            str: Default message for the status code
        """
        return self.status_messages.get(status_code, _("Unknown Status"))

    def _format_error_message(self, response_data: dict) -> str:
        """
        Format error messages from various error types into a standardized format.
        Args:
            response_data (Dict): The error response data
        Returns:
            str: Formatted error message
        """
        if isinstance(response_data, str):
            return response_data

        if isinstance(response_data, dict):
            error_messages = []

            # Handle non_field_errors
            if "non_field_errors" in response_data:
                error_messages.extend(response_data["non_field_errors"])

            # Handle 'detail' error
            if "detail" in response_data:
                error_messages.append(str(response_data["detail"]))

            # Handle field-specific errors
            for key, value in response_data.items():
                if key not in self.default_response_keys:
                    if isinstance(value, list):
                        error_messages.append(f"{key}: {' '.join(str(v) for v in value)}")
                    else:
                        error_messages.append(f"{key}: {str(value)}")

            return " | ".join(error_messages) if error_messages else _("An error occurred")

        return str(response_data)

    def _handle_pagination(self, response_data: dict, request) -> dict:
        """
        Handle pagination data and return standardized format.
        Args:
            response_data (Dict): The response data containing pagination
            request: The request object to get current page from query params
        Returns:
            Dict: Standardized pagination data
        """
        # Get current page from query params
        query_params = parse_qs(urlparse(request.get_full_path()).query)
        current_page = int(query_params.get('page', [1])[0])

        return {
            "data": response_data.get("results", []),
            "pagination": {
                "count": response_data.get("count", 0),
                "page_size": response_data.get("page_size", len(response_data.get("results", []))),
                "current_page": current_page,
                "next": response_data.get("next"),
                "previous": response_data.get("previous"),
            },
        }

    def _create_response(
        self, status_code: int, success: bool, message: str = None, data: Any = None, pagination: Optional[Dict] = None
    ) -> Dict:
        """
        Create standardized response dictionary.
        Args:
            status_code (int): HTTP status code
            success (bool): Success status
            message (str, optional): Response message
            data (Any, optional): Response data
            pagination (Dict, optional): Pagination information
        Returns:
            Dict: Standardized response dictionary
        """
        response = {
            "status": status_code,
            "success": success,
            "message": message or self.get_default_message(status_code),
            "data": data if data is not None else {},
        }

        if pagination:
            response["pagination"] = pagination

        return response

    def process_response(self, request, response):
        """
        Process and standardize the response.
        Args:
            request: The request object
            response: The response object
        Returns:
            Response: Processed response object
        """
        # Check if response should be processed
        if not self.should_process_response(request):
            return response

        # Skip processing for non-Response objects
        if not hasattr(response, "data") and not hasattr(response, "results"):
            return response

        try:
            # Create a deep copy of the response data to prevent modifications
            response_data = copy.deepcopy(response.data) if hasattr(response, "data") else {}
            status_code = response.status_code

            # Handle successful responses
            if status_code < 400:
                # Check for pagination
                if isinstance(response_data, dict) and all(key in response_data for key in ["count", "results"]):
                    pagination_data = self._handle_pagination(response_data, request)
                    standardized_response = self._create_response(
                        status_code=status_code,
                        success=True,
                        message=self.get_default_message(status_code),
                        data=pagination_data["data"],
                        pagination=pagination_data["pagination"],
                    )
                else:
                    standardized_response = self._create_response(
                        status_code=status_code,
                        success=True,
                        message=self.get_default_message(status_code),
                        data=response_data,
                    )

            # Handle error responses
            else:
                error_message = self._format_error_message(response_data)
                standardized_response = self._create_response(
                    status_code=status_code,
                    success=False,
                    message=error_message,
                    data=response_data if isinstance(response_data, dict) else None,
                )

            # Update response
            response.data = standardized_response
            response.content = json.dumps(standardized_response, cls=DjangoJSONEncoder)

            # Maintain original status code
            response.status_code = status_code

            return response

        except Exception as e:
            # If any error occurs during processing, return original response
            return response
