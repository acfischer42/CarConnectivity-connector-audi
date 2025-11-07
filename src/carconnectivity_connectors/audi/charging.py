"""
Module for charging for Audi vehicles.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from carconnectivity.attributes import BooleanAttribute, EnumAttribute, GenericAttribute, StringAttribute
from carconnectivity.charging import Charging
from carconnectivity.objects import GenericObject
from carconnectivity.vehicle import ElectricVehicle

if TYPE_CHECKING:
    from typing import Dict, Optional


class AudiCharging(Charging):  # pylint: disable=too-many-instance-attributes
    """
    AudiCharging class for handling Audi vehicle charging information.

    This class extends the Charging class and includes an enumeration of various
    charging states specific to Audi vehicles.
    """

    def __init__(self, vehicle: ElectricVehicle | None = None, origin: Optional[Charging] = None) -> None:
        if origin is not None:
            super().__init__(vehicle=vehicle, origin=origin)
            self.settings = AudiCharging.Settings(parent=self, origin=origin.settings)
            # preserve timers if origin contained them
            if hasattr(origin, "timers"):
                self.timers = origin.timers
                self.timers.parent = self
            else:
                self.timers = AudiCharging.Timers(parent=self)
        else:
            super().__init__(vehicle=vehicle)
            self.settings = AudiCharging.Settings(parent=self, origin=self.settings)
            self.timers = AudiCharging.Timers(parent=self)

        # Charge mode attribute (connector_custom)
        self.charge_mode: EnumAttribute = EnumAttribute("charge_mode", parent=self, tags={"connector_custom"})

    class Settings(Charging.Settings):
        """
        This class represents the settings for audi car charging.
        """

        def __init__(self, parent: Optional[GenericObject] = None, origin: Optional[Charging.Settings] = None) -> None:
            if origin is not None:
                super().__init__(parent=parent, origin=origin)
            else:
                super().__init__(parent=parent)
            self.max_current_in_ampere: Optional[bool] = None
            # Preferred charge mode and available modes (connector_custom)
            self.preferred_charge_mode: EnumAttribute = EnumAttribute(
                "preferred_charge_mode", parent=self, tags={"connector_custom"}
            )
            self.available_charge_modes: StringAttribute = StringAttribute(
                "available_charge_modes", parent=self, tags={"connector_custom"}
            )

    class AudiChargingState(
        Enum,
    ):
        """
        Enum representing the various charging states for an Audi vehicle.
        """

        OFF = "off"
        READY_FOR_CHARGING = "readyForCharging"
        NOT_READY_FOR_CHARGING = "notReadyForCharging"
        CONSERVATION = "conservation"
        CHARGE_PURPOSE_REACHED_NOT_CONSERVATION_CHARGING = "chargePurposeReachedAndNotConservationCharging"
        CHARGE_PURPOSE_REACHED_CONSERVATION = "chargePurposeReachedAndConservation"
        CHARGING = "charging"
        ERROR = "error"
        UNSUPPORTED = "unsupported"
        DISCHARGING = "discharging"
        UNKNOWN = "unknown charging state"

    class AudiChargeMode(
        Enum,
    ):
        """
        Enum class representing different Audi charge modes.
        """

        MANUAL = "manual"
        INVALID = "invalid"
        OFF = "off"
        TIMER = "timer"
        ONLY_OWN_CURRENT = "onlyOwnCurrent"
        PREFERRED_CHARGING_TIMES = "preferredChargingTimes"
        UNKNOWN = "unknown"
        TIMER_CHARGING_WITH_CLIMATISATION = "timerChargingWithClimatisation"
        HOME_STORAGE_CHARGING = "homeStorageCharging"
        IMMEDIATE_DISCHARGING = "immediateDischarging"

    class Timers(GenericObject):
        """
        Timers container for charging timers.

        Creates per-timer GenericObject children (timer_{id}) with accessible attributes.
        """

        def __init__(self, parent: Optional[GenericObject] = None, debug_mode: bool = False) -> None:
            super().__init__(object_id="timers", parent=parent)
            # Individual timer objects will be created dynamically based on API response
            # Example: self.timer_1, self.timer_2, etc.

        def update_timers(self, timers_data: list, captured_at) -> None:
            """Update timer data from API response"""
            # Clear existing timer attributes - properly remove from children list
            existing_timers = [attr for attr in dir(self) if attr.startswith("timer_") and not attr.startswith("_")]
            for timer_attr in existing_timers:
                timer_obj = getattr(self, timer_attr)
                if hasattr(timer_obj, "parent"):
                    timer_obj.parent = None  # This removes it from parent's children list
                delattr(self, timer_attr)

            # Create individual timer objects
            for timer in timers_data:
                if "id" in timer:
                    timer_id = timer["id"]
                    timer_attr_name = f"timer_{timer_id}"

                    # Create a GenericObject for this timer
                    timer_obj = GenericObject(object_id=timer_attr_name, parent=self)

                    # Add basic timer properties
                    timer_obj.timer_id = GenericAttribute("id", timer_obj, value=timer_id, tags={"connector_custom"})
                    timer_obj.enabled = BooleanAttribute(
                        "enabled", timer_obj, value=timer.get("enabled", False), tags={"connector_custom"}
                    )

                    # Add climatisation flag if present
                    if "climatisation" in timer:
                        timer_obj.climatisation = BooleanAttribute(
                            "climatisation", timer_obj, value=timer.get("climatisation", False), tags={"connector_custom"}
                        )

                    # Handle preferredChargingTimes - create individual time window attributes
                    if "preferredChargingTimes" in timer and timer["preferredChargingTimes"] is not None:
                        times = timer["preferredChargingTimes"]
                        for idx, pt in enumerate(times):
                            if isinstance(pt, dict):
                                pt_id = pt.get("id", idx)
                                pt_name = f"window_{pt_id}"

                                # Create a child object for this time window
                                pt_obj = GenericObject(object_id=pt_name, parent=timer_obj)

                                if "id" in pt:
                                    pt_obj.window_id = GenericAttribute(
                                        "id", pt_obj, value=pt["id"], tags={"connector_custom"}
                                    )

                                if "enabled" in pt:
                                    pt_obj.enabled = BooleanAttribute(
                                        "enabled", pt_obj, value=pt.get("enabled", False), tags={"connector_custom"}
                                    )

                                if "startTimeLocal" in pt:
                                    pt_obj.start_time_local = GenericAttribute(
                                        "start_time_local", pt_obj, value=pt["startTimeLocal"], tags={"connector_custom"}
                                    )

                                if "endTimeLocal" in pt:
                                    pt_obj.end_time_local = GenericAttribute(
                                        "end_time_local", pt_obj, value=pt["endTimeLocal"], tags={"connector_custom"}
                                    )

                                # Set as attribute on timer object
                                setattr(timer_obj, pt_name, pt_obj)

                    # Handle recurringTimer - create flattened attributes
                    if "recurringTimer" in timer and timer["recurringTimer"] is not None:
                        recurring = timer["recurringTimer"]

                        if "departureTimeLocal" in recurring:
                            timer_obj.departure_time_local = GenericAttribute(
                                "departure_time_local",
                                timer_obj,
                                value=recurring["departureTimeLocal"],
                                tags={"connector_custom"},
                            )

                        if "targetTimeLocal" in recurring:
                            timer_obj.target_time_local = GenericAttribute(
                                "target_time_local", timer_obj, value=recurring["targetTimeLocal"], tags={"connector_custom"}
                            )

                        if "repetitionDays" in recurring:
                            timer_obj.repetition_days = GenericAttribute(
                                "repetition_days", timer_obj, value=recurring["repetitionDays"], tags={"connector_custom"}
                            )

                        # Handle recurringOn - create boolean attributes for each day
                        if "recurringOn" in recurring and isinstance(recurring["recurringOn"], dict):
                            for day_key, day_val in recurring["recurringOn"].items():
                                attr_day = f"recurring_{day_key}"
                                setattr(
                                    timer_obj,
                                    attr_day,
                                    BooleanAttribute(attr_day, timer_obj, value=bool(day_val), tags={"connector_custom"}),
                                )

                    # Set the timer object as an attribute of this Timers object
                    setattr(self, timer_attr_name, timer_obj)


# Mapping of Audi charging states to generic charging states
mapping_audi_charging_state: Dict[AudiCharging.AudiChargingState, Charging.ChargingState] = {
    AudiCharging.AudiChargingState.OFF: Charging.ChargingState.OFF,
    AudiCharging.AudiChargingState.NOT_READY_FOR_CHARGING: Charging.ChargingState.OFF,
    AudiCharging.AudiChargingState.READY_FOR_CHARGING: Charging.ChargingState.READY_FOR_CHARGING,
    AudiCharging.AudiChargingState.CONSERVATION: Charging.ChargingState.CONSERVATION,
    # TODO: CHARGE_PURPOSE_REACHED means charging is complete/finished, not ready for charging
    # Framework needs extension to support COMPLETE/FINISHED state (see GitHub issue)
    AudiCharging.AudiChargingState.CHARGE_PURPOSE_REACHED_NOT_CONSERVATION_CHARGING: Charging.ChargingState.READY_FOR_CHARGING,
    AudiCharging.AudiChargingState.CHARGE_PURPOSE_REACHED_CONSERVATION: Charging.ChargingState.CONSERVATION,
    AudiCharging.AudiChargingState.CHARGING: Charging.ChargingState.CHARGING,
    AudiCharging.AudiChargingState.ERROR: Charging.ChargingState.ERROR,
    AudiCharging.AudiChargingState.UNSUPPORTED: Charging.ChargingState.UNSUPPORTED,
    AudiCharging.AudiChargingState.DISCHARGING: Charging.ChargingState.DISCHARGING,
    AudiCharging.AudiChargingState.UNKNOWN: Charging.ChargingState.UNKNOWN,
}
