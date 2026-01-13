"""
Module for climatization for audi vehicles.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from carconnectivity.attributes import BooleanAttribute, DateAttribute, GenericAttribute
from carconnectivity.climatization import Climatization
from carconnectivity.objects import GenericObject
from carconnectivity.units import Temperature
from carconnectivity.vehicle import GenericVehicle

if TYPE_CHECKING:
    from typing import Optional


class AudiClimatization(Climatization):  # pylint: disable=too-many-instance-attributes
    """
    AudiClimatization class for handling Audi vehicle climatization information.

    This class extends the Climatization class and includes an enumeration of various
    climatization states specific to Audi vehicles.
    """

    def __init__(
        self,
        vehicle: GenericVehicle | None = None,
        origin: Optional[Climatization] = None,
        initialization: Optional[dict] = None,
    ) -> None:
        if origin is not None:
            super().__init__(origin=origin, initialization=initialization)
            if not isinstance(self.settings, AudiClimatization.Settings):
                self.settings: Climatization.Settings = AudiClimatization.Settings(parent=self, origin=origin.settings)
            # Add timer support
            if hasattr(origin, "timers"):
                self.timers: AudiClimatization.Timers = origin.timers
                self.timers.parent = self
            else:
                self.timers: AudiClimatization.Timers = AudiClimatization.Timers(
                    parent=self, initialization=self.get_initialization("timers")
                )
        else:
            super().__init__(vehicle=vehicle, initialization=initialization)
            self.settings: Climatization.Settings = AudiClimatization.Settings(
                parent=self, initialization=self.get_initialization("settings")
            )
            self.timers: AudiClimatization.Timers = AudiClimatization.Timers(
                parent=self, initialization=self.get_initialization("timers")
            )

    class Settings(Climatization.Settings):
        """
        This class represents the settings for an audi car climatization.
        """

        def __init__(
            self,
            parent: Optional[GenericObject] = None,
            origin: Optional[Climatization.Settings] = None,
            initialization: Optional[dict] = None,
        ) -> None:
            if origin is not None:
                super().__init__(parent=parent, origin=origin, initialization=initialization)
            else:
                super().__init__(parent=parent, initialization=initialization)
            self.unit_in_car: Optional[Temperature] = None
            self.front_zone_left_enabled: BooleanAttribute = BooleanAttribute(
                parent=self,
                name="front_zone_left_enabled",
                tags={"connector_custom"},
                initialization=self.get_initialization("front_zone_left_enabled"),
            )
            self.front_zone_right_enabled: BooleanAttribute = BooleanAttribute(
                parent=self,
                name="front_zone_right_enabled",
                tags={"connector_custom"},
                initialization=self.get_initialization("front_zone_right_enabled"),
            )
            self.rear_zone_left_enabled: BooleanAttribute = BooleanAttribute(
                parent=self,
                name="rear_zone_left_enabled",
                tags={"connector_custom"},
                initialization=self.get_initialization("rear_zone_left_enabled"),
            )
            self.rear_zone_right_enabled: BooleanAttribute = BooleanAttribute(
                parent=self,
                name="rear_zone_right_enabled",
                tags={"connector_custom"},
                initialization=self.get_initialization("rear_zone_right_enabled"),
            )

    class Timers(GenericObject):
        """
        This class represents the timers for Audi car climatization.
        """

        def __init__(self, parent: Optional[GenericObject] = None, initialization: Optional[dict] = None) -> None:
            super().__init__(object_id="timers", parent=parent, initialization=initialization)

            # Raw timer data from API - will be updated with actual timer list
            self.raw_data = GenericAttribute(
                "raw_data", self, value=None, tags={"connector_custom"}, initialization=self.get_initialization("raw_data")
            )

            # Individual timer objects will be created dynamically based on API response
            # Example: self.timer_1, self.timer_2, etc.

        def update_timers(self, timers_data: list, captured_at) -> None:
            """Update timer data from API response"""
            # Store raw data
            self.raw_data._set_value(value=timers_data, measured=captured_at)

            # Clear existing timer attributes
            existing_timers = [attr for attr in dir(self) if attr.startswith("timer_") and not attr.startswith("_")]
            for timer_attr in existing_timers:
                delattr(self, timer_attr)

            # Create individual timer objects
            for timer in timers_data:
                if "id" in timer:
                    timer_id = timer["id"]
                    timer_attr_name = f"timer_{timer_id}"

                    # Create a GenericObject for this timer
                    timer_obj = GenericObject(object_id=timer_attr_name, parent=self)

                    # Add timer properties
                    timer_obj.timer_id = GenericAttribute("id", timer_obj, value=timer_id, tags={"connector_custom"})
                    timer_obj.enabled = BooleanAttribute(
                        "enabled", timer_obj, value=timer.get("enabled", False), tags={"connector_custom"}
                    )

                    if "singleTimer" in timer:
                        single_timer = timer["singleTimer"]
                        if "startDateTimeLocal" in single_timer:
                            timer_obj.start_datetime = DateAttribute("start_datetime", timer_obj, tags={"connector_custom"})
                            # Parse the datetime string to a proper datetime object
                            from datetime import datetime

                            try:
                                start_dt = datetime.fromisoformat(single_timer["startDateTimeLocal"])
                                timer_obj.start_datetime._set_value(value=start_dt, measured=captured_at)
                            except (ValueError, TypeError):
                                timer_obj.start_datetime._set_value(
                                    value=single_timer["startDateTimeLocal"], measured=captured_at
                                )

                        if "targetDateTimeLocal" in single_timer:
                            timer_obj.target_datetime = DateAttribute("target_datetime", timer_obj, tags={"connector_custom"})
                            try:
                                target_dt = datetime.fromisoformat(single_timer["targetDateTimeLocal"])
                                timer_obj.target_datetime._set_value(value=target_dt, measured=captured_at)
                            except (ValueError, TypeError):
                                timer_obj.target_datetime._set_value(
                                    value=single_timer["targetDateTimeLocal"], measured=captured_at
                                )

                    # Set the timer object as an attribute of this Timers object
                    setattr(self, timer_attr_name, timer_obj)
