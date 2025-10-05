"""
Module for climatization for audi vehicles.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from carconnectivity.attributes import BooleanAttribute
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

    def __init__(self, vehicle: GenericVehicle | None = None, origin: Optional[Climatization] = None) -> None:
        if origin is not None:
            super().__init__(origin=origin)
            if not isinstance(self.settings, AudiClimatization.Settings):
                self.settings: Climatization.Settings = AudiClimatization.Settings(parent=self, origin=origin.settings)
        else:
            super().__init__(vehicle=vehicle)
            self.settings: Climatization.Settings = AudiClimatization.Settings(parent=self)

    class Settings(Climatization.Settings):
        """
        This class represents the settings for an audi car climatization.
        """

        def __init__(self, parent: Optional[GenericObject] = None, origin: Optional[Climatization.Settings] = None) -> None:
            if origin is not None:
                super().__init__(parent=parent, origin=origin)
            else:
                super().__init__(parent=parent)
            self.unit_in_car: Optional[Temperature] = None
            self.front_zone_left_enabled: BooleanAttribute = BooleanAttribute(
                parent=self, name="front_zone_left_enabled", tags={"connector_custom"}
            )
            self.front_zone_right_enabled: BooleanAttribute = BooleanAttribute(
                parent=self, name="front_zone_right_enabled", tags={"connector_custom"}
            )
            self.rear_zone_left_enabled: BooleanAttribute = BooleanAttribute(
                parent=self, name="rear_zone_left_enabled", tags={"connector_custom"}
            )
            self.rear_zone_right_enabled: BooleanAttribute = BooleanAttribute(
                parent=self, name="rear_zone_right_enabled", tags={"connector_custom"}
            )
