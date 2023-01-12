"""Recordings API Handler."""
from __future__ import annotations

import logging

import voluptuous as vol

from viseron.components.webserver.api import BaseAPIHandler
from viseron.components.webserver.const import (
    STATUS_ERROR_ENDPOINT_NOT_FOUND,
    STATUS_ERROR_INTERNAL,
)
from viseron.helpers.validators import request_argument_no_value

LOGGER = logging.getLogger(__name__)

LATEST_DAILY_GROUP = "latest_daily"
LATEST_DAILY_MSG = "'daily' must be used together with 'latest'"


class RecordingsAPIHandler(BaseAPIHandler):
    """Handler for API calls related to recordings."""

    routes = [
        {
            "path_pattern": (r"/recordings"),
            "supported_methods": ["GET"],
            "method": "get_recordings",
            "request_arguments_schema": vol.Schema(
                vol.Any(
                    {
                        vol.Inclusive(
                            "latest",
                            LATEST_DAILY_GROUP,
                            default=False,
                            msg=LATEST_DAILY_MSG,
                        ): request_argument_no_value,
                        vol.Inclusive(
                            "daily",
                            LATEST_DAILY_GROUP,
                            default=False,
                            msg=LATEST_DAILY_MSG,
                        ): request_argument_no_value,
                    },
                    {
                        vol.Optional(
                            "latest", default=False
                        ): request_argument_no_value,
                    },
                ),
            ),
        },
        {
            "path_pattern": (
                r"/recordings/(?P<camera_identifier>[A-Za-z0-9_]+)"
                r"/(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})"
            ),
            "supported_methods": ["GET"],
            "method": "get_recordings_camera",
            "request_arguments_schema": vol.Schema(
                {
                    vol.Optional("latest", default=False): request_argument_no_value,
                },
            ),
        },
        {
            "path_pattern": (r"/recordings/(?P<camera_identifier>[A-Za-z0-9_]+)"),
            "supported_methods": ["GET"],
            "method": "get_recordings_camera",
            "request_arguments_schema": vol.Schema(
                vol.Any(
                    {
                        vol.Inclusive(
                            "latest",
                            LATEST_DAILY_GROUP,
                            default=False,
                            msg=LATEST_DAILY_MSG,
                        ): request_argument_no_value,
                        vol.Inclusive(
                            "daily",
                            LATEST_DAILY_GROUP,
                            default=False,
                            msg=LATEST_DAILY_MSG,
                        ): request_argument_no_value,
                    },
                    {
                        vol.Optional(
                            "latest", default=False
                        ): request_argument_no_value,
                    },
                ),
            ),
        },
        {
            "path_pattern": (
                r"/recordings/(?P<camera_identifier>[A-Za-z0-9_]+)"
                r"/(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})"
                r"/(?P<filename>.*\..*)"
            ),
            "supported_methods": ["DELETE"],
            "method": "delete_recording",
        },
        {
            "path_pattern": (
                r"/recordings/(?P<camera_identifier>[A-Za-z0-9_]+)"
                r"/(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})"
            ),
            "supported_methods": ["DELETE"],
            "method": "delete_recording",
        },
        {
            "path_pattern": (r"/recordings/(?P<camera_identifier>[A-Za-z0-9_]+)"),
            "supported_methods": ["DELETE"],
            "method": "delete_recording",
        },
    ]

    def get_recordings(self):
        """Get recordings for all cameras."""
        cameras = self._get_cameras()

        if not cameras:
            self.response_error(
                STATUS_ERROR_ENDPOINT_NOT_FOUND,
                reason="No cameras found",
            )
            return

        recordings = {}
        for camera in cameras.values():
            if self.request_arguments["latest"] and self.request_arguments.get(
                "daily", False
            ):
                recordings[
                    camera.identifier
                ] = camera.recorder.get_latest_recording_daily()
                continue
            if self.request_arguments["latest"]:
                recordings[camera.identifier] = camera.recorder.get_latest_recording()
                continue
            recordings[camera.identifier] = camera.recorder.get_recordings()

        self.response_success(recordings)
        return

    def get_recordings_camera(self, camera_identifier: str, date: str = None):
        """Get recordings for a single camera."""
        camera = self._get_camera(camera_identifier)

        if not camera:
            self.response_error(
                STATUS_ERROR_ENDPOINT_NOT_FOUND,
                reason=f"Camera {camera_identifier} not found",
            )
            return

        if self.request_arguments["latest"] and self.request_arguments.get(
            "daily", False
        ):
            self.response_success(camera.recorder.get_latest_recording_daily())
            return

        if self.request_arguments["latest"]:
            self.response_success(camera.recorder.get_latest_recording(date))
            return

        self.response_success(camera.recorder.get_recordings(date))
        return

    def delete_recording(
        self, camera_identifier: str, date: str = None, filename: str = None
    ):
        """Delete recording(s)."""
        camera = self._get_camera(camera_identifier)

        if not camera:
            self.response_error(
                STATUS_ERROR_ENDPOINT_NOT_FOUND,
                reason=f"Camera {camera_identifier} not found",
            )
            return

        # Try to delete recording
        if camera.recorder.delete_recording(date, filename):
            self.response_success()
            return
        self.response_error(
            STATUS_ERROR_INTERNAL,
            reason=(f"Failed to delete recording. Date={date} filename={filename}"),
        )
        return
