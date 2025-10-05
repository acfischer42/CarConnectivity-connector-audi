"""Module for Audi vehicle classes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from carconnectivity.attributes import BooleanAttribute
from carconnectivity.vehicle import CombustionVehicle, ElectricVehicle, GenericVehicle, HybridVehicle

from carconnectivity_connectors.audi.capability import Capabilities
from carconnectivity_connectors.audi.charging import AudiCharging
from carconnectivity_connectors.audi.climatization import AudiClimatization

SUPPORT_IMAGES = False
try:
    from PIL import Image

    SUPPORT_IMAGES = True
except ImportError:
    pass

if TYPE_CHECKING:
    from typing import Dict, Optional

    from carconnectivity.garage import Garage
    from carconnectivity_connectors.base.connector import BaseConnector


class AudiVehicle(GenericVehicle):  # pylint: disable=too-many-instance-attributes
    """
    A class to represent a generic Audi vehicle.

    Attributes:
    -----------
    vin : StringAttribute
        The vehicle identification number (VIN) of the vehicle.
    license_plate : StringAttribute
        The license plate of the vehicle.
    """

    def __init__(
        self,
        vin: Optional[str] = None,
        garage: Optional[Garage] = None,
        managing_connector: Optional[BaseConnector] = None,
        origin: Optional[AudiVehicle] = None,
    ) -> None:
        if origin is not None:
            super().__init__(garage=garage, origin=origin)
            self.capabilities: Capabilities = origin.capabilities
            self.capabilities.parent = self
            self.is_active: BooleanAttribute = origin.is_active
            self.is_active.parent = self
            if SUPPORT_IMAGES:
                self._car_images = origin._car_images
        else:
            super().__init__(vin=vin, garage=garage, managing_connector=managing_connector)
            self.capabilities: Capabilities = Capabilities(vehicle=self)
            self.climatization = AudiClimatization(vehicle=self, origin=self.climatization)
            self.is_active = BooleanAttribute(name="is_active", parent=self, tags={"connector_custom"})
            if SUPPORT_IMAGES:
                self._car_images: Dict[str, Image.Image] = {}
        self.manufacturer._set_value(value="Audi")  # pylint: disable=protected-access


class AudiElectricVehicle(ElectricVehicle, AudiVehicle):
    """
    Represents an Audi electric vehicle.
    """

    def __init__(
        self,
        vin: Optional[str] = None,
        garage: Optional[Garage] = None,
        managing_connector: Optional[BaseConnector] = None,
        origin: Optional[AudiVehicle] = None,
    ) -> None:
        if origin is not None:
            super().__init__(garage=garage, origin=origin)
            if isinstance(origin, ElectricVehicle):
                self.charging = AudiCharging(vehicle=self, origin=origin.charging)
            else:
                self.charging = AudiCharging(vehicle=self, origin=self.charging)
        else:
            super().__init__(vin=vin, garage=garage, managing_connector=managing_connector)
            self.charging = AudiCharging(vehicle=self, origin=self.charging)


class AudiCombustionVehicle(CombustionVehicle, AudiVehicle):
    """
    Represents an Audi combustion vehicle.
    """

    def __init__(
        self,
        vin: Optional[str] = None,
        garage: Optional[Garage] = None,
        managing_connector: Optional[BaseConnector] = None,
        origin: Optional[AudiVehicle] = None,
    ) -> None:
        if origin is not None:
            super().__init__(garage=garage, origin=origin)
        else:
            super().__init__(vin=vin, garage=garage, managing_connector=managing_connector)


class AudiHybridVehicle(HybridVehicle, AudiElectricVehicle, AudiCombustionVehicle):
    """
    Represents an Audi hybrid vehicle.
    """

    def __init__(
        self,
        vin: Optional[str] = None,
        garage: Optional[Garage] = None,
        managing_connector: Optional[BaseConnector] = None,
        origin: Optional[AudiVehicle] = None,
    ) -> None:
        if origin is not None:
            super().__init__(garage=garage, origin=origin)
        else:
            super().__init__(vin=vin, garage=garage, managing_connector=managing_connector)
