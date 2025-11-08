"""Module for Audi vehicle classes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from carconnectivity.attributes import BooleanAttribute, StringAttribute
from carconnectivity.objects import GenericObject
from carconnectivity.vehicle import CombustionVehicle, ElectricVehicle, GenericVehicle, HybridVehicle

from carconnectivity_connectors.audi.capability import Capabilities
from carconnectivity_connectors.audi.charging import AudiCharging
from carconnectivity_connectors.audi.climatization import AudiClimatization
from carconnectivity_connectors.audi.warnings import AudiWarnings

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


class Media(GenericObject):
    """
    Container for vehicle media information (colors, etc.) from VGQL API.

    This class dynamically creates attributes based on the media response content.
    Common attributes include exteriorColor and interiorColor.
    """

    def __init__(self, specification: GenericVehicle.VehicleSpecification, origin: Optional[Media] = None) -> None:
        if origin is not None:
            super().__init__(object_id="media", parent=specification, origin=origin)
            # Copy all dynamically created attributes from origin
            for attr_name in dir(origin):
                if not attr_name.startswith("_") and attr_name not in ["parent", "object_id"]:
                    source_attr = getattr(origin, attr_name)
                    if hasattr(source_attr, "parent"):
                        setattr(self, attr_name, source_attr)
                        source_attr.parent = self
        else:
            super().__init__(object_id="media", parent=specification)
        # Enable by default so WebUI shows the tab
        self.enabled = True

    def populate_from_data(self, media_data: dict) -> None:
        """
        Dynamically populate media attributes from VGQL response.

        Creates an attribute for each key in the media_data dictionary.

        Args:
            media_data: Dictionary containing media information (e.g., exteriorColor, interiorColor)
        """
        for key, value in media_data.items():
            if value is not None:
                # Convert camelCase to snake_case for attribute name
                attr_name = "".join(["_" + c.lower() if c.isupper() else c for c in key]).lstrip("_")

                # Create or update the attribute
                if hasattr(self, attr_name):
                    attr = getattr(self, attr_name)
                    attr._set_value(value)  # pylint: disable=protected-access
                else:
                    # Use StringAttribute for better display in WebUI
                    attr = StringAttribute(attr_name, self, tags={"connector_custom", "vgql"})
                    attr._set_value(str(value))  # pylint: disable=protected-access
                    setattr(self, attr_name, attr)

        # Enable the media object so it appears in WebUI
        self.enabled = True
        # Notify observers that media has been updated
        self.notify(flags=self.ObserverEvent.UPDATED)


class TechSpecGroup(GenericObject):
    """
    Container for a group of technical specifications (e.g., engine, performance).

    This class dynamically creates attributes for each spec in the group.
    """

    def __init__(self, group_id: str, parent: GenericObject, origin: Optional[TechSpecGroup] = None) -> None:
        if origin is not None:
            super().__init__(object_id=group_id, parent=parent, origin=origin)
            # Copy all dynamically created attributes from origin
            for attr_name in dir(origin):
                if not attr_name.startswith("_") and attr_name not in ["parent", "object_id"]:
                    source_attr = getattr(origin, attr_name)
                    if hasattr(source_attr, "parent"):
                        setattr(self, attr_name, source_attr)
                        source_attr.parent = self
        else:
            super().__init__(object_id=group_id, parent=parent)
        self.enabled = True


class TechSpecs(GenericObject):
    """
    Container for vehicle technical specifications from VGQL API.

    This class dynamically creates group objects based on the groupId in the API response,
    then creates attributes for each specification within those groups.

    Example structure:
        techspecs/
            engine/
                displacement = "1395 cm³"
                max_output = "180 kW (245 PS)"
            performance_data/
                acceleration = "7,3 s"
                top_speed = "210 km/h"
    """

    def __init__(self, specification: GenericVehicle.VehicleSpecification, origin: Optional[TechSpecs] = None) -> None:
        if origin is not None:
            super().__init__(object_id="techspecs", parent=specification, origin=origin)
            # Copy all dynamically created group objects from origin
            for attr_name in dir(origin):
                if not attr_name.startswith("_") and attr_name not in ["parent", "object_id"]:
                    source_attr = getattr(origin, attr_name)
                    if hasattr(source_attr, "parent"):
                        setattr(self, attr_name, source_attr)
                        source_attr.parent = self
        else:
            super().__init__(object_id="techspecs", parent=specification)
        self.enabled = True

    def populate_from_data(self, techspecs_array: list) -> None:
        """
        Dynamically populate technical specifications from VGQL response.

        Groups specifications by their groupId and creates nested structure.

        Args:
            techspecs_array: Array of technical specification objects from VGQL API
        """
        # Group specs by groupId
        groups = {}
        for spec in techspecs_array:
            group_id = spec.get("groupId", "other")
            if group_id not in groups:
                groups[group_id] = []
            groups[group_id].append(spec)

        # Create a group object for each groupId
        for group_id, specs in groups.items():
            # Convert groupId to snake_case for attribute name
            group_name = group_id.replace("-", "_").lower()

            # Create or get the group
            if hasattr(self, group_name):
                group = getattr(self, group_name)
            else:
                group = TechSpecGroup(group_id=group_name, parent=self)
                setattr(self, group_name, group)

            # Add each spec as an attribute in the group
            for spec in specs:
                key = spec.get("key", "")
                value = spec.get("value", "")
                unit = spec.get("unit", "")

                if key and value:
                    # Convert key to snake_case
                    attr_name = key.replace("-", "_").replace(" ", "_").lower()

                    # Create display value with unit if provided
                    display_value = f"{value} {unit}" if unit and unit not in str(value) else value

                    # Create or update the attribute
                    if hasattr(group, attr_name):
                        attr = getattr(group, attr_name)
                        attr._set_value(str(display_value))  # pylint: disable=protected-access
                    else:
                        attr = StringAttribute(attr_name, group, tags={"connector_custom", "vgql"})
                        attr._set_value(str(display_value))  # pylint: disable=protected-access
                        setattr(group, attr_name, attr)

        # Enable and notify
        self.enabled = True
        self.notify(flags=self.ObserverEvent.UPDATED)


class EquipmentCategory(GenericObject):
    """Represents a category of equipment items."""

    def __init__(self, category_id: str, parent: GenericObject, origin: Optional["EquipmentCategory"] = None) -> None:
        """Initialize equipment category.

        Args:
            category_id: The category identifier
            parent: Parent object
            origin: Origin observable
        """
        if origin is not None:
            super().__init__(object_id=category_id, parent=parent, origin=origin)
            # Copy all dynamically created attributes from origin
            for attr_name in dir(origin):
                if not attr_name.startswith("_") and attr_name not in ["parent", "object_id"]:
                    source_attr = getattr(origin, attr_name)
                    if hasattr(source_attr, "parent"):
                        setattr(self, attr_name, source_attr)
                        source_attr.parent = self
        else:
            super().__init__(object_id=category_id, parent=parent)
        self.enabled = True


class Equipment(GenericObject):
    """Container for vehicle equipment organized by categories.

    Creates dynamic category groups from equipment data, where each category
    contains individual equipment items as StringAttribute objects.
    Structure: vehicle.equipments.category_name.equipment_name = "Equipment Name (code)"
    """

    def __init__(self, specification: GenericVehicle.VehicleSpecification, origin: Optional["Equipment"] = None) -> None:
        """Initialize equipment container.

        Args:
            specification: Parent specification object
            origin: Origin observable for change notification
        """
        if origin is not None:
            super().__init__(object_id="equipments", parent=specification, origin=origin)
            # Copy all dynamically created attributes from origin
            for attr_name in dir(origin):
                if not attr_name.startswith("_") and attr_name not in ["parent", "object_id"]:
                    source_attr = getattr(origin, attr_name)
                    if hasattr(source_attr, "parent"):
                        setattr(self, attr_name, source_attr)
                        source_attr.parent = self
        else:
            super().__init__(object_id="equipments", parent=specification)
        self.enabled = True

    def populate_from_data(self, equipments_array: list):
        """Populate equipment structure from VGQL equipment array.

        Groups equipment items by categoryId and creates nested structure:
        - Each categoryId becomes an EquipmentCategory object
        - Each equipment item becomes a StringAttribute with name and code
        - Attributes named by equipment code for uniqueness

        Args:
            equipments_array: List of equipment dictionaries from VGQL API
        """
        # Group equipment by categoryId
        categories = {}
        for equipment in equipments_array:
            category_id = equipment.get("categoryId", "other")
            if category_id not in categories:
                categories[category_id] = []
            categories[category_id].append(equipment)

        # Create a category object for each categoryId
        for category_id, items in categories.items():
            # Convert categoryId to snake_case for attribute name
            category_name = category_id.replace("-", "_").lower()

            # Create or get the category
            if hasattr(self, category_name):
                category = getattr(self, category_name)
            else:
                category = EquipmentCategory(category_id=category_name, parent=self)
                setattr(self, category_name, category)

            # Add each equipment item as an attribute in the category
            for item in items:
                code = item.get("code", "").strip()
                name = item.get("name", "")
                standard = item.get("standard", False)

                if code and name:
                    # Convert code to snake_case for attribute name
                    attr_name = code.replace(" ", "_").replace(".", "_").lower()

                    # Create display value: "Name (code)" with [S] or [O] for standard/optional
                    marker = "[S]" if standard else "[O]"
                    display_value = f"{marker} {name} ({code})"

                    # Create or update the attribute
                    if hasattr(category, attr_name):
                        attr = getattr(category, attr_name)
                        attr._set_value(display_value)  # pylint: disable=protected-access
                    else:
                        attr = StringAttribute(attr_name, category, tags={"connector_custom", "vgql"})
                        attr._set_value(display_value)  # pylint: disable=protected-access
                        setattr(category, attr_name, attr)

        # Enable and notify
        self.enabled = True
        self.notify(flags=self.ObserverEvent.UPDATED)


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
            self.warnings: AudiWarnings = origin.warnings if hasattr(origin, "warnings") else AudiWarnings(vehicle=self)
            self.warnings.parent = self
            # TechSpecs, Equipment, and Media are now children of specification
            if hasattr(self.specification, "techspecs") and isinstance(self.specification.techspecs, TechSpecs):
                self.specification.techspecs = (
                    origin.specification.techspecs
                    if hasattr(origin.specification, "techspecs")
                    else TechSpecs(specification=self.specification)
                )
                self.specification.techspecs.parent = self.specification
            else:
                self.specification.techspecs = TechSpecs(specification=self.specification)
            if hasattr(self.specification, "equipments") and isinstance(self.specification.equipments, Equipment):
                self.specification.equipments = (
                    origin.specification.equipments
                    if hasattr(origin.specification, "equipments")
                    else Equipment(specification=self.specification)
                )
                self.specification.equipments.parent = self.specification
            else:
                self.specification.equipments = Equipment(specification=self.specification)
            if hasattr(self.specification, "media") and isinstance(self.specification.media, Media):
                self.specification.media = (
                    origin.specification.media
                    if hasattr(origin.specification, "media")
                    else Media(specification=self.specification)
                )
                self.specification.media.parent = self.specification
            else:
                self.specification.media = Media(specification=self.specification)
            # Enable specification so it shows in WebUI
            self.specification.enabled = True
            if SUPPORT_IMAGES:
                self._car_images = origin._car_images
        else:
            super().__init__(vin=vin, garage=garage, managing_connector=managing_connector)
            self.capabilities: Capabilities = Capabilities(vehicle=self)
            self.climatization = AudiClimatization(vehicle=self, origin=self.climatization)
            self.is_active = BooleanAttribute(name="is_active", parent=self, tags={"connector_custom"})
            self.warnings: AudiWarnings = AudiWarnings(vehicle=self)
            # TechSpecs, Equipment, and Media are now children of specification
            self.specification.techspecs = TechSpecs(specification=self.specification)
            self.specification.equipments = Equipment(specification=self.specification)
            self.specification.media = Media(specification=self.specification)
            # Enable specification so it shows in WebUI
            self.specification.enabled = True
            if SUPPORT_IMAGES:
                self._car_images: Dict[str, Image.Image] = {}
        self.manufacturer._set_value(value="Audi")  # pylint: disable=protected-access


class AudiElectricVehicle(ElectricVehicle, AudiVehicle):
    """
    Represents an Audi electric vehicle.

    This class uses multiple inheritance from ElectricVehicle and AudiVehicle.
    The super().__init__() call properly initializes all parent classes through
    Python's Method Resolution Order (MRO).

    MRO for AudiElectricVehicle:
    1. AudiElectricVehicle
    2. ElectricVehicle
    3. AudiVehicle
    4. GenericVehicle
    5. GenericObject
    6. object

    The super().__init__() call ensures proper initialization of all parent classes.
    """

    def __init__(
        self,
        vin: Optional[str] = None,
        garage: Optional[Garage] = None,
        managing_connector: Optional[BaseConnector] = None,
        origin: Optional[AudiVehicle] = None,
    ) -> None:
        # Initialize parent classes through MRO - always call super().__init__()
        # CodeQL requires this call to be made in all code paths
        if origin is not None:
            # Initialize with origin-based parameters
            super().__init__(garage=garage, origin=origin)
            # Set up Audi-specific charging with origin
            if isinstance(origin, ElectricVehicle):
                self.charging = AudiCharging(vehicle=self, origin=origin.charging)
            else:
                self.charging = AudiCharging(vehicle=self, origin=self.charging)
        else:
            # Initialize with direct parameters
            super().__init__(vin=vin, garage=garage, managing_connector=managing_connector)
            # Set up Audi-specific charging without origin
            self.charging = AudiCharging(vehicle=self, origin=self.charging)


class AudiCombustionVehicle(CombustionVehicle, AudiVehicle):
    """
    Represents an Audi combustion vehicle.

    This class uses multiple inheritance from CombustionVehicle and AudiVehicle.
    The super().__init__() call properly initializes all parent classes through
    Python's Method Resolution Order (MRO).

    MRO for AudiCombustionVehicle:
    1. AudiCombustionVehicle
    2. CombustionVehicle
    3. AudiVehicle
    4. GenericVehicle
    5. GenericObject
    6. object

    The super().__init__() call ensures proper initialization of all parent classes.
    """

    def __init__(
        self,
        vin: Optional[str] = None,
        garage: Optional[Garage] = None,
        managing_connector: Optional[BaseConnector] = None,
        origin: Optional[AudiVehicle] = None,
    ) -> None:
        # Initialize parent classes through MRO - always call super().__init__()
        # CodeQL requires this call to be made in all code paths
        if origin is not None:
            # Initialize with origin-based parameters
            super().__init__(garage=garage, origin=origin)
        else:
            # Initialize with direct parameters
            super().__init__(vin=vin, garage=garage, managing_connector=managing_connector)


class AudiHybridVehicle(HybridVehicle, AudiElectricVehicle, AudiCombustionVehicle):
    """
    Represents an Audi hybrid vehicle.

    This class uses multiple inheritance from HybridVehicle, AudiElectricVehicle, and AudiCombustionVehicle.
    The super().__init__() call properly initializes all parent classes through
    Python's Method Resolution Order (MRO).

    MRO for AudiHybridVehicle:
    1. AudiHybridVehicle
    2. HybridVehicle
    3. AudiElectricVehicle
    4. ElectricVehicle
    5. AudiCombustionVehicle
    6. CombustionVehicle
    7. AudiVehicle
    8. GenericVehicle
    9. GenericObject
    10. object

    The super().__init__() call ensures proper initialization of all parent classes.
    """

    def __init__(
        self,
        vin: Optional[str] = None,
        garage: Optional[Garage] = None,
        managing_connector: Optional[BaseConnector] = None,
        origin: Optional[AudiVehicle] = None,
    ) -> None:
        # Initialize parent classes through MRO - always call super().__init__()
        # CodeQL requires this call to be made in all code paths
        if origin is not None:
            # Initialize with origin-based parameters
            super().__init__(garage=garage, origin=origin)
        else:
            # Initialize with direct parameters
            super().__init__(vin=vin, garage=garage, managing_connector=managing_connector)
