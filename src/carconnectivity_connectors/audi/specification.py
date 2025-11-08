"""Module for dynamic vehicle specification classes for Audi vehicles.

This module provides a flexible, dynamic structure that automatically adapts to
the VGQL API response without hardcoded attribute names or hierarchy.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

from carconnectivity.attributes import FloatAttribute, GenericAttribute, IntegerAttribute, StringAttribute
from carconnectivity.objects import GenericObject

if TYPE_CHECKING:
    from carconnectivity.objects import GenericObject as GenericObjectType


class DynamicSpecGroup(GenericObject):
    """
    A dynamic specification group that creates attributes based on data structure.

    This class can represent any grouping level (engine, performance, consumption, etc.)
    and automatically creates child attributes or nested groups based on the data.
    """

    def __init__(
        self, object_id: str, parent: Optional[GenericObjectType] = None, origin: Optional[DynamicSpecGroup] = None
    ) -> None:
        if origin is not None:
            super().__init__(object_id=object_id, parent=parent, origin=origin)
            # Copy all dynamically created attributes from origin
            for attr_name in dir(origin):
                if not attr_name.startswith("_") and attr_name not in ["parent", "object_id"]:
                    source_attr = getattr(origin, attr_name)
                    if hasattr(source_attr, "parent"):
                        # It's an attribute or child object - copy it
                        setattr(self, attr_name, source_attr)
                        source_attr.parent = self
        else:
            super().__init__(object_id=object_id, parent=parent)

    def add_attribute(self, key: str, value: Any, unit: Optional[str] = None) -> None:
        """
        Dynamically add an attribute with automatic type detection.

        Args:
            key: The attribute key/name (will be sanitized for Python)
            value: The value to set
            unit: Optional unit string to append to value
        """
        # Sanitize the key for Python attribute name
        attr_name = key.replace("-", "_").replace(" ", "_").lower()

        # Skip if attribute already exists
        if hasattr(self, attr_name):
            existing_attr = getattr(self, attr_name)
            if hasattr(existing_attr, "_set_value"):
                existing_attr._set_value(value)  # pylint: disable=protected-access
            return

        # Create display value with unit if provided
        display_value = f"{value} {unit}" if unit and unit not in str(value) else value

        # Detect type and create appropriate attribute
        if value is None:
            attr = StringAttribute(name=attr_name, parent=self, tags={"connector_custom", "vgql"})
        elif isinstance(value, bool):
            from carconnectivity.attributes import BooleanAttribute

            attr = BooleanAttribute(name=attr_name, parent=self, tags={"connector_custom", "vgql"})
            attr._set_value(value)  # pylint: disable=protected-access
        elif isinstance(value, int):
            attr = IntegerAttribute(name=attr_name, parent=self, tags={"connector_custom", "vgql"})
            attr._set_value(value)  # pylint: disable=protected-access
        elif isinstance(value, float):
            attr = FloatAttribute(name=attr_name, parent=self, tags={"connector_custom", "vgql"})
            attr._set_value(value)  # pylint: disable=protected-access
        else:
            # String or complex type
            attr = StringAttribute(name=attr_name, parent=self, tags={"connector_custom", "vgql"})
            attr._set_value(str(display_value))  # pylint: disable=protected-access

        # Store as attribute (automatically adds to children via parent setter)
        setattr(self, attr_name, attr)

    def add_child_group(self, group_id: str) -> DynamicSpecGroup:
        """
        Add a nested specification group.

        Args:
            group_id: The identifier for the child group

        Returns:
            The created child group
        """
        # Sanitize group_id for Python attribute name
        attr_name = group_id.replace("-", "_").replace(" ", "_").lower()

        # Return existing if already created
        if hasattr(self, attr_name):
            return getattr(self, attr_name)

        child_group = DynamicSpecGroup(object_id=group_id, parent=self)
        setattr(self, attr_name, child_group)
        return child_group


class Specification(GenericObject):
    """
    Dynamic specification container for Audi vehicles.

    This class automatically creates a hierarchical structure based on the
    VGQL API response, grouping technical specifications by their groupId
    and creating nested attributes as needed.

    The structure adapts to whatever the API returns without requiring
    hardcoded attribute names or hierarchy levels.

    Example structure created from API:
        specification/
            groups/
                engine/
                    displacement = 1395
                    max_output = "180 kW (245 PS)"
                    fuel_type = "Super schwefelfrei ROZ 95"
                performance_data/
                    acceleration = "7,3 s"
                    top_speed = "210 km/h"
                consumption/
                    fuel_consumption_combined = "6,5 l/100km"
                    electric_consumption = "15,8 kWh/100 km"
    """

    def __init__(self, parent: Optional[GenericObjectType] = None, origin: Optional[Specification] = None) -> None:
        if origin is not None:
            super().__init__(object_id="specification", parent=parent, origin=origin)

            # Copy all dynamically created groups and attributes from origin
            for attr_name in dir(origin):
                if not attr_name.startswith("_") and attr_name not in ["parent", "object_id"]:
                    source_attr = getattr(origin, attr_name)
                    if hasattr(source_attr, "parent"):
                        setattr(self, attr_name, source_attr)
                        source_attr.parent = self

            # Copy raw data storage
            if hasattr(origin, "_raw_data"):
                self._raw_data = origin._raw_data
        else:
            super().__init__(object_id="specification", parent=parent)
            self._raw_data: Dict[str, Any] = {}

    def populate_from_vgql(self, vgql_data: Dict[str, Any]) -> None:
        """
        Populate specification from VGQL API response.

        This method dynamically creates the specification structure based on
        the API response, creating nested groups for each groupId found in
        techSpecs, and adding attributes for each specification item.

        Args:
            vgql_data: The vehicle data from VGQL API containing techSpecs,
                      equipments, media, and consumption sections
        """
        self._raw_data = vgql_data

        # Process technical specifications - group by groupId
        if "techSpecs" in vgql_data and vgql_data["techSpecs"]:
            self._process_tech_specs(vgql_data["techSpecs"])

        # Process media (colors)
        if "media" in vgql_data and vgql_data["media"]:
            self._process_media(vgql_data["media"])

        # Process equipment as a list attribute
        if "equipments" in vgql_data and vgql_data["equipments"]:
            self._process_equipment(vgql_data["equipments"])

        # Process consumption data
        if "consumption" in vgql_data and vgql_data["consumption"]:
            self._process_consumption(vgql_data["consumption"])

        # Enable the specification object after population
        self.enabled = True
        # Notify observers that the specification has been updated
        self.notify(flags=self.ObserverEvent.UPDATED)

    def _process_tech_specs(self, tech_specs: list) -> None:
        """Process technical specifications and create grouped structure."""
        # Group specs by their groupId
        groups: Dict[str, list] = {}
        for spec in tech_specs:
            group_id = spec.get("groupId", "other")
            if group_id not in groups:
                groups[group_id] = []
            groups[group_id].append(spec)

        # Create a group object for each groupId
        for group_id, specs in groups.items():
            group = self.add_child_group(group_id)

            # Add each spec as an attribute in its group
            for spec in specs:
                key = spec.get("key", "")
                value = spec.get("value", "")
                unit = spec.get("unit")

                if key and value:
                    group.add_attribute(key, value, unit)

    def _process_media(self, media: Dict[str, Any]) -> None:
        """Process media section (colors)."""
        if "exteriorColor" in media and media["exteriorColor"]:
            self.add_attribute("exterior_color", media["exteriorColor"])

        if "interiorColor" in media and media["interiorColor"]:
            self.add_attribute("interior_color", media["interiorColor"])

    def _process_equipment(self, equipments: list) -> None:
        """Process equipment list."""
        # Store raw equipment data
        equipment_attr = GenericAttribute(name="equipment", parent=self, value=equipments, tags={"connector_custom", "vgql"})
        setattr(self, "equipment", equipment_attr)

        # Also create a summary
        equipment_count = len(equipments)
        equipment_summary = f"{equipment_count} equipment items"
        summary_attr = StringAttribute(name="equipment_count", parent=self, tags={"connector_custom", "vgql"})
        summary_attr._set_value(equipment_summary)  # pylint: disable=protected-access
        setattr(self, "equipment_count", summary_attr)

    def _process_consumption(self, consumption: Dict[str, Any]) -> None:
        """Process consumption data."""
        # Consumption has complex nested structure - create a group for it
        if "wltps" in consumption and consumption["wltps"]:
            consumption_group = self.add_child_group("consumption")

            for wltp in consumption["wltps"]:
                attribute_group = wltp.get("attributeGroup", "unknown")
                # Sanitize for use as group name
                group_name = attribute_group.lower().replace("|", "_")

                if "attributes" in wltp:
                    for attr in wltp["attributes"]:
                        attr_id = attr.get("attributeId", "")
                        value = attr.get("value", "")
                        unit = attr.get("scaleUnit", "")

                        if attr_id and value:
                            # Create compound key from group and attribute
                            key = f"{group_name}_{attr_id}".lower().replace("|", "_")
                            consumption_group.add_attribute(key, value, unit)

    def add_child_group(self, group_id: str) -> DynamicSpecGroup:
        """
        Add or get a nested specification group.

        Args:
            group_id: The identifier for the child group

        Returns:
            The child group (existing or newly created)
        """
        # Sanitize group_id for Python attribute name
        attr_name = group_id.replace("-", "_").replace(" ", "_").lower()

        # Return existing if already created
        if hasattr(self, attr_name):
            return getattr(self, attr_name)

        # Create child group with parent=self (automatically adds to children list)
        child_group = DynamicSpecGroup(object_id=attr_name, parent=self)
        child_group.enabled = True  # Enable the group so it's accessible
        setattr(self, attr_name, child_group)
        return child_group

    def add_attribute(self, key: str, value: Any, unit: Optional[str] = None) -> None:
        """
        Add a top-level attribute to specification.

        Args:
            key: The attribute key/name
            value: The value to set
            unit: Optional unit string
        """
        # Sanitize the key
        attr_name = key.replace("-", "_").replace(" ", "_").lower()

        # Skip if exists
        if hasattr(self, attr_name):
            return

        display_value = f"{value} {unit}" if unit and unit not in str(value) else value

        attr = StringAttribute(name=attr_name, parent=self, tags={"connector_custom", "vgql"})
        attr._set_value(str(display_value))  # pylint: disable=protected-access
        setattr(self, attr_name, attr)
