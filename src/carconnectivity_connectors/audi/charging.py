"""
Module for charging for Audi vehicles.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from carconnectivity.charging import Charging
from carconnectivity.vehicle import ElectricVehicle

if TYPE_CHECKING:
    from typing import Dict, Optional

    from carconnectivity.objects import GenericObject


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
        else:
            super().__init__(vehicle=vehicle)
            self.settings = AudiCharging.Settings(parent=self, origin=self.settings)

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
        TIMER_CHARGING_WITH_CLIMATISATION = "timerChargingWithClimatisation"
        HOME_STORAGE_CHARGING = "homeStorageCharging"
        IMMEDIATE_DISCHARGING = "immediateDischarging"
        UNKNOWN = "unknown charge mode"


# Mapping of Audi charging states to generic charging states
mapping_audi_charging_state: Dict[AudiCharging.AudiChargingState, Charging.ChargingState] = {
    AudiCharging.AudiChargingState.OFF: Charging.ChargingState.OFF,
    AudiCharging.AudiChargingState.NOT_READY_FOR_CHARGING: Charging.ChargingState.OFF,
    AudiCharging.AudiChargingState.READY_FOR_CHARGING: Charging.ChargingState.READY_FOR_CHARGING,
    AudiCharging.AudiChargingState.CONSERVATION: Charging.ChargingState.CONSERVATION,
    AudiCharging.AudiChargingState.CHARGE_PURPOSE_REACHED_NOT_CONSERVATION_CHARGING: Charging.ChargingState.READY_FOR_CHARGING,
    AudiCharging.AudiChargingState.CHARGE_PURPOSE_REACHED_CONSERVATION: Charging.ChargingState.CONSERVATION,
    AudiCharging.AudiChargingState.CHARGING: Charging.ChargingState.CHARGING,
    AudiCharging.AudiChargingState.ERROR: Charging.ChargingState.ERROR,
    AudiCharging.AudiChargingState.UNSUPPORTED: Charging.ChargingState.UNSUPPORTED,
    AudiCharging.AudiChargingState.DISCHARGING: Charging.ChargingState.DISCHARGING,
    AudiCharging.AudiChargingState.UNKNOWN: Charging.ChargingState.UNKNOWN,
}
